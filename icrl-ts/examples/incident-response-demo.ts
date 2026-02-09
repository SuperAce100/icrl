/**
 * Incident response playbook demo (real-world use case).
 *
 * Run with:
 *   bun run example:incident
 */

import * as assert from "node:assert/strict";
import Anthropic from "@anthropic-ai/sdk";
import { Agent, AnthropicProvider, FileSystemAdapter } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  LocalHashEmbedder,
} from "./_demo_shared";
import { loadWorkspaceEnv } from "./_live_env";
import type { Environment, StepResult } from "../src";

function detectOwner(text: string): "payments" | "backend" | "data" {
  const lower = text.toLowerCase();
  if (/payment|checkout|invoice|billing/.test(lower)) return "payments";
  if (/database|replica|query|migration|storage/.test(lower)) return "data";
  return "backend";
}

class IncidentEnvironment implements Environment {
  private expectedOwner: "payments" | "backend" | "data" = "backend";

  reset(goal: string): string {
    this.expectedOwner = detectOwner(goal);
    return [
      "PRODUCTION INCIDENT",
      `Incident: ${goal}`,
      `Expected incident owner: ${this.expectedOwner}`,
      "Return structured first-response output.",
    ].join("\n");
  }

  step(action: string): StepResult {
    const lower = action.toLowerCase();

    const hasSeverity = /severity\s*:\s*(sev-1|sev-2|sev-3)/.test(lower);
    const hasOwner = new RegExp(`owner\\s*:\\s*${this.expectedOwner}`).test(lower);
    const hasFirstAction = /first_action\s*:\s*.+/i.test(action);

    const success = hasSeverity && hasOwner && hasFirstAction;

    return {
      observation: success
        ? `Incident response accepted for owner ${this.expectedOwner}.`
        : `Incident response rejected. Required: severity, owner:${this.expectedOwner}, first_action.`,
      done: true,
      success,
    };
  }
}

async function main(): Promise<void> {
  loadWorkspaceEnv();

  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("ANTHROPIC_API_KEY is not set");
  }

  const dbPath = createTempDir("incident-response-demo");

  try {
    const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

    const agent = new Agent({
      llm: new AnthropicProvider(anthropic, {
        model: process.env.ANTHROPIC_MODEL ?? "claude-sonnet-4-20250514",
        temperature: 0,
      }),
      embedder: new LocalHashEmbedder(),
      storage: new FileSystemAdapter(dbPath),
      maxSteps: 2,
      k: 2,
      planPrompt: `You are an on-call incident commander.\n\nGoal: {goal}\n\nExamples:\n{examples}\n\nCreate a short response plan.`,
      reasonPrompt: `Goal: {goal}\nPlan: {plan}\nObservation: {observation}\nHistory:\n{history}\nExamples:\n{examples}\n\nReason about severity and immediate stabilization.`,
      actPrompt: `Return exactly these lines:\nseverity: <sev-1|sev-2|sev-3>\nowner: <payments|backend|data>\nfirst_action: <immediate mitigation step>\n\nOwner hints:\n- payment/checkout/billing -> payments\n- database/storage/migration -> data\n- api/login/service timeout -> backend\n\nGoal: {goal}\nPlan: {plan}\nReasoning: {reasoning}`,
    });

    await agent.init();

    const trainGoals = [
      "Checkout requests failing with payment authorization errors for all regions.",
      "Primary database replica lag above 2 minutes causing stale reads.",
    ];

    for (const goal of trainGoals) {
      const trajectory = await agent.train(new IncidentEnvironment(), goal);
      assert.equal(trajectory.success, true, `training failed for goal: ${goal}`);
    }

    const inferenceGoal = "Public API login endpoint returning intermittent 503 timeouts.";
    const inference = await agent.run(new IncidentEnvironment(), inferenceGoal);
    assert.equal(inference.success, true, "incident inference failed");

    console.log(`Stored trajectories: ${agent.getStats().totalTrajectories}`);
    console.log("example:incident passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
