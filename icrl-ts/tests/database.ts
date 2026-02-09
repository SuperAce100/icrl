/**
 * Demonstrates TrajectoryDatabase + FileSystemAdapter operations.
 *
 * Run with:
 *   bun run test:database
 */

import * as assert from "node:assert/strict";
import { FileSystemAdapter, TrajectoryDatabase, type Trajectory } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DeterministicEmbedder,
} from "./_shared";

function makeTrajectory(id: string, goal: string, action: string): Trajectory {
  return {
    id,
    goal,
    plan: "Solve the goal and return the result.",
    steps: [{ observation: `Task: ${goal}`, reasoning: `Compute ${goal}`, action }],
    success: true,
    metadata: {},
  };
}

async function main(): Promise<void> {
  const dbPath = createTempDir("database");

  try {
    const adapter = new FileSystemAdapter(dbPath);
    const db = new TrajectoryDatabase(adapter, new DeterministicEmbedder());
    await db.load();

    await db.add(makeTrajectory("traj-add", "add 3 and 4", "answer:7"));
    await db.add(makeTrajectory("traj-mul", "multiply 3 and 4", "answer:12"));

    assert.equal(db.size, 2);

    const trajectoryHits = await db.search("add two numbers", 1);
    assert.equal(trajectoryHits.length, 1);
    assert.equal(trajectoryHits[0]?.id, "traj-add");

    const stepHits = await db.searchSteps("multiply values", 1);
    assert.equal(stepHits.length, 1);
    assert.equal(stepHits[0]?.trajectoryId, "traj-mul");

    await db.recordRetrieval("traj-add", true);
    const meta = db.getCurationMetadata("traj-add");
    assert.equal(meta?.timesRetrieved, 1);
    assert.equal(meta?.timesLedToSuccess, 1);

    const removed = await db.remove("traj-mul");
    assert.equal(removed, true);
    assert.equal(db.size, 1);

    const reloaded = new TrajectoryDatabase(
      new FileSystemAdapter(dbPath),
      new DeterministicEmbedder()
    );
    await reloaded.load();

    assert.equal(reloaded.size, 1);
    assert.equal(reloaded.get("traj-add")?.goal, "add 3 and 4");

    console.log("test:database passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
