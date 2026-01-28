/**
 * Convex storage adapter for the ICRL library.
 *
 * This adapter implements the StorageAdapter interface from icrl-ts,
 * delegating all storage operations to Convex queries and mutations.
 */

import type { ConvexClient } from "convex/browser";
import type { FunctionReference, OptionalRestArgs } from "convex/server";
import type { Id } from "../../convex/_generated/dataModel";
import type {
  StorageAdapter,
  StoredEmbedding,
  EmbeddingSearchResult,
} from "../../../src/storage";
import type { Trajectory, StepExample, CurationMetadata } from "../../../src/models";

// Import Convex API types
import { api } from "../../convex/_generated/api";

/**
 * Options for the ConvexAdapter.
 */
export interface ConvexAdapterOptions {
  /** The database ID to scope all operations to */
  databaseId: Id<"databases">;
}

/**
 * Convex storage adapter for ICRL.
 *
 * All operations are scoped to a specific database ID, allowing
 * multiple independent ICRL instances to share the same Convex project.
 *
 * @example
 * ```typescript
 * import { ConvexClient } from "convex/browser";
 * import { ConvexAdapter } from "./convex-adapter";
 *
 * const client = new ConvexClient(process.env.NEXT_PUBLIC_CONVEX_URL!);
 * const adapter = new ConvexAdapter(client, { databaseId });
 *
 * const db = new TrajectoryDatabase(adapter, embedder);
 * await db.load();
 * ```
 */
export class ConvexAdapter implements StorageAdapter {
  private readonly client: ConvexClient;
  private readonly databaseId: Id<"databases">;

  // In-memory caches (populated on init)
  private trajectories: Map<string, Trajectory> = new Map();
  private curationMetadata: Map<string, CurationMetadata> = new Map();

  constructor(client: ConvexClient, options: ConvexAdapterOptions) {
    this.client = client;
    this.databaseId = options.databaseId;
  }

  // Helper to run queries
  private async query<T>(
    func: FunctionReference<"query">,
    args: Record<string, unknown>
  ): Promise<T> {
    return this.client.query(func as any, args as any) as Promise<T>;
  }

  // Helper to run mutations
  private async mutate<T>(
    func: FunctionReference<"mutation">,
    args: Record<string, unknown>
  ): Promise<T> {
    return this.client.mutation(func as any, args as any) as Promise<T>;
  }

  // =========================================================================
  // Initialization
  // =========================================================================

  async init(): Promise<void> {
    // Load all trajectories into cache
    const trajectories = await this.query<any[]>(api.trajectories.listByDatabase, {
      databaseId: this.databaseId,
    });

    this.trajectories.clear();
    for (const t of trajectories) {
      const traj: Trajectory = {
        id: t.trajectoryId,
        goal: t.goal,
        plan: t.plan,
        steps: t.steps,
        success: t.success,
        metadata: t.metadata ?? {},
      };
      this.trajectories.set(traj.id, traj);
    }

    // Load all curation metadata into cache
    const metadata = await this.query<any[]>(api.trajectories.getAllCurationMetadata, {
      databaseId: this.databaseId,
    });

    this.curationMetadata.clear();
    for (const m of metadata) {
      const meta: CurationMetadata = {
        trajectoryId: m.trajectoryId,
        createdAt: new Date(m.createdAt),
        timesRetrieved: m.timesRetrieved,
        timesLedToSuccess: m.timesLedToSuccess,
        validations: [],
        retrievalScore: m.retrievalScore ?? null,
        persistenceScore: m.persistenceScore ?? null,
        utilityScore: m.utilityScore,
        isDeprecated: m.isDeprecated,
        deprecatedAt: m.deprecatedAt ? new Date(m.deprecatedAt) : null,
        deprecationReason: m.deprecationReason ?? null,
        supersededBy: m.supersededBy ?? null,
      };
      this.curationMetadata.set(meta.trajectoryId, meta);
    }
  }

  // =========================================================================
  // Trajectory Operations
  // =========================================================================

  async saveTrajectory(trajectory: Trajectory): Promise<void> {
    await this.mutate(api.trajectories.create, {
      databaseId: this.databaseId,
      trajectoryId: trajectory.id,
      goal: trajectory.goal,
      plan: trajectory.plan,
      steps: trajectory.steps,
      success: trajectory.success,
      metadata: trajectory.metadata,
    });

    this.trajectories.set(trajectory.id, trajectory);
  }

  async getTrajectory(id: string): Promise<Trajectory | null> {
    return this.trajectories.get(id) ?? null;
  }

  async getAllTrajectories(): Promise<Trajectory[]> {
    return Array.from(this.trajectories.values());
  }

