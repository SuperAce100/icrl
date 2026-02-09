/**
 * Web-example integration demo using Convex storage.
 *
 * This reuses the ConvexAdapter from web-example so trajectories are stored
 * in the same backend architecture as the Next.js web demo.
 *
 * Run with:
 *   bun run example:web
 *
 * Required env vars:
 *   OPENAI_API_KEY
 *   NEXT_PUBLIC_CONVEX_URL
 *
 * Optional:
 *   ICRL_CONVEX_DATABASE_ID (if omitted, a demo database is created)
 */

import * as assert from "node:assert/strict";
import OpenAI from "openai";
import { ConvexHttpClient } from "convex/browser";
import { Agent, OpenAIProvider } from "../src";
import { ConvexAdapter } from "../web-example/src/lib/convex-adapter";
import { api } from "../web-example/convex/_generated/api";
import {
  LocalHashEmbedder,
  DEFAULT_PROMPTS,
  MathEnvironment,
} from "./_demo_shared";
import { loadWorkspaceEnv } from "./_live_env";

async function main(): Promise<void> {
  loadWorkspaceEnv();

  const apiKey = process.env.OPENAI_API_KEY;
  const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;
  let databaseId = process.env.ICRL_CONVEX_DATABASE_ID;

  if (!apiKey || !convexUrl) {
    throw new Error("Missing required env vars: OPENAI_API_KEY, NEXT_PUBLIC_CONVEX_URL");
  }

  const openai = new OpenAI({ apiKey });
  const convexClient = new ConvexHttpClient(convexUrl);

  if (!databaseId) {
    databaseId = await convexClient.mutation(api.databases.create as any, {
      name: `icrl-ts-demo-${Date.now()}`,
      description: "Auto-created by web-convex-demo.ts",
      systemPrompt: "Demo database for ICRL TypeScript web integration.",
    });
    console.log(`Created demo Convex database: ${databaseId}`);
  }

  const adapter = new ConvexAdapter(convexClient as any, {
    databaseId: databaseId as any,
  });

  const agent = new Agent({
    llm: new OpenAIProvider(openai, { model: "gpt-4o-mini", temperature: 0 }),
    embedder: new LocalHashEmbedder(),
    storage: adapter,
    planPrompt: DEFAULT_PROMPTS.plan,
    reasonPrompt: DEFAULT_PROMPTS.reason,
    actPrompt: DEFAULT_PROMPTS.act,
    maxSteps: 3,
    k: 1,
  });

  await agent.init();
  const trajectory = await agent.train(new MathEnvironment(), "add 17 and 25");

  assert.equal(trajectory.success, true);

  const stats = agent.getStats();
  console.log(`Convex-backed trajectories in this DB: ${stats.totalTrajectories}`);
  console.log("example:web passed");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
