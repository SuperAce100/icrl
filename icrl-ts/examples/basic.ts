/**
 * Basic offline example using deterministic mocks.
 *
 * Run with:
 *   bun run example:basic
 */

import * as assert from "node:assert/strict";
import { Agent, FileSystemAdapter } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DEFAULT_PROMPTS,
  DeterministicEmbedder,
  MathEnvironment,
  ScriptedMathLLM,
  assertSuccessful,
} from "./_shared";

async function main(): Promise<void> {
  const dbPath = createTempDir("basic");

  try {
    const stepsSeen: number[] = [];

    const agent = new Agent({
      llm: new ScriptedMathLLM(),
      embedder: new DeterministicEmbedder(),
      storage: new FileSystemAdapter(dbPath),
      planPrompt: DEFAULT_PROMPTS.plan,
      reasonPrompt: DEFAULT_PROMPTS.reason,
      actPrompt: DEFAULT_PROMPTS.act,
      maxSteps: 3,
      onStep: (_step, context) => {
        stepsSeen.push(context.stepNumber);
      },
      verifyTrajectory: async (trajectory) => trajectory.goal.includes("store"),
    });

    await agent.init();

    const stored = await agent.train(new MathEnvironment(), "add 3 and 4 and store");
    assertSuccessful("stored training trajectory", stored.success);

    const skipped = await agent.train(new MathEnvironment(), "multiply 2 and 9 but skip");
    assertSuccessful("unstored training trajectory", skipped.success);

    const inference = await agent.run(new MathEnvironment(), "multiply 3 and 5");
    assertSuccessful("inference trajectory", inference.success);

    const stats = agent.getStats();
    assert.equal(stats.totalTrajectories, 1);
    assert.equal(stats.successfulTrajectories, 1);
    assert.equal(stepsSeen.length > 0, true);

    console.log("example:basic passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
