/**
 * Anthropic Vertex AI provider for Claude models on Google Cloud.
 *
 * This provider uses the @anthropic-ai/vertex-sdk package to call Claude
 * models through Google Cloud's Vertex AI service.
 */

import type { Message } from "../models";
import type { LLMProvider } from "../protocols";

// Type for AnthropicVertex client (peer dependency)
type AnthropicVertexClient = {
  messages: {
    create: (params: {
      model: string;
      max_tokens: number;
      system?: string;
      messages: Array<{ role: "user" | "assistant"; content: string }>;
    }) => Promise<{
      content: Array<{ type: string; text?: string }>;
    }>;
  };
};

// Model aliases for convenience
export const ANTHROPIC_VERTEX_MODEL_ALIASES: Record<string, string> = {
  // Claude 3.5 models
  "claude-3-5-sonnet": "claude-3-5-sonnet-v2@20241022",
  "claude-3.5-sonnet": "claude-3-5-sonnet-v2@20241022",
  "claude-3-5-haiku": "claude-3-5-haiku@20241022",
  // Claude 3.7 models
  "claude-3-7-sonnet": "claude-3-7-sonnet@20250219",
  "claude-3.7-sonnet": "claude-3-7-sonnet@20250219",
  // Claude 4 models
  "claude-sonnet-4": "claude-sonnet-4@20250514",
  "claude-4-sonnet": "claude-sonnet-4@20250514",
  "claude-opus-4": "claude-opus-4@20250514",
  "claude-4-opus": "claude-opus-4@20250514",
  // Claude 4.5 models
  "claude-opus-4.5": "claude-opus-4-5@20251101",
  "claude-opus-4-5": "claude-opus-4-5@20251101",
  "claude-4.5-opus": "claude-opus-4-5@20251101",
  "claude-sonnet-4.5": "claude-sonnet-4-5@20251101",
  "claude-sonnet-4-5": "claude-sonnet-4-5@20251101",
  "claude-4.5-sonnet": "claude-sonnet-4-5@20251101",
};

export interface AnthropicVertexProviderOptions {
  /** Model name or alias (default: "claude-opus-4-5") */
  model?: string;
  /** Maximum tokens to generate (default: 4096) */
  maxTokens?: number;
}

/**
 * Resolve model shorthand to full vertex model name.
 */
function resolveModel(model: string): string {
  return ANTHROPIC_VERTEX_MODEL_ALIASES[model] ?? model;
}

/**
 * Anthropic Vertex AI LLM provider.
 *
 * Requires the `@anthropic-ai/vertex-sdk` package and Google Cloud credentials.
 *
 * @example
 * ```typescript
 * import { AnthropicVertex } from "@anthropic-ai/vertex-sdk";
 * import { AnthropicVertexProvider } from "icrl";
 *
 * const client = new AnthropicVertex({
 *   region: "us-east5",
 *   projectId: "my-project",
 * });
 *
 * const provider = new AnthropicVertexProvider(client, {
 *   model: "claude-opus-4-5",
 * });
 * ```
 */
export class AnthropicVertexProvider implements LLMProvider {
  private readonly client: AnthropicVertexClient;
  private readonly model: string;
  private readonly maxTokens: number;

  constructor(
    client: AnthropicVertexClient,
    options: AnthropicVertexProviderOptions = {}
  ) {
    this.client = client;
    this.model = resolveModel(options.model ?? "claude-opus-4-5");
    this.maxTokens = options.maxTokens ?? 4096;
  }

  async complete(messages: Message[]): Promise<string> {
    // Extract system message if present
    let systemPrompt: string | undefined;
    const chatMessages: Array<{ role: "user" | "assistant"; content: string }> =
      [];

    for (const msg of messages) {
      if (msg.role === "system") {
        systemPrompt = msg.content;
      } else if (msg.role === "user" || msg.role === "assistant") {
        chatMessages.push({ role: msg.role, content: msg.content });
      }
    }

    // Anthropic requires alternating user/assistant messages
    // If first message isn't user, prepend a user message
    if (chatMessages.length > 0 && chatMessages[0]?.role !== "user") {
      chatMessages.unshift({ role: "user", content: "Hello" });
    }

    // Ensure we have at least one message
    if (chatMessages.length === 0) {
      chatMessages.push({ role: "user", content: "Hello" });
    }

    const response = await this.client.messages.create({
      model: this.model,
      max_tokens: this.maxTokens,
      system: systemPrompt,
      messages: chatMessages,
    });

    // Extract text from response
    const textBlock = response.content.find((block) => block.type === "text");
    return textBlock?.text ?? "";
  }
}
