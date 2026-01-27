/**
 * Trajectory database with filesystem storage and vector similarity search.
 *
 * This is a simplified TypeScript implementation that uses a basic
 * cosine similarity search. For production use with large datasets,
 * consider using a vector database like Pinecone, Weaviate, or hnswlib-node.
 */

import * as fs from "fs";
import * as path from "path";
import {
  Trajectory,
  TrajectorySchema,
  StepExample,
  CurationMetadata,
  CurationMetadataSchema,
  updateCurationUtility,
} from "./models";
import type { Embedder } from "./protocols";

/**
 * Normalize a vector to unit length for cosine similarity.
 */
function normalize(vec: number[]): number[] {
  const norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0));
  if (norm === 0) return vec;
  return vec.map((v) => v / norm);
}

/**
 * Compute cosine similarity between two normalized vectors.
 */
function cosineSimilarity(a: number[], b: number[]): number {
  return a.reduce((sum, ai, i) => sum + ai * (b[i] ?? 0), 0);
}

/**
 * Database for storing and retrieving trajectories.
 *
 * Trajectories are stored as JSON files on the filesystem.
 * Uses cosine similarity for vector search (swap in a proper vector DB for scale).
 */
export class TrajectoryDatabase {
  private readonly dbPath: string;
  private readonly embedder: Embedder;
  private trajectories: Map<string, Trajectory> = new Map();
  private curationMetadata: Map<string, CurationMetadata> = new Map();

  // Vector index (simple in-memory for now)
  private trajectoryEmbeddings: Map<string, number[]> = new Map();
  private stepExamples: StepExample[] = [];
  private stepEmbeddings: number[][] = [];

  private readonly maxEmbedChars: number;

  constructor(dbPath: string, embedder: Embedder, options: { maxEmbedChars?: number } = {}) {
    this.dbPath = dbPath;
    this.embedder = embedder;
    this.maxEmbedChars = options.maxEmbedChars ?? 2000;

    // Ensure directory exists
    if (!fs.existsSync(dbPath)) {
      fs.mkdirSync(dbPath, { recursive: true });
    }
  }

  /**
   * Load trajectories and index from disk.
   */
  async load(): Promise<void> {
    const trajDir = path.join(this.dbPath, "trajectories");

    // Load trajectories
    if (fs.existsSync(trajDir)) {
      const files = fs.readdirSync(trajDir).filter((f) => f.endsWith(".json"));
      for (const file of files) {
        const data = JSON.parse(fs.readFileSync(path.join(trajDir, file), "utf-8"));
        const traj = TrajectorySchema.parse(data);
        this.trajectories.set(traj.id, traj);
      }
    }

    // Load curation metadata
    const curationFile = path.join(this.dbPath, "curation.json");
    if (fs.existsSync(curationFile)) {
      const data = JSON.parse(fs.readFileSync(curationFile, "utf-8"));
      for (const item of data) {
        const meta = CurationMetadataSchema.parse({
          ...item,
          createdAt: new Date(item.createdAt),
          deprecatedAt: item.deprecatedAt ? new Date(item.deprecatedAt) : null,
        });
        this.curationMetadata.set(meta.trajectoryId, meta);
      }
    }

    // Rebuild embeddings index
    await this.rebuildIndex();
  }

  /**
   * Rebuild the vector index from loaded trajectories.
   */
  private async rebuildIndex(): Promise<void> {
    this.trajectoryEmbeddings.clear();
    this.stepExamples = [];
    this.stepEmbeddings = [];

    if (this.trajectories.size === 0) return;

    // Build trajectory-level embeddings
    const trajTexts: string[] = [];
    const trajIds: string[] = [];

    for (const [id, traj] of this.trajectories) {
      trajTexts.push(this.truncateForEmbedding(`${traj.goal}\n${traj.plan}`));
      trajIds.push(id);
    }

    const trajEmbeddings = await this.embedder.embed(trajTexts);
    trajIds.forEach((id, i) => {
      this.trajectoryEmbeddings.set(id, normalize(trajEmbeddings[i]!));
    });

    // Build step-level index
    const stepTexts: string[] = [];

    for (const [trajId, traj] of this.trajectories) {
      traj.steps.forEach((step, stepIdx) => {
        this.stepExamples.push({
          goal: traj.goal,
          plan: traj.plan,
          observation: step.observation,
          reasoning: step.reasoning,
          action: step.action,
          trajectoryId: trajId,
          stepIndex: stepIdx,
        });
        stepTexts.push(this.truncateForEmbedding(`${step.observation}\n${step.reasoning}`));
      });
    }

    if (stepTexts.length > 0) {
      const embeddings = await this.embedder.embed(stepTexts);
      this.stepEmbeddings = embeddings.map(normalize);
    }
  }

