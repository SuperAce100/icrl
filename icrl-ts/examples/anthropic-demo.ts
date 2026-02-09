/**
 * Live Anthropic example (network/API required).
 *
 * Run with:
 *   bun run example:anthropic
 */

import * as assert from "node:assert/strict";
import Anthropic from "@anthropic-ai/sdk";
import { Agent, AnthropicProvider, FileSystemAdapter } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DEFAULT_PROMPTS,
  LocalHashEmbedder,
  MathEnvironment,
} from "./_demo_shared";
import { loadWorkspaceEnv } from "./_live_env";

async function main(): Promise<void> {
  loadWorkspaceEnv();

  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("ANTHROPIC_API_KEY is not set");
  }

  const dbPath = createTempDir("anthropic-demo");

  try {
    const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

    const agent = new Agent({
      llm: new AnthropicProvider(anthropic, {
        model: process.env.ANTHROPIC_MODEL ?? "claude-sonnet-4-20250514",
        temperature: 0,
      }),
      embedder: new LocalHashEmbedder(),
      storage: new FileSystemAdapter(dbPath),
      planPrompt: DEFAULT_PROMPTS.plan,
      reasonPrompt: DEFAULT_PROMPTS.reason,
      actPrompt: DEFAULT_PROMPTS.act,
      maxSteps: 3,
      k: 1,
    });

    await agent.init();
    const trajectory = await agent.train(new MathEnvironment(), "multiply 6 and 7");

    assert.equal(trajectory.success, true);
    assert.equal(agent.getStats().totalTrajectories, 1);

    console.log("example:anthropic passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
