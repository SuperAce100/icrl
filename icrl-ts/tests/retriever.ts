/**
 * Demonstrates TrajectoryRetriever behavior and retrieval tracking.
 *
 * Run with:
 *   bun run test:retriever
 */

import * as assert from "node:assert/strict";
import {
  FileSystemAdapter,
  TrajectoryDatabase,
  TrajectoryRetriever,
  type Trajectory,
} from "../src";
import {
  cleanupTempDir,
  createTempDir,
  DeterministicEmbedder,
} from "./_shared";

const trajectories: Trajectory[] = [
  {
    id: "r-add",
    goal: "add 10 and 2",
    plan: "Compute sum",
    steps: [{ observation: "Need 10 + 2", reasoning: "Add numbers", action: "answer:12" }],
    success: true,
    metadata: {},
  },
  {
    id: "r-mul",
    goal: "multiply 10 and 2",
    plan: "Compute product",
    steps: [
      {
        observation: "Need 10 * 2",
        reasoning: "Multiply numbers",
        action: "answer:20",
      },
    ],
    success: true,
    metadata: {},
  },
];

async function main(): Promise<void> {
  const dbPath = createTempDir("retriever");

  try {
    const db = new TrajectoryDatabase(
      new FileSystemAdapter(dbPath),
      new DeterministicEmbedder()
    );
    await db.load();

    for (const trajectory of trajectories) {
      await db.add(trajectory);
    }

    const retriever = new TrajectoryRetriever(db, 1);

    const planExamples = await retriever.retrieveForPlan("add numbers quickly");
    assert.equal(planExamples.length, 1);
    assert.equal(planExamples[0]?.trajectoryId, "r-add");

    const stepExamples = await retriever.retrieveForStep(
      "multiply numbers",
      "Compute product",
      "Need 5 * 5"
    );
    assert.equal(stepExamples.length, 1);
    assert.equal(stepExamples[0]?.trajectoryId, "r-mul");

    const retrievedIds = retriever.getRetrievedIds().sort();
    assert.deepEqual(retrievedIds, ["r-add", "r-mul"]);

    retriever.recordEpisodeResult(true);

    assert.equal(db.getCurationMetadata("r-add")?.timesRetrieved, 1);
    assert.equal(db.getCurationMetadata("r-mul")?.timesRetrieved, 1);
    assert.equal(retriever.getRetrievedIds().length, 0);

    console.log("test:retriever passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
