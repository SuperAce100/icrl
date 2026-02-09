/**
 * Demonstrates all built-in providers with mocked SDK clients.
 *
 * Run with:
 *   bun run example:providers
 */

import * as assert from "node:assert/strict";
import {
  ANTHROPIC_VERTEX_MODEL_ALIASES,
  AnthropicProvider,
  AnthropicVertexProvider,
  OpenAIEmbedder,
  OpenAIProvider,
  type Message,
} from "../src";

function buildMessages(): Message[] {
  return [
    { role: "system", content: "You are helpful." },
    { role: "user", content: "Say hi" },
  ];
}

async function main(): Promise<void> {
  const openaiClient = {
    chat: {
      completions: {
        create: async (params: {
          model: string;
          messages: Array<{ role: string; content: string }>;
          temperature?: number;
          max_tokens?: number;
        }) => ({
          choices: [{ message: { content: `openai:${params.model}:${params.messages.length}` } }],
        }),
      },
    },
    embeddings: {
      create: async (params: { model: string; input: string | string[] }) => {
        const inputs = Array.isArray(params.input) ? params.input : [params.input];
        return {
          data: inputs.map((input) => ({
            embedding: [input.length, params.model.length, 1],
          })),
        };
      },
    },
  };

  const openaiProvider = new OpenAIProvider(openaiClient, { model: "gpt-4o-mini" });
  const openaiResult = await openaiProvider.complete(buildMessages());
  assert.equal(openaiResult, "openai:gpt-4o-mini:2");

  const openaiEmbedder = new OpenAIEmbedder(openaiClient, {
    model: "text-embedding-3-small",
  });
  const embedding = await openaiEmbedder.embedSingle("abc");
  assert.deepEqual(embedding, [3, 22, 1]);

  const anthropicClient = {
    messages: {
      create: async (params: {
        model: string;
        max_tokens: number;
        system?: string;
        messages: Array<{ role: "user" | "assistant"; content: string }>;
        temperature?: number;
      }) => ({
        content: [{ type: "text", text: `anthropic:${params.model}:${params.messages.length}` }],
      }),
    },
  };

  const anthropicProvider = new AnthropicProvider(anthropicClient, {
    model: "claude-sonnet-4-20250514",
  });
  const anthropicResult = await anthropicProvider.complete(buildMessages());
  assert.equal(anthropicResult, "anthropic:claude-sonnet-4-20250514:1");

  const vertexClient = {
    messages: {
      create: async (params: {
        model: string;
        max_tokens: number;
        system?: string;
        messages: Array<{ role: "user" | "assistant"; content: string }>;
      }) => ({
        content: [{ type: "text", text: `vertex:${params.model}:${params.messages.length}` }],
      }),
    },
  };

  const vertexProvider = new AnthropicVertexProvider(vertexClient, {
    model: "claude-opus-4-5",
  });
  const vertexResult = await vertexProvider.complete(buildMessages());
  assert.equal(vertexResult, "vertex:claude-opus-4-5@20251101:1");

  assert.equal(ANTHROPIC_VERTEX_MODEL_ALIASES["claude-opus-4-5"], "claude-opus-4-5@20251101");

  console.log("example:providers passed");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
