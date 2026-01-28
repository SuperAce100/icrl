/**
 * Trajectory database with pluggable storage and vector similarity search.
 *
 * This class manages trajectories, embeddings, and curation metadata.
 * Storage is delegated to a StorageAdapter, allowing different backends
 * (filesystem, Convex, PostgreSQL, etc.).
 */

import { v4 as uuidv4 } from "uuid";
import {
  Trajectory,
  StepExample,
  CurationMetadata,
  updateCurationUtility,
} from "./models";
import type { Embedder } from "./protocols";
import type { StorageAdapter, StoredEmbedding } from "./storage";

export interface TrajectoryDatabaseOptions {
  /** Maximum characters to use for embedding text (default: 2000) */
  maxEmbedChars?: number;
}

/**
 * Database for storing and retrieving trajectories with semantic search.
 *
 * Uses a StorageAdapter for persistence and an Embedder for generating
 * vector representations for similarity search.
 *
 * @example
 * ```typescript
 * // With filesystem adapter (Node.js)
 * const adapter = new FileSystemAdapter("./trajectories");
 * const embedder = new OpenAIEmbedder(openai);
 * const db = new TrajectoryDatabase(adapter, embedder);
 * await db.load();
 *
 * // With Convex adapter (web)
 * const adapter = new ConvexAdapter(convexClient);
 * const db = new TrajectoryDatabase(adapter, embedder);
 * await db.load();
 * ```
 */
export class TrajectoryDatabase {
  private readonly storage: StorageAdapter;
  private readonly embedder: Embedder;
  private readonly maxEmbedChars: number;

  // In-memory caches for fast access
  private trajectories: Map<string, Trajectory> = new Map();
  private curationMetadata: Map<string, CurationMetadata> = new Map();
  private stepExamples: StepExample[] = [];

  constructor(
    storage: StorageAdapter,
    embedder: Embedder,
    options: TrajectoryDatabaseOptions = {}
  ) {
    this.storage = storage;
    this.embedder = embedder;
    this.maxEmbedChars = options.maxEmbedChars ?? 2000;
  }

  /**
   * Get the storage adapter.
   */
  getStorage(): StorageAdapter {
    return this.storage;
  }

  /**
   * Get the embedder.
   */
  getEmbedder(): Embedder {
    return this.embedder;
  }

  /**
   * Load trajectories and index from storage.
   */
  async load(): Promise<void> {
    // Initialize storage
    await this.storage.init();

    // Load trajectories
    const trajectories = await this.storage.getAllTrajectories();
    this.trajectories.clear();
    for (const traj of trajectories) {
      this.trajectories.set(traj.id, traj);
    }

    // Load curation metadata
    const metadata = await this.storage.getAllCurationMetadata();
    this.curationMetadata.clear();
    for (const meta of metadata) {
      this.curationMetadata.set(meta.trajectoryId, meta);
    }

    // Build step examples cache
    this.stepExamples = await this.storage.getAllStepExamples();
  }

  private truncateForEmbedding(text: string): string {
    if (text.length <= this.maxEmbedChars) return text;
    return text.slice(0, this.maxEmbedChars);
  }