  async deleteTrajectory(id: string): Promise<boolean> {
    const existed = this.trajectories.has(id);

    if (existed) {
      await this.mutate(api.trajectories.deleteByTrajectoryId, {
        databaseId: this.databaseId,
        trajectoryId: id,
      });
      this.trajectories.delete(id);
    }

    return existed;
  }

  // =========================================================================
  // Curation Metadata Operations
  // =========================================================================

  async saveCurationMetadata(meta: CurationMetadata): Promise<void> {
    await this.mutate(api.trajectories.saveCurationMetadata, {
      databaseId: this.databaseId,
      trajectoryId: meta.trajectoryId,
      createdAt: meta.createdAt.getTime(),
      timesRetrieved: meta.timesRetrieved,
      timesLedToSuccess: meta.timesLedToSuccess,
      retrievalScore: meta.retrievalScore ?? undefined,
      persistenceScore: meta.persistenceScore ?? undefined,
      utilityScore: meta.utilityScore,
      isDeprecated: meta.isDeprecated,
      deprecatedAt: meta.deprecatedAt?.getTime(),
      deprecationReason: meta.deprecationReason ?? undefined,
      supersededBy: meta.supersededBy ?? undefined,
    });

    this.curationMetadata.set(meta.trajectoryId, meta);
  }

  async getCurationMetadata(trajectoryId: string): Promise<CurationMetadata | null> {
    return this.curationMetadata.get(trajectoryId) ?? null;
  }

  async getAllCurationMetadata(): Promise<CurationMetadata[]> {
    return Array.from(this.curationMetadata.values());
  }

  async deleteCurationMetadata(trajectoryId: string): Promise<boolean> {
    const existed = this.curationMetadata.has(trajectoryId);

    if (existed) {
      await this.mutate(api.trajectories.deleteCurationMetadata, {
        databaseId: this.databaseId,
        trajectoryId,
      });
      this.curationMetadata.delete(trajectoryId);
    }

    return existed;
  }

  // =========================================================================
  // Embedding Operations
  // =========================================================================

  async saveEmbedding(embedding: StoredEmbedding): Promise<void> {
    await this.mutate(api.embeddings.save, {
      databaseId: this.databaseId,
      embeddingId: embedding.id,
      trajectoryId: embedding.trajectoryId,
      type: embedding.type,
      stepIndex: embedding.stepIndex,
      embedding: embedding.embedding,
    });
  }

  async saveEmbeddings(embeddings: StoredEmbedding[]): Promise<void> {
    await this.mutate(api.embeddings.saveBatch, {
      databaseId: this.databaseId,
      embeddings: embeddings.map((e) => ({
        embeddingId: e.id,
        trajectoryId: e.trajectoryId,
        type: e.type,
        stepIndex: e.stepIndex,
        embedding: e.embedding,
      })),
    });
  }

  async getEmbedding(id: string): Promise<StoredEmbedding | null> {
    const result = await this.query<any | null>(api.embeddings.getById, {
      databaseId: this.databaseId,
      embeddingId: id,
    });

    if (!result) return null;

    return {
      id: result.embeddingId,
      embedding: result.embedding,
      type: result.type,
      trajectoryId: result.trajectoryId,
      stepIndex: result.stepIndex,
    };
  }

  async getEmbeddingsByType(type: "trajectory" | "step"): Promise<StoredEmbedding[]> {
    const results = await this.query<any[]>(api.embeddings.getByType, {
      databaseId: this.databaseId,
      type,
    });

    return results.map((r) => ({
      id: r.embeddingId,
      embedding: r.embedding,
      type: r.type,
      trajectoryId: r.trajectoryId,
      stepIndex: r.stepIndex,
    }));
  }

  async deleteEmbeddingsForTrajectory(trajectoryId: string): Promise<void> {
    await this.mutate(api.embeddings.deleteForTrajectory, {
      databaseId: this.databaseId,
      trajectoryId,
    });
  }

  async searchByEmbedding(
    query: number[],
    type: "trajectory" | "step",
    k: number
  ): Promise<EmbeddingSearchResult[]> {
    const results = await this.query<any[]>(api.embeddings.search, {
      databaseId: this.databaseId,
      query,
      type,
      k,
    });

    return results.map((r) => ({
      id: r.id,
      trajectoryId: r.trajectoryId,
      stepIndex: r.stepIndex,
      score: r.score,
    }));
  }

  // =========================================================================
  // Step Examples (derived from trajectories)
  // =========================================================================

  async getStepExamplesForTrajectory(trajectoryId: string): Promise<StepExample[]> {
    const trajectory = this.trajectories.get(trajectoryId);
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

  async getAllStepExamples(): Promise<StepExample[]> {
    const examples: StepExample[] = [];

    for (const trajectory of this.trajectories.values()) {
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
