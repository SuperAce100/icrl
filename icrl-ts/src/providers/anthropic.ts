/**
 * Anthropic provider for LLM completions.
 */

import type { Message } from "../models";
import type { LLMProvider } from "../protocols";

// Type for Anthropic client (peer dependency)
type AnthropicClient = {
  messages: {
    create: (params: {
      model: string;
      max_tokens: number;
      system?: string;
      messages: Array<{ role: "user" | "assistant"; content: string }>;
      temperature?: number;
    }) => Promise<{
      content: Array<{ type: string; text?: string }>;
    }>;
  };
};

export interface AnthropicProviderOptions {
  /** Anthropic model to use (default: "claude-sonnet-4-20250514") */
  model?: string;
  /** Sampling temperature (default: 0.7) */
  temperature?: number;
  /** Maximum tokens to generate (default: 4096) */
  maxTokens?: number;
}

/**
 * Anthropic LLM provider.
 *
 * @example
 * ```typescript
 * import Anthropic from "@anthropic-ai/sdk";
 * import { AnthropicProvider } from "icrl";
 *
 * const anthropic = new Anthropic();
 * const provider = new AnthropicProvider(anthropic, {
 *   model: "claude-sonnet-4-20250514"
 * });
 * ```
 */
export class AnthropicProvider implements LLMProvider {
  private readonly client: AnthropicClient;
  private readonly model: string;
  private readonly temperature: number;
  private readonly maxTokens: number;

  constructor(client: AnthropicClient, options: AnthropicProviderOptions = {}) {
    this.client = client;
    this.model = options.model ?? "claude-sonnet-4-20250514";
    this.temperature = options.temperature ?? 0.7;
    this.maxTokens = options.maxTokens ?? 4096;
  }

  async complete(messages: Message[]): Promise<string> {
    // Extract system message if present
    let systemPrompt: string | undefined;
    const chatMessages: Array<{ role: "user" | "assistant"; content: string }> = [];

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

    const response = await this.client.messages.create({
      model: this.model,
      max_tokens: this.maxTokens,
      system: systemPrompt,
      messages: chatMessages,
      temperature: this.temperature,
    });

    // Extract text from response
    const textBlock = response.content.find((block) => block.type === "text");
    return textBlock?.text ?? "";
  }
}
