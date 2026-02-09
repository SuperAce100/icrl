/**
 * Demonstrates model schemas and formatter utilities.
 *
 * Run with:
 *   bun run test:models
 */

import * as assert from "node:assert/strict";
import {
  CurationMetadataSchema,
  MessageSchema,
  StepContextSchema,
  StepExampleSchema,
  StepSchema,
  TrajectorySchema,
  formatExamples,
  formatHistory,
  stepExampleToString,
  trajectoryToExampleString,
  updateCurationUtility,
} from "../src";

async function main(): Promise<void> {
  const message = MessageSchema.parse({ role: "user", content: "hello" });
  assert.equal(message.role, "user");

  const step = StepSchema.parse({
    observation: "Need 2 + 2",
    reasoning: "Add values",
    action: "answer:4",
  });

  const stepExample = StepExampleSchema.parse({
    goal: "add 2 and 2",
    plan: "Compute sum",
    observation: step.observation,
    reasoning: step.reasoning,
    action: step.action,
    trajectoryId: "traj-1",
    stepIndex: 0,
  });

  const trajectory = TrajectorySchema.parse({
    goal: "add 2 and 2",
    plan: "Compute sum",
    steps: [step],
    success: true,
  });

  const context = StepContextSchema.parse({
    goal: trajectory.goal,
    plan: trajectory.plan,
    observation: "Current observation",
    history: trajectory.steps,
    examples: [stepExample],
  });
  assert.equal(context.examples.length, 1);

  const single = stepExampleToString(stepExample);
  assert.equal(single.includes("Observation:"), true);

  const examplesText = formatExamples([stepExample], { maxExamples: 1, maxChars: 1000 });
  assert.equal(examplesText.includes("Action:"), true);

  const historyText = formatHistory(trajectory.steps);
  assert.equal(historyText.includes("Step 1:"), true);

  const trajectoryText = trajectoryToExampleString(trajectory);
  assert.equal(trajectoryText.includes("Goal:"), true);

  const metadata = CurationMetadataSchema.parse({
    trajectoryId: "traj-1",
    createdAt: new Date(),
    timesRetrieved: 10,
    timesLedToSuccess: 8,
    validations: [],
    retrievalScore: null,
    persistenceScore: null,
    utilityScore: 1,
    isDeprecated: false,
    deprecatedAt: null,
    deprecationReason: null,
    supersededBy: null,
  });

  const updated = updateCurationUtility(metadata);
  assert.equal(updated.utilityScore > 0, true);

  console.log("test:models passed");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
