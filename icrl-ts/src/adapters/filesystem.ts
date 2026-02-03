/**
 * Filesystem-based storage adapter for Node.js environments.
 *
 * Stores trajectories as JSON files on disk and maintains an in-memory
 * index for embeddings with cosine similarity search.
 */

import * as fs from "fs";
import * as path from "path";
import {
  Trajectory,
  TrajectorySchema,
  CurationMetadata,
  CurationMetadataSchema,
} from "../models";
import {
  BaseStorageAdapter,
  StoredEmbedding,
  EmbeddingSearchResult,
} from "../storage";

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

export interface FileSystemAdapterOptions {
  /** Whether to normalize embeddings before storage/search (default: true) */
  normalizeEmbeddings?: boolean;
}

/**
 * Filesystem storage adapter for trajectories and embeddings.
 *
 * Directory structure:
 * ```
 * dbPath/
 * ├── trajectories/
 * │   ├── <uuid-1>.json
 * │   ├── <uuid-2>.json
 * │   └── ...
 * ├── curation.json
 * └── embeddings.json
 * ```
 *
 * @example
 * ```typescript
 * const adapter = new FileSystemAdapter("./trajectories");
 * await adapter.init();
 *
 * const db = new TrajectoryDatabase(adapter, embedder);
 * ```
 */
export class FileSystemAdapter extends BaseStorageAdapter {
  private readonly dbPath: string;
  private readonly normalizeEmbeddings: boolean;

  // In-memory caches
  private trajectories: Map<string, Trajectory> = new Map();
  private curationMetadata: Map<string, CurationMetadata> = new Map();
  private embeddings: Map<string, StoredEmbedding> = new Map();

  constructor(dbPath: string, options: FileSystemAdapterOptions = {}) {
    super();
    this.dbPath = dbPath;
    this.normalizeEmbeddings = options.normalizeEmbeddings ?? true;
  }

  /**
   * Get the base path for this adapter.
   */
  get basePath(): string {
    return this.dbPath;
  }

  // =========================================================================
  // Initialization
  // =========================================================================

  async init(): Promise<void> {
    // Ensure directory exists
    if (!fs.existsSync(this.dbPath)) {
      fs.mkdirSync(this.dbPath, { recursive: true });
    }

    // Load existing data
    await this.loadTrajectories();
    await this.loadCurationMetadata();
    await this.loadEmbeddings();
  }

  private async loadTrajectories(): Promise<void> {
    const trajDir = path.join(this.dbPath, "trajectories");

    if (fs.existsSync(trajDir)) {
      const files = fs.readdirSync(trajDir).filter((f) => f.endsWith(".json"));
      for (const file of files) {
        try {
          const data = JSON.parse(
            fs.readFileSync(path.join(trajDir, file), "utf-8")
          );
          const traj = TrajectorySchema.parse(data);
          this.trajectories.set(traj.id, traj);
        } catch (error) {
          console.warn(`Failed to load trajectory ${file}:`, error);
        }
      }
    }
  }

  private async loadCurationMetadata(): Promise<void> {
    const curationFile = path.join(this.dbPath, "curation.json");

    if (fs.existsSync(curationFile)) {
      try {
        const data = JSON.parse(fs.readFileSync(curationFile, "utf-8"));
        for (const item of data) {
          const meta = CurationMetadataSchema.parse({
            ...item,
            createdAt: new Date(item.createdAt),
            deprecatedAt: item.deprecatedAt ? new Date(item.deprecatedAt) : null,
          });
          this.curationMetadata.set(meta.trajectoryId, meta);
        }
      } catch (error) {
        console.warn("Failed to load curation metadata:", error);
      }
    }
  }

  private async loadEmbeddings(): Promise<void> {
    const embeddingsFile = path.join(this.dbPath, "embeddings.json");

    if (fs.existsSync(embeddingsFile)) {
      try {
        const data = JSON.parse(fs.readFileSync(embeddingsFile, "utf-8"));
        for (const item of data) {
          this.embeddings.set(item.id, item as StoredEmbedding);
        }
      } catch (error) {
        console.warn("Failed to load embeddings:", error);
      }
    }
  }

  // =========================================================================
  // Trajectory Operations
  // =========================================================================

