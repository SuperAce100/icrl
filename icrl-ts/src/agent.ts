/**
 * Main Agent class for ICRL.
 */

import type { Trajectory } from "./models";
import type { Environment, LLMProvider, OnStepCallback, Embedder } from "./protocols";
import type { StorageAdapter } from "./storage";
import { TrajectoryDatabase } from "./database";
import { TrajectoryRetriever } from "./retriever";
import { ReActLoop } from "./loop";
import { CurationManager } from "./curation";

/**
 * Options for creating an ICRL Agent.
 */
export interface AgentOptions {
  /** The LLM provider for generating completions */
  llm: LLMProvider;
  /** Storage adapter for persisting trajectories (e.g., FileSystemAdapter, ConvexAdapter) */
  storage: StorageAdapter;
  /** Embedder for semantic similarity search */
  embedder: Embedder;
  /** Template for planning prompts. Placeholders: {goal}, {examples} */
  planPrompt: string;
  /** Template for reasoning prompts. Placeholders: {goal}, {plan}, {observation}, {history}, {examples} */
  reasonPrompt: string;
  /** Template for action prompts. Placeholders: {goal}, {plan}, {reasoning}, {history}, {examples} */
  actPrompt: string;
  /** Number of examples to retrieve at each decision point (default: 3) */
  k?: number;
  /** Maximum number of steps per episode (default: 30) */
  maxSteps?: number;
  /** Initial trajectories to populate the database */
  seedTrajectories?: Trajectory[];
  /** Optional callback called after each step */
  onStep?: OnStepCallback;
  /** Utility threshold below which trajectories are pruned (default: 0.3) */
  curationThreshold?: number;
  /** Minimum retrievals before a trajectory can be pruned (default: 5) */
  curationMinRetrievals?: number;
  /**
   * Optional callback to verify a trajectory before storing.
   * Return true to store, false to discard.
   */
  verifyTrajectory?: (trajectory: Trajectory) => boolean | Promise<boolean>;
}

/**
 * ICRL Agent that learns from self-generated trajectories.
 *
 * This agent implements the Self-Generated In-Context Learning algorithm,
 * which bootstraps performance by accumulating successful trajectories
 * and using them as in-context examples for future tasks.
 *
 * @example
 * ```typescript
 * import OpenAI from "openai";
 * import { Agent, OpenAIProvider, OpenAIEmbedder, FileSystemAdapter } from "icrl";
 *
 * const openai = new OpenAI();
 *
 * const agent = new Agent({
 *   llm: new OpenAIProvider(openai, { model: "gpt-4o" }),
 *   embedder: new OpenAIEmbedder(openai),
 *   storage: new FileSystemAdapter("./trajectories"),
 *   planPrompt: "Goal: {goal}\n\nExamples:\n{examples}\n\nCreate a plan:",
 *   reasonPrompt: "Goal: {goal}\nPlan: {plan}\nObservation: {observation}\nThink step by step:",
 *   actPrompt: "Goal: {goal}\nPlan: {plan}\nReasoning: {reasoning}\nNext action:",
 * });
 *
 * // Training: successful trajectories are stored
 * const trajectory = await agent.train(env, "Complete the task");
 *
 * // Inference: uses stored examples but doesn't add new ones
 * const result = await agent.run(env, "Another task");
 * ```
 */
export class Agent {
  private readonly llm: LLMProvider;
  private readonly database: TrajectoryDatabase;
  private readonly retriever: TrajectoryRetriever;
  private readonly loop: ReActLoop;
  private readonly curation: CurationManager;
  private readonly verifyTrajectory?: (trajectory: Trajectory) => boolean | Promise<boolean>;
  private initialized = false;

  constructor(private readonly options: AgentOptions) {
    this.llm = options.llm;
    this.verifyTrajectory = options.verifyTrajectory;

    // Create database with storage adapter
    this.database = new TrajectoryDatabase(options.storage, options.embedder);

    // Create retriever
    this.retriever = new TrajectoryRetriever(this.database, options.k ?? 3);

    // Create curation manager
    this.curation = new CurationManager(this.database, {
      threshold: options.curationThreshold ?? 0.3,
      minRetrievals: options.curationMinRetrievals ?? 5,
    });

    // Create ReAct loop
    this.loop = new ReActLoop(this.llm, this.retriever, {
      planPrompt: options.planPrompt,
      reasonPrompt: options.reasonPrompt,
      actPrompt: options.actPrompt,
      maxSteps: options.maxSteps ?? 30,
      onStep: options.onStep,
    });
  }

  /**
   * Initialize the agent (load database from disk).
   * Must be called before train() or run().
   */
  async init(): Promise<void> {
    if (this.initialized) return;

    await this.database.load();

    // Add seed trajectories if provided
    if (this.options.seedTrajectories) {
      const existingIds = new Set(this.database.getAll().map((t) => t.id));
      for (const traj of this.options.seedTrajectories) {
        if (!existingIds.has(traj.id)) {
          await this.database.add(traj);
        }
      }
    }

    this.initialized = true;
  }

  /**
   * Get the trajectory database.
   */
  getDatabase(): TrajectoryDatabase {
    return this.database;
  }

  /**
   * Run a training episode.
   *
   * In training mode, successful trajectories are added to the database
   * and used as examples for future episodes.
   */
  async train(env: Environment, goal: string): Promise<Trajectory> {
    if (!this.initialized) {
      await this.init();
    }

    const trajectory = await this.loop.run(env, goal);

    if (trajectory.success) {
      // Check verification callback if provided
      let shouldStore = true;
      if (this.verifyTrajectory) {
        shouldStore = await Promise.resolve(this.verifyTrajectory(trajectory));
      }

      if (shouldStore) {
        await this.database.add(trajectory);
        await this.curation.maybeCurate();
      }
    }

    return trajectory;
  }

  /**
   * Run an inference episode.
   *
   * In inference mode, the database is frozen and trajectories are
   * not added regardless of success.
   */
  async run(env: Environment, goal: string): Promise<Trajectory> {
    if (!this.initialized) {
      await this.init();
    }

    return this.loop.run(env, goal);
  }

  /**
   * Train on multiple goals.
   */
  async trainBatch(
    envFactory: () => Environment,
    goals: string[]
  ): Promise<Trajectory[]> {
    const trajectories: Trajectory[] = [];
    for (const goal of goals) {
      const env = envFactory();
      const trajectory = await this.train(env, goal);
      trajectories.push(trajectory);
    }
    return trajectories;
  }

  /**
   * Run inference on multiple goals.
   */
  async runBatch(
    envFactory: () => Environment,
    goals: string[]
  ): Promise<Trajectory[]> {
    const trajectories: Trajectory[] = [];
    for (const goal of goals) {
      const env = envFactory();
      const trajectory = await this.run(env, goal);
      trajectories.push(trajectory);
    }
    return trajectories;
  }

  /**
   * Get statistics about the agent's database.
   */
  getStats(): { totalTrajectories: number; successfulTrajectories: number; successRate: number } {
    const allTrajs = this.database.getAll();
    const successful = allTrajs.filter((t) => t.success).length;

    return {
      totalTrajectories: allTrajs.length,
      successfulTrajectories: successful,
      successRate: allTrajs.length > 0 ? successful / allTrajs.length : 0,
    };
  }
}
