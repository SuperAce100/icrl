/**
 * ICRL - In-Context Reinforcement Learning for LLM Agents
 *
 * This library implements the Self-Generated In-Context Learning algorithm,
 * enabling LLM agents to bootstrap their own performance by learning from
 * successful trajectories.
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
 * await agent.init();
 *
 * // Training: successful trajectories are stored
 * const trajectory = await agent.train(env, "Complete the task");
 *
 * // Inference: uses stored examples but doesn't add new ones
 * const result = await agent.run(env, "Another task");
 * ```
 *
 * @packageDocumentation
 */

// Core agent
export { Agent } from "./agent";
export type { AgentOptions } from "./agent";

// Models and types
export {
  MessageSchema,
  StepSchema,
  StepExampleSchema,
  TrajectorySchema,
  StepContextSchema,
  CurationMetadataSchema,
  DeferredValidationSchema,
  trajectoryToExampleString,
  stepExampleToString,
  formatExamples,
  formatHistory,
  updateCurationUtility,
} from "./models";
export type {
  Message,
  Step,
  StepExample,
  Trajectory,
  StepContext,
  CurationMetadata,
  DeferredValidation,
} from "./models";

// Protocols/interfaces
export type {
  Environment,
  StepResult,
  LLMProvider,
  Embedder,
  OnThinkingCallback,
  OnToolStartCallback,
  OnToolEndCallback,
  OnStepCallback,
  AgentCallbacks,
} from "./protocols";

// Storage adapters
export type {
  StorageAdapter,
  StoredEmbedding,
  EmbeddingSearchResult,
} from "./storage";
export { BaseStorageAdapter } from "./storage";

// Built-in adapters
export { FileSystemAdapter } from "./adapters";
export type { FileSystemAdapterOptions } from "./adapters";

// Database
export { TrajectoryDatabase } from "./database";
export type { TrajectoryDatabaseOptions } from "./database";

// Retriever
export { TrajectoryRetriever } from "./retriever";

// Loop
export { ReActLoop } from "./loop";
export type { StepContext as LoopStepContext, ReActLoopOptions } from "./loop";

// Curation
export { CurationManager } from "./curation";
export type { CurationManagerOptions } from "./curation";

// Providers
export {
  OpenAIProvider,
  OpenAIEmbedder,
  AnthropicProvider,
  AnthropicVertexProvider,
  ANTHROPIC_VERTEX_MODEL_ALIASES,
} from "./providers";
export type {
  OpenAIProviderOptions,
  OpenAIEmbedderOptions,
  AnthropicProviderOptions,
  AnthropicVertexProviderOptions,
} from "./providers";
