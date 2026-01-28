/**
 * Storage adapter interface for pluggable backends.
 *
 * This allows the TrajectoryDatabase to work with different storage systems
 * such as filesystem, Convex, PostgreSQL, etc.
 */

import type { Trajectory, StepExample, CurationMetadata } from "./models";

/**
 * Stored embedding with metadata.
 */
export interface StoredEmbedding {
  /** Unique identifier */
  id: string;
  /** The embedding vector */
  embedding: number[];
  /** Type of embedding (trajectory-level or step-level) */
  type: "trajectory" | "step";
  /** Reference to the source trajectory */
  trajectoryId: string;
  /** For step embeddings, the step index */
  stepIndex?: number;
}

/**
 * Result of a vector similarity search.
 */
export interface EmbeddingSearchResult {
  /** ID of the matching embedding */
  id: string;
  /** Trajectory ID */
  trajectoryId: string;
  /** Step index (for step embeddings) */
  stepIndex?: number;
  /** Similarity score */
  score: number;
}

/**
 * Interface for storage backends.
 *
 * Implementations handle persistence of trajectories, curation metadata,
 * and embeddings. The TrajectoryDatabase delegates all storage operations
 * to this adapter.
 *
 * @example
 * ```typescript
 * // Filesystem adapter (default, for Node.js)
 * const adapter = new FileSystemAdapter("./trajectories");
 *
 * // Convex adapter (for web apps)
 * const adapter = new ConvexAdapter(convexClient);
 *
 * // Use with TrajectoryDatabase
 * const db = new TrajectoryDatabase(adapter, embedder);
 * ```
 */
export interface StorageAdapter {
  /**
   * Initialize the storage (create directories, tables, etc.).
   */
  init(): Promise<void>;

  // =========================================================================
  // Trajectory Operations
  // =========================================================================

  /**
   * Save a trajectory to storage.
   */
  saveTrajectory(trajectory: Trajectory): Promise<void>;

  /**
   * Get a trajectory by ID.
   */
  getTrajectory(id: string): Promise<Trajectory | null>;

  /**
   * Get all trajectories.
   */
  getAllTrajectories(): Promise<Trajectory[]>;

  /**
   * Delete a trajectory by ID.
   * @returns true if the trajectory existed and was deleted.
   */
  deleteTrajectory(id: string): Promise<boolean>;

  // =========================================================================
  // Curation Metadata Operations
  // =========================================================================

  /**
   * Save or update curation metadata for a trajectory.
   */
  saveCurationMetadata(meta: CurationMetadata): Promise<void>;

  /**
   * Get curation metadata for a trajectory.
   */
  getCurationMetadata(trajectoryId: string): Promise<CurationMetadata | null>;

  /**
   * Get all curation metadata.
   */
  getAllCurationMetadata(): Promise<CurationMetadata[]>;

  /**
   * Delete curation metadata for a trajectory.
   */
  deleteCurationMetadata(trajectoryId: string): Promise<boolean>;

  // =========================================================================
  // Embedding Operations
  // =========================================================================

  /**
   * Save an embedding vector.
   */
  saveEmbedding(embedding: StoredEmbedding): Promise<void>;

  /**
   * Save multiple embeddings at once (batch operation).
   */
  saveEmbeddings(embeddings: StoredEmbedding[]): Promise<void>;

  /**
   * Get an embedding by ID.
   */
  getEmbedding(id: string): Promise<StoredEmbedding | null>;

  /**
   * Get all embeddings of a specific type.
   */
  getEmbeddingsByType(type: "trajectory" | "step"): Promise<StoredEmbedding[]>;

  /**
   * Delete embeddings for a trajectory.
   */
  deleteEmbeddingsForTrajectory(trajectoryId: string): Promise<void>;

  /**
   * Search for similar embeddings using vector similarity.
   *
   * @param query - The query embedding vector.
   * @param type - Type of embeddings to search.
   * @param k - Number of results to return.
   * @returns Sorted results with highest similarity first.
   */
  searchByEmbedding(
    query: number[],
    type: "trajectory" | "step",
    k: number
  ): Promise<EmbeddingSearchResult[]>;

  // =========================================================================
  // Step Examples (derived from trajectories)
  // =========================================================================

  /**
   * Get step examples for a trajectory.
   * These are derived from the trajectory's steps and used for retrieval.
   */
  getStepExamplesForTrajectory(trajectoryId: string): Promise<StepExample[]>;

  /**
   * Get all step examples.
   */
  getAllStepExamples(): Promise<StepExample[]>;
}

/**
 * Base class with common utility methods for storage adapters.
 */
export abstract class BaseStorageAdapter implements StorageAdapter {
  abstract init(): Promise<void>;
  abstract saveTrajectory(trajectory: Trajectory): Promise<void>;
  abstract getTrajectory(id: string): Promise<Trajectory | null>;
  abstract getAllTrajectories(): Promise<Trajectory[]>;
  abstract deleteTrajectory(id: string): Promise<boolean>;
  abstract saveCurationMetadata(meta: CurationMetadata): Promise<void>;
  abstract getCurationMetadata(trajectoryId: string): Promise<CurationMetadata | null>;
  abstract getAllCurationMetadata(): Promise<CurationMetadata[]>;
  abstract deleteCurationMetadata(trajectoryId: string): Promise<boolean>;
  abstract saveEmbedding(embedding: StoredEmbedding): Promise<void>;
  abstract saveEmbeddings(embeddings: StoredEmbedding[]): Promise<void>;
  abstract getEmbedding(id: string): Promise<StoredEmbedding | null>;
  abstract getEmbeddingsByType(type: "trajectory" | "step"): Promise<StoredEmbedding[]>;
  abstract deleteEmbeddingsForTrajectory(trajectoryId: string): Promise<void>;
  abstract searchByEmbedding(
    query: number[],
    type: "trajectory" | "step",
    k: number
  ): Promise<EmbeddingSearchResult[]>;

  /**
   * Default implementation: derive step examples from trajectories.
   */
  async getStepExamplesForTrajectory(trajectoryId: string): Promise<StepExample[]> {
    const trajectory = await this.getTrajectory(trajectoryId);
    if (!trajectory) return [];

    return trajectory.steps.map((step, stepIndex) => ({
      goal: trajectory.goal,
      plan: trajectory.plan,
      observation: step.observation,
      reasoning: step.reasoning,
      action: step.action,
      trajectoryId: trajectory.id,
      stepIndex,
    }));
  }

  /**
   * Default implementation: get all step examples from all trajectories.
   */
  async getAllStepExamples(): Promise<StepExample[]> {
    const trajectories = await this.getAllTrajectories();
    const examples: StepExample[] = [];

    for (const trajectory of trajectories) {
      trajectory.steps.forEach((step, stepIndex) => {
        examples.push({
          goal: trajectory.goal,
          plan: trajectory.plan,
          observation: step.observation,
          reasoning: step.reasoning,
          action: step.action,
          trajectoryId: trajectory.id,
          stepIndex,
        });
      });
    }

    return examples;
  }
}
