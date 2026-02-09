/**
 * Demonstrates direct ReActLoop usage.
 *
 * Run with:
 *   bun run example:loop
 */

import * as assert from "node:assert/strict";
import {
  FileSystemAdapter,
  ReActLoop,
  TrajectoryDatabase,
  TrajectoryRetriever,
  type Trajectory,
} from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DEFAULT_PROMPTS,
  DeterministicEmbedder,
  MathEnvironment,
  ScriptedMathLLM,
} from "./_shared";

async function main(): Promise<void> {
  const dbPath = createTempDir("loop");

  try {
    const seed: Trajectory = {
      id: "loop-seed",
      goal: "add 2 and 2",
      plan: "Compute the sum",
      steps: [{ observation: "Need 2 + 2", reasoning: "Add", action: "answer:4" }],
      success: true,
      metadata: {},
    };

    const db = new TrajectoryDatabase(
      new FileSystemAdapter(dbPath),
      new DeterministicEmbedder()
    );
    await db.load();
    await db.add(seed);

    const retriever = new TrajectoryRetriever(db, 1);

    const loop = new ReActLoop(new ScriptedMathLLM(), retriever, {
      planPrompt: DEFAULT_PROMPTS.plan,
      reasonPrompt: DEFAULT_PROMPTS.reason,
      actPrompt: DEFAULT_PROMPTS.act,
      maxSteps: 3,
    });

    const trajectory = await loop.run(new MathEnvironment(), "add 9 and 1");

    assert.equal(trajectory.success, true);
    assert.equal(trajectory.goal, "add 9 and 1");
    assert.equal(trajectory.steps.length, 1);
    assert.equal(trajectory.steps[0]?.action, "answer:10");

    console.log("example:loop passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