  async saveTrajectory(trajectory: Trajectory): Promise<void> {
    this.trajectories.set(trajectory.id, trajectory);

    const trajDir = path.join(this.dbPath, "trajectories");
    if (!fs.existsSync(trajDir)) {
      fs.mkdirSync(trajDir, { recursive: true });
    }

    const filePath = path.join(trajDir, `${trajectory.id}.json`);
    fs.writeFileSync(filePath, JSON.stringify(trajectory, null, 2));
  }

  async getTrajectory(id: string): Promise<Trajectory | null> {
    return this.trajectories.get(id) ?? null;
  }

  async getAllTrajectories(): Promise<Trajectory[]> {
    return Array.from(this.trajectories.values());
  }

  async deleteTrajectory(id: string): Promise<boolean> {
    const existed = this.trajectories.delete(id);

    if (existed) {
      const filePath = path.join(this.dbPath, "trajectories", `${id}.json`);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    }

    return existed;
  }

  // =========================================================================
  // Curation Metadata Operations
  // =========================================================================

  async saveCurationMetadata(meta: CurationMetadata): Promise<void> {
    this.curationMetadata.set(meta.trajectoryId, meta);
    this.persistCurationMetadata();
  }

  async getCurationMetadata(trajectoryId: string): Promise<CurationMetadata | null> {
    return this.curationMetadata.get(trajectoryId) ?? null;
  }

  async getAllCurationMetadata(): Promise<CurationMetadata[]> {
    return Array.from(this.curationMetadata.values());
  }

  async deleteCurationMetadata(trajectoryId: string): Promise<boolean> {
    const existed = this.curationMetadata.delete(trajectoryId);
    if (existed) {
      this.persistCurationMetadata();
    }
    return existed;
  }

  private persistCurationMetadata(): void {
    const curationFile = path.join(this.dbPath, "curation.json");
    const data = Array.from(this.curationMetadata.values());
    fs.writeFileSync(curationFile, JSON.stringify(data, null, 2));
  }

  // =========================================================================
  // Embedding Operations
  // =========================================================================

  async saveEmbedding(embedding: StoredEmbedding): Promise<void> {
    const toStore = this.normalizeEmbeddings
      ? { ...embedding, embedding: normalize(embedding.embedding) }
      : embedding;

    this.embeddings.set(embedding.id, toStore);
    this.persistEmbeddings();
  }

  async saveEmbeddings(embeddings: StoredEmbedding[]): Promise<void> {
    for (const embedding of embeddings) {
      const toStore = this.normalizeEmbeddings
        ? { ...embedding, embedding: normalize(embedding.embedding) }
        : embedding;
      this.embeddings.set(embedding.id, toStore);
    }
    this.persistEmbeddings();
  }

  async getEmbedding(id: string): Promise<StoredEmbedding | null> {
    return this.embeddings.get(id) ?? null;
  }

  async getEmbeddingsByType(type: "trajectory" | "step"): Promise<StoredEmbedding[]> {
    return Array.from(this.embeddings.values()).filter((e) => e.type === type);
  }

  async deleteEmbeddingsForTrajectory(trajectoryId: string): Promise<void> {
    const toDelete: string[] = [];

    for (const [id, embedding] of this.embeddings) {
      if (embedding.trajectoryId === trajectoryId) {
        toDelete.push(id);
      }
    }

    for (const id of toDelete) {
      this.embeddings.delete(id);
    }

    if (toDelete.length > 0) {
      this.persistEmbeddings();
    }
  }

  async searchByEmbedding(
    query: number[],
    type: "trajectory" | "step",
    k: number
  ): Promise<EmbeddingSearchResult[]> {
    const queryNormalized = this.normalizeEmbeddings ? normalize(query) : query;

    const scores: EmbeddingSearchResult[] = [];

    for (const embedding of this.embeddings.values()) {
      if (embedding.type !== type) continue;

      const score = cosineSimilarity(queryNormalized, embedding.embedding);
      scores.push({
        id: embedding.id,
        trajectoryId: embedding.trajectoryId,
        stepIndex: embedding.stepIndex,
        score,
      });
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    return scores.slice(0, k);
  }

  private persistEmbeddings(): void {
    const embeddingsFile = path.join(this.dbPath, "embeddings.json");
    const data = Array.from(this.embeddings.values());
    fs.writeFileSync(embeddingsFile, JSON.stringify(data, null, 2));
  }
}
