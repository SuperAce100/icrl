/**
 * Demonstrates Agent seed trajectories + batch training/inference.
 *
 * Run with:
 *   bun run example:batch
 */

import * as assert from "node:assert/strict";
import { Agent, FileSystemAdapter, type Trajectory } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DEFAULT_PROMPTS,
  DeterministicEmbedder,
  MathEnvironment,
  ScriptedMathLLM,
} from "./_shared";

async function main(): Promise<void> {
  const dbPath = createTempDir("batch");

  try {
    const seededTrajectory: Trajectory = {
      id: "seed-trajectory",
      goal: "add 1 and 1",
      plan: "Compute the sum and return it.",
      steps: [{ observation: "Solve 1 + 1", reasoning: "It is 2", action: "answer:2" }],
      success: true,
      metadata: { source: "seed" },
    };

    const agent = new Agent({
      llm: new ScriptedMathLLM(),
      embedder: new DeterministicEmbedder(),
      storage: new FileSystemAdapter(dbPath),
      planPrompt: DEFAULT_PROMPTS.plan,
      reasonPrompt: DEFAULT_PROMPTS.reason,
      actPrompt: DEFAULT_PROMPTS.act,
      seedTrajectories: [seededTrajectory],
    });

    await agent.init();
    assert.equal(agent.getDatabase().size, 1);

    const trained = await agent.trainBatch(
      () => new MathEnvironment(),
      ["add 5 and 7", "multiply 4 and 6"]
    );
    assert.equal(trained.length, 2);
    assert.equal(trained.every((trajectory) => trajectory.success), true);
    assert.equal(agent.getDatabase().size, 3);

    const beforeInference = agent.getDatabase().size;

    const inferred = await agent.runBatch(
      () => new MathEnvironment(),
      ["add 8 and 3", "multiply 3 and 7"]
    );
    assert.equal(inferred.length, 2);
    assert.equal(inferred.every((trajectory) => trajectory.success), true);
    assert.equal(agent.getDatabase().size, beforeInference);

    console.log("example:batch passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
