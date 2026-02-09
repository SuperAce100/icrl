/**
 * Live OpenAI example (network/API required).
 *
 * Run with:
 *   bun run example:openai
 */

import * as assert from "node:assert/strict";
import OpenAI from "openai";
import { Agent, FileSystemAdapter, OpenAIEmbedder, OpenAIProvider } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DEFAULT_PROMPTS,
  MathEnvironment,
} from "./_demo_shared";
import { loadWorkspaceEnv } from "./_live_env";

async function main(): Promise<void> {
  loadWorkspaceEnv();

  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is not set");
  }

  const dbPath = createTempDir("openai-demo");

  try {
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

    const agent = new Agent({
      llm: new OpenAIProvider(openai, { model: "gpt-4o-mini", temperature: 0 }),
      embedder: new OpenAIEmbedder(openai, { model: "text-embedding-3-small" }),
      storage: new FileSystemAdapter(dbPath),
      planPrompt: DEFAULT_PROMPTS.plan,
      reasonPrompt: DEFAULT_PROMPTS.reason,
      actPrompt: DEFAULT_PROMPTS.act,
      maxSteps: 3,
      k: 1,
    });

    await agent.init();
    const trajectory = await agent.train(new MathEnvironment(), "add 12 and 8");

    assert.equal(trajectory.success, true);
    assert.equal(agent.getStats().totalTrajectories, 1);

    console.log("example:openai passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
