/**
 * Trajectory retriever for in-context learning.
 */

import type { StepExample } from "./models";
import type { TrajectoryDatabase } from "./database";

/**
 * Retriever for finding relevant step examples for in-context learning.
 *
 * Following the paper, retrieves different examples at each decision point
 * based on relevance to the current situation. Uses step-level retrieval
 * for fine-grained similarity matching.
 */
export class TrajectoryRetriever {
  private readonly database: TrajectoryDatabase;
  private readonly k: number;
  private retrievedIds: string[] = [];

  /**
   * Initialize the retriever.
   *
   * @param database - The trajectory database to search.
   * @param k - Default number of examples to retrieve.
   */
  constructor(database: TrajectoryDatabase, k: number = 2) {
    this.database = database;
    this.k = k;
  }

  /**
   * Retrieve step examples for planning phase.
   *
   * @param goal - The goal description.
   * @param k - Number of examples to retrieve. Uses default if undefined.
   * @returns List of relevant step examples.
   */
  async retrieveForPlan(goal: string, k?: number): Promise<StepExample[]> {
    const numExamples = k ?? this.k;
    const steps = await this.database.searchSteps(goal, numExamples);
    this.trackRetrievedSteps(steps);
    return steps;
  }

  /**
   * Retrieve step examples for a reasoning/acting step.
   *
   * @param goal - The goal description.
   * @param plan - The current plan.
   * @param observation - The current observation.
   * @param k - Number of examples to retrieve. Uses default if undefined.
   * @returns List of relevant step examples.
   */
  async retrieveForStep(
    goal: string,
    _plan: string,
    observation: string,
    k?: number
  ): Promise<StepExample[]> {
    const numExamples = k ?? this.k;
    // Query based on the current task + observation for step-level similarity.
    // (The plan string can be very long/noisy; we focus on goal + observation.)
    const query = `${goal}\n${observation}`;
    const steps = await this.database.searchSteps(query, numExamples);
    this.trackRetrievedSteps(steps);
    return steps;
  }

  private trackRetrievedSteps(steps: StepExample[]): void {
    for (const step of steps) {
      if (!this.retrievedIds.includes(step.trajectoryId)) {
        this.retrievedIds.push(step.trajectoryId);
      }
    }
  }

  /**
   * Get all trajectory IDs retrieved in this session.
   */
  getRetrievedIds(): string[] {
    return [...this.retrievedIds];
  }

  /**
   * Clear the list of retrieved trajectory IDs.
   */
  clearRetrieved(): void {
    this.retrievedIds = [];
  }

  /**
   * Record the result of the episode for curation.
   *
   * @param success - Whether the episode was successful.
   */
  recordEpisodeResult(success: boolean): void {
    if (this.retrievedIds.length > 0) {
      for (const id of this.retrievedIds) {
        this.database.recordRetrieval(id, success);
      }
    }
    this.clearRetrieved();
  }
}