  /**
   * Add a trajectory to the database.
   *
   * Generates embeddings for the trajectory and its steps, then stores
   * everything in the storage adapter.
   */
  async add(trajectory: Trajectory): Promise<void> {
    // Ensure trajectory has an ID
    if (!trajectory.id) {
      trajectory.id = uuidv4();
    }

    // Store trajectory
    this.trajectories.set(trajectory.id, trajectory);
    await this.storage.saveTrajectory(trajectory);

    // Create curation metadata
    const meta: CurationMetadata = {
      trajectoryId: trajectory.id,
      createdAt: new Date(),
      timesRetrieved: 0,
      timesLedToSuccess: 0,
      validations: [],
      retrievalScore: null,
      persistenceScore: null,
      utilityScore: 1.0,
      isDeprecated: false,
      deprecatedAt: null,
      deprecationReason: null,
      supersededBy: null,
    };
    this.curationMetadata.set(trajectory.id, meta);
    await this.storage.saveCurationMetadata(meta);

    // Generate and store trajectory embedding
    const trajText = this.truncateForEmbedding(`${trajectory.goal}\n${trajectory.plan}`);
    const [trajEmbed] = await this.embedder.embed([trajText]);

    const trajEmbedding: StoredEmbedding = {
      id: `traj-${trajectory.id}`,
      embedding: trajEmbed!,
      type: "trajectory",
      trajectoryId: trajectory.id,
    };
    await this.storage.saveEmbedding(trajEmbedding);

    // Generate and store step embeddings
    const stepEmbeddings: StoredEmbedding[] = [];
    const stepTexts = trajectory.steps.map((step) =>
      this.truncateForEmbedding(`${step.observation}\n${step.reasoning}`)
    );

    if (stepTexts.length > 0) {
      const stepEmbeds = await this.embedder.embed(stepTexts);

      trajectory.steps.forEach((step, stepIdx) => {
        // Add to step examples cache
        this.stepExamples.push({
          goal: trajectory.goal,
          plan: trajectory.plan,
          observation: step.observation,
          reasoning: step.reasoning,
          action: step.action,
          trajectoryId: trajectory.id,
          stepIndex: stepIdx,
        });

        // Create embedding record
        stepEmbeddings.push({
          id: `step-${trajectory.id}-${stepIdx}`,
          embedding: stepEmbeds[stepIdx]!,
          type: "step",
          trajectoryId: trajectory.id,
          stepIndex: stepIdx,
        });
      });

      await this.storage.saveEmbeddings(stepEmbeddings);
    }
  }

  /**
   * Search for similar trajectories by goal.
   */
  async search(query: string, k: number = 3): Promise<Trajectory[]> {
    if (this.trajectories.size === 0) return [];

    const queryEmbed = await this.embedder.embedSingle(
      this.truncateForEmbedding(query)
    );

    const results = await this.storage.searchByEmbedding(
      queryEmbed,
      "trajectory",
      k
    );

    return results
      .map((r) => this.trajectories.get(r.trajectoryId))
      .filter((t): t is Trajectory => t !== undefined);
  }

  /**
   * Search for similar step examples.
   */
  async searchSteps(query: string, k: number = 3): Promise<StepExample[]> {
    if (this.stepExamples.length === 0) return [];

    const queryEmbed = await this.embedder.embedSingle(
      this.truncateForEmbedding(query)
    );

    const results = await this.storage.searchByEmbedding(queryEmbed, "step", k);

    // Map results back to step examples
    return results
      .map((r) =>
        this.stepExamples.find(
          (ex) =>
            ex.trajectoryId === r.trajectoryId && ex.stepIndex === r.stepIndex
        )
      )
      .filter((ex): ex is StepExample => ex !== undefined);
  }

  /**
   * Get a trajectory by ID.
   */
  get(id: string): Trajectory | undefined {
    return this.trajectories.get(id);
  }

  /**
   * Get all trajectories.
   */
  getAll(): Trajectory[] {
    return Array.from(this.trajectories.values());
  }

  /**
   * Remove a trajectory by ID.
   */
  async remove(id: string): Promise<boolean> {
    const existed = this.trajectories.delete(id);

    if (existed) {
      // Remove from storage
      await this.storage.deleteTrajectory(id);
      await this.storage.deleteCurationMetadata(id);
      await this.storage.deleteEmbeddingsForTrajectory(id);

      // Remove from caches
      this.curationMetadata.delete(id);
      this.stepExamples = this.stepExamples.filter(
        (ex) => ex.trajectoryId !== id
      );
    }

    return existed;
  }

  /**
   * Record that a trajectory was retrieved and whether it led to success.
   */
  async recordRetrieval(trajectoryId: string, ledToSuccess: boolean): Promise<void> {
    const meta = this.curationMetadata.get(trajectoryId);
    if (meta) {
      meta.timesRetrieved++;
      if (ledToSuccess) {
        meta.timesLedToSuccess++;
      }
      updateCurationUtility(meta);
      await this.storage.saveCurationMetadata(meta);
    }
  }

  /**
   * Get curation metadata for a trajectory.
   */
  getCurationMetadata(trajectoryId: string): CurationMetadata | undefined {
    return this.curationMetadata.get(trajectoryId);
  }

  /**
   * Get the number of trajectories in the database.
   */
  get size(): number {
    return this.trajectories.size;
  }
}
