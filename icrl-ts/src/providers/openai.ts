/**
 * OpenAI provider for LLM completions and embeddings.
 */

import type { Message } from "../models";
import type { LLMProvider, Embedder } from "../protocols";

// Type for OpenAI client (peer dependency)
type OpenAIClient = {
  chat: {
    completions: {
      create: (params: {
        model: string;
        messages: Array<{ role: string; content: string }>;
        temperature?: number;
        max_tokens?: number;
      }) => Promise<{
        choices: Array<{ message: { content: string | null } }>;
      }>;
    };
  };
  embeddings: {
    create: (params: {
      model: string;
      input: string | string[];
    }) => Promise<{
      data: Array<{ embedding: number[] }>;
    }>;
  };
};

export interface OpenAIProviderOptions {
  /** OpenAI model to use (default: "gpt-4o-mini") */
  model?: string;
  /** Sampling temperature (default: 0.7) */
  temperature?: number;
  /** Maximum tokens to generate */
  maxTokens?: number;
}

/**
 * OpenAI LLM provider.
 *
 * @example
 * ```typescript
 * import OpenAI from "openai";
 * import { OpenAIProvider } from "icrl";
 *
 * const openai = new OpenAI();
 * const provider = new OpenAIProvider(openai, { model: "gpt-4o" });
 * ```
 */
export class OpenAIProvider implements LLMProvider {
  private readonly client: OpenAIClient;
  private readonly model: string;
  private readonly temperature: number;
  private readonly maxTokens?: number;

  constructor(client: OpenAIClient, options: OpenAIProviderOptions = {}) {
    this.client = client;
    this.model = options.model ?? "gpt-4o-mini";
    this.temperature = options.temperature ?? 0.7;
    this.maxTokens = options.maxTokens;
  }

  async complete(messages: Message[]): Promise<string> {
    const response = await this.client.chat.completions.create({
      model: this.model,
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      temperature: this.temperature,
      max_tokens: this.maxTokens,
    });

    return response.choices[0]?.message.content ?? "";
  }
}

export interface OpenAIEmbedderOptions {
  /** Embedding model to use (default: "text-embedding-3-small") */
  model?: string;
}

/**
 * OpenAI embeddings provider.
 *
 * @example
 * ```typescript
 * import OpenAI from "openai";
 * import { OpenAIEmbedder } from "icrl";
 *
 * const openai = new OpenAI();
 * const embedder = new OpenAIEmbedder(openai);
 * ```
 */
export class OpenAIEmbedder implements Embedder {
  private readonly client: OpenAIClient;
  private readonly model: string;

  /** Embedding dimension for text-embedding-3-small */
  readonly dimension = 1536;

  constructor(client: OpenAIClient, options: OpenAIEmbedderOptions = {}) {
    this.client = client;
    this.model = options.model ?? "text-embedding-3-small";
  }

  async embed(texts: string[]): Promise<number[][]> {
    if (texts.length === 0) return [];

    const response = await this.client.embeddings.create({
      model: this.model,
      input: texts,
    });

    return response.data.map((d) => d.embedding);
  }

  async embedSingle(text: string): Promise<number[]> {
    const [embedding] = await this.embed([text]);
    return embedding!;
  }
}