  private truncateForEmbedding(text: string): string {
    if (text.length <= this.maxEmbedChars) return text;
    return text.slice(0, this.maxEmbedChars);
  }

  /**
   * Add a trajectory to the database.
   */
  async add(trajectory: Trajectory): Promise<void> {
    this.trajectories.set(trajectory.id, trajectory);

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

    // Update embeddings
    const trajText = this.truncateForEmbedding(`${trajectory.goal}\n${trajectory.plan}`);
    const [trajEmbed] = await this.embedder.embed([trajText]);
    this.trajectoryEmbeddings.set(trajectory.id, normalize(trajEmbed!));

    // Add step embeddings
    const stepTexts = trajectory.steps.map((step) =>
      this.truncateForEmbedding(`${step.observation}\n${step.reasoning}`)
    );

    if (stepTexts.length > 0) {
      const stepEmbeds = await this.embedder.embed(stepTexts);
      trajectory.steps.forEach((step, stepIdx) => {
        this.stepExamples.push({
          goal: trajectory.goal,
          plan: trajectory.plan,
          observation: step.observation,
          reasoning: step.reasoning,
          action: step.action,
          trajectoryId: trajectory.id,
          stepIndex: stepIdx,
        });
        this.stepEmbeddings.push(normalize(stepEmbeds[stepIdx]!));
      });
    }

    // Save to disk
    this.saveTrajectory(trajectory);
    this.saveCuration();
  }

  private saveTrajectory(trajectory: Trajectory): void {
    const trajDir = path.join(this.dbPath, "trajectories");
    if (!fs.existsSync(trajDir)) {
      fs.mkdirSync(trajDir, { recursive: true });
    }
    const filePath = path.join(trajDir, `${trajectory.id}.json`);
    fs.writeFileSync(filePath, JSON.stringify(trajectory, null, 2));
  }

  private saveCuration(): void {
    const curationFile = path.join(this.dbPath, "curation.json");
    const data = Array.from(this.curationMetadata.values());
    fs.writeFileSync(curationFile, JSON.stringify(data, null, 2));
  }

  /**
   * Search for similar trajectories by goal.
   */
  async search(query: string, k: number = 3): Promise<Trajectory[]> {
    if (this.trajectories.size === 0) return [];

    const queryEmbed = normalize(await this.embedder.embedSingle(this.truncateForEmbedding(query)));

    // Compute similarities
    const scores: Array<{ id: string; score: number }> = [];
    for (const [id, embed] of this.trajectoryEmbeddings) {
      scores.push({ id, score: cosineSimilarity(queryEmbed, embed) });
    }

    // Sort by score descending and take top k
    scores.sort((a, b) => b.score - a.score);
    const topK = scores.slice(0, k);

    return topK.map((s) => this.trajectories.get(s.id)!).filter(Boolean);
  }

  /**
   * Search for similar step examples.
   */
  async searchSteps(query: string, k: number = 3): Promise<StepExample[]> {
    if (this.stepExamples.length === 0) return [];

    const queryEmbed = normalize(await this.embedder.embedSingle(this.truncateForEmbedding(query)));

    // Compute similarities
    const scores = this.stepEmbeddings.map((embed, i) => ({
      index: i,
      score: cosineSimilarity(queryEmbed, embed),
    }));

    // Sort by score descending and take top k
    scores.sort((a, b) => b.score - a.score);
    const topK = scores.slice(0, k);

    return topK.map((s) => this.stepExamples[s.index]!).filter(Boolean);
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
  remove(id: string): boolean {
    const existed = this.trajectories.delete(id);
    if (existed) {
      this.trajectoryEmbeddings.delete(id);
      this.curationMetadata.delete(id);

      // Remove step examples for this trajectory
      const indicesToRemove = new Set<number>();
      this.stepExamples.forEach((ex, i) => {
        if (ex.trajectoryId === id) indicesToRemove.add(i);
      });

      this.stepExamples = this.stepExamples.filter((_, i) => !indicesToRemove.has(i));
      this.stepEmbeddings = this.stepEmbeddings.filter((_, i) => !indicesToRemove.has(i));

      // Remove file
      const filePath = path.join(this.dbPath, "trajectories", `${id}.json`);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }

      this.saveCuration();
    }
    return existed;
  }

  /**
   * Record that a trajectory was retrieved and whether it led to success.
   */
  recordRetrieval(trajectoryId: string, ledToSuccess: boolean): void {
    const meta = this.curationMetadata.get(trajectoryId);
    if (meta) {
      meta.timesRetrieved++;
      if (ledToSuccess) {
        meta.timesLedToSuccess++;
      }
      updateCurationUtility(meta);
      this.saveCuration();
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
