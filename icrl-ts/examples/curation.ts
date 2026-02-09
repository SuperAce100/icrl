/**
 * Demonstrates curation scoring and pruning.
 *
 * Run with:
 *   bun run example:curation
 */

import * as assert from "node:assert/strict";
import {
  CurationManager,
  FileSystemAdapter,
  TrajectoryDatabase,
  type Trajectory,
} from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DeterministicEmbedder,
} from "./_shared";

function makeTrajectory(id: string, goal: string, action: string): Trajectory {
  return {
    id,
    goal,
    plan: "Solve the goal.",
    steps: [{ observation: `Task ${goal}`, reasoning: `Reason about ${goal}`, action }],
    success: true,
    metadata: {},
  };
}

async function main(): Promise<void> {
  const dbPath = createTempDir("curation");

  try {
    const db = new TrajectoryDatabase(
      new FileSystemAdapter(dbPath),
      new DeterministicEmbedder()
    );
    await db.load();

    await db.add(makeTrajectory("c-good", "add 4 and 1", "answer:5"));
    await db.add(makeTrajectory("c-bad", "multiply 4 and 1", "answer:4"));

    for (let i = 0; i < 6; i++) {
      await db.recordRetrieval("c-good", true);
      await db.recordRetrieval("c-bad", false);
    }

    const curation = new CurationManager(db, {
      threshold: 0.5,
      minRetrievals: 5,
      curateEvery: 1,
    });

    const lowUtility = curation.getLowUtilityTrajectories();
    assert.deepEqual(lowUtility, ["c-bad"]);

    const ran = await curation.maybeCurate();
    assert.equal(ran, true);
    assert.equal(db.get("c-bad"), undefined);
    assert.notEqual(db.get("c-good"), undefined);

    const scores = curation.getUtilityScores();
    assert.equal(scores.has("c-good"), true);
    assert.equal(scores.has("c-bad"), false);

    console.log("example:curation passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
