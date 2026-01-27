/**
 * Protocol/interface definitions for ICRL components.
 * Equivalent to Python's Protocol classes.
 */

import type { Message } from "./models";

// ============================================================================
// Environment
// ============================================================================

/**
 * Result of an environment step.
 */
export interface StepResult {
  /** The resulting observation string */
  observation: string;
  /** Whether the episode has ended */
  done: boolean;
  /** Whether the goal was achieved */
  success: boolean;
}

/**
 * Protocol for environments that the agent interacts with.
 *
 * Implement this interface for your custom environment.
 *
 * @example
 * ```typescript
 * class MyEnvironment implements Environment {
 *   private goal: string = "";
 *
 *   reset(goal: string): string {
 *     this.goal = goal;
 *     return "Initial state description";
 *   }
 *
 *   async step(action: string): Promise<StepResult> {
 *     const observation = await execute(action);
 *     const success = checkGoal(this.goal);
 *     return { observation, done: success, success };
 *   }
 * }
 * ```
 */
export interface Environment {
  /**
   * Reset the environment for a new episode.
   *
   * The environment should store the goal internally for use
   * when determining success in step().
   *
   * @param goal - The goal description for this episode.
   * @returns The initial observation as a string.
   */
  reset(goal: string): string | Promise<string>;

  /**
   * Execute an action in the environment.
   *
   * @param action - The action to execute.
   * @returns A StepResult with observation, done, and success.
   */
  step(action: string): StepResult | Promise<StepResult>;
}

// ============================================================================
// LLMProvider
// ============================================================================

/**
 * Protocol for LLM providers.
 *
 * Implement this interface for custom LLM integrations,
 * or use the built-in OpenAIProvider/AnthropicProvider.
 *
 * @example
 * ```typescript
 * class MyLLMProvider implements LLMProvider {
 *   async complete(messages: Message[]): Promise<string> {
 *     const response = await myLLMCall(messages);
 *     return response.text;
 *   }
 * }
 * ```
 */
export interface LLMProvider {
  /**
   * Generate a completion from the given messages.
   *
   * @param messages - A list of Message objects representing the conversation.
   * @returns The generated completion as a string.
   */
  complete(messages: Message[]): Promise<string>;
}

// ============================================================================
// Embedder
// ============================================================================

/**
 * Protocol for embedding providers.
 *
 * Used internally for semantic similarity search in the trajectory database.
 *
 * @example
 * ```typescript
 * class OpenAIEmbedder implements Embedder {
 *   readonly dimension = 1536;
 *
 *   async embed(texts: string[]): Promise<number[][]> {
 *     const response = await openai.embeddings.create({
 *       model: "text-embedding-3-small",
 *       input: texts,
 *     });
 *     return response.data.map(d => d.embedding);
 *   }
 *
 *   async embedSingle(text: string): Promise<number[]> {
 *     const [embedding] = await this.embed([text]);
 *     return embedding!;
 *   }
 * }
 * ```
 */
export interface Embedder {
  /** Embedding dimensionality */
  readonly dimension: number;

  /**
   * Generate embeddings for a list of texts.
   *
   * @param texts - List of strings to embed.
   * @returns List of embedding vectors.
   */
  embed(texts: string[]): Promise<number[][]>;

  /**
   * Generate embedding for a single text.
   *
   * @param text - String to embed.
   * @returns Embedding vector.
   */
  embedSingle(text: string): Promise<number[]>;
}

// ============================================================================
// Callbacks
// ============================================================================

/**
 * Callback for when the agent produces thinking/reasoning text.
 */
export type OnThinkingCallback = (text: string) => void;

/**
 * Callback for when a tool/action is about to be executed.
 */
export type OnToolStartCallback = (tool: string, params: Record<string, unknown>) => void;

/**
 * Callback for when a tool/action execution completes.
 */
export type OnToolEndCallback = (tool: string, result: { output: string; error?: string }) => void;

/**
 * Callback for when a step is completed.
 */
export type OnStepCallback = (
  step: { observation: string; reasoning: string; action: string },
  context: { goal: string; plan: string; stepNumber: number }
) => void;

/**
 * All available agent callbacks.
 */
export interface AgentCallbacks {
  onThinking?: OnThinkingCallback;
  onToolStart?: OnToolStartCallback;
  onToolEnd?: OnToolEndCallback;
  onStep?: OnStepCallback;
}
