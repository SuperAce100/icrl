/**
 * Automatic curation for trajectory databases.
 */

import type { TrajectoryDatabase } from "./database";

export interface CurationManagerOptions {
  /** Utility score threshold below which trajectories are pruned (default: 0.3) */
  threshold?: number;
  /** Minimum retrievals before a trajectory can be pruned (default: 5) */
  minRetrievals?: number;
  /** Run curation after this many successful episodes (default: 10) */
  curateEvery?: number;
}

/**
 * Manages automatic curation of trajectory databases.
 *
 * Implements exemplar-level curation from the ICRL paper:
 * - Tracks which trajectories are retrieved and whether they lead to success
 * - Periodically prunes trajectories with low utility scores
 */
export class CurationManager {
  private readonly database: TrajectoryDatabase;
  private readonly threshold: number;
  private readonly minRetrievals: number;
  private readonly curateEvery: number;
  private episodesSinceCuration = 0;

  constructor(database: TrajectoryDatabase, options: CurationManagerOptions = {}) {
    this.database = database;
    this.threshold = options.threshold ?? 0.3;
    this.minRetrievals = options.minRetrievals ?? 5;
    this.curateEvery = options.curateEvery ?? 10;
  }

  /**
   * Check if curation should run and run it if so.
   * @returns True if curation was performed, false otherwise.
   */
  async maybeCurate(): Promise<boolean> {
    this.episodesSinceCuration++;

    if (this.episodesSinceCuration >= this.curateEvery) {
      await this.curate();
      this.episodesSinceCuration = 0;
      return true;
    }

    return false;
  }

  /**
   * Run curation to prune low-utility trajectories.
   * @returns List of trajectory IDs that were removed.
   */
  async curate(): Promise<string[]> {
    const removedIds: string[] = [];

    for (const trajectory of this.database.getAll()) {
      const metadata = this.database.getCurationMetadata(trajectory.id);

      if (!metadata) continue;
      if (metadata.timesRetrieved < this.minRetrievals) continue;

      if (metadata.utilityScore < this.threshold) {
        if (await this.database.remove(trajectory.id)) {
          removedIds.push(trajectory.id);
        }
      }
    }

    return removedIds;
  }

  /**
   * Get utility scores for all trajectories.
   */
  getUtilityScores(): Map<string, number> {
    const scores = new Map<string, number>();

    for (const trajectory of this.database.getAll()) {
      const metadata = this.database.getCurationMetadata(trajectory.id);
      if (metadata) {
        scores.set(trajectory.id, metadata.utilityScore);
      }
    }

    return scores;
  }

  /**
   * Get trajectory IDs that would be pruned if curation ran now.
   */
  getLowUtilityTrajectories(): string[] {
    const lowUtility: string[] = [];

    for (const trajectory of this.database.getAll()) {
      const metadata = this.database.getCurationMetadata(trajectory.id);

      if (!metadata) continue;
      if (metadata.timesRetrieved < this.minRetrievals) continue;

      if (metadata.utilityScore < this.threshold) {
        lowUtility.push(trajectory.id);
      }
    }

    return lowUtility;
  }
}
