/**
 * Customer support triage demo (real-world use case).
 *
 * Run with:
 *   bun run example:support
 */

import * as assert from "node:assert/strict";
import OpenAI from "openai";
import { Agent, FileSystemAdapter, OpenAIProvider } from "../src";
import {
  cleanupTempDir,
  createTempDir,
  LocalHashEmbedder,
} from "./_demo_shared";
import { loadWorkspaceEnv } from "./_live_env";
import type { Environment, StepResult } from "../src";

function detectTeam(text: string): "billing" | "shipping" | "technical" {
  const lower = text.toLowerCase();
  if (/charge|invoice|refund|payment|billing/.test(lower)) return "billing";
  if (/delivery|tracking|shipment|package|ship/.test(lower)) return "shipping";
  return "technical";
}

class SupportTicketEnvironment implements Environment {
  private goal = "";
  private expectedTeam: "billing" | "shipping" | "technical" = "technical";

  reset(goal: string): string {
    this.goal = goal;
    this.expectedTeam = detectTeam(goal);
    return [
      "INBOX TICKET",
      `Customer issue: ${goal}`,
      `Expected routing team: ${this.expectedTeam}`,
      "Return a structured triage action.",
    ].join("\n");
  }

  step(action: string): StepResult {
    const lower = action.toLowerCase();
    const hasPriority = /priority\s*:\s*(low|medium|high)/.test(lower);
    const hasTeam = new RegExp(`team\\s*:\\s*${this.expectedTeam}`).test(lower);
    const replyMatch = action.match(/reply\s*:\s*([\s\S]+)/i);
    const replyLength = replyMatch?.[1]?.trim().length ?? 0;
    const hasReply = replyLength >= 40;

    const success = hasPriority && hasTeam && hasReply;

    const observation = success
      ? `Triage accepted for ${this.expectedTeam} team.`
      : `Triage rejected. Requirements: priority, team:${this.expectedTeam}, reply >= 40 chars.`;

    return {
      observation,
      done: true,
      success,
    };
  }
}

async function main(): Promise<void> {
  loadWorkspaceEnv();

  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is not set");
  }

  const dbPath = createTempDir("support-triage-demo");

  try {
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

    const agent = new Agent({
      llm: new OpenAIProvider(openai, { model: "gpt-4o-mini", temperature: 0.2 }),
      embedder: new LocalHashEmbedder(),
      storage: new FileSystemAdapter(dbPath),
      maxSteps: 2,
      k: 2,
      planPrompt: `You are a support operations assistant.\n\nGoal: {goal}\n\nExamples:\n{examples}\n\nCreate a short triage plan.`,
      reasonPrompt: `Goal: {goal}\nPlan: {plan}\nObservation: {observation}\nHistory:\n{history}\nExamples:\n{examples}\n\nReason about the most appropriate routing and tone for a customer reply.`,
      actPrompt: `Return exactly these fields:\npriority: <low|medium|high>\nteam: <billing|shipping|technical>\nreply: <empathetic customer-facing response>\n\nRouting hints:\n- billing/payment/refund -> billing\n- tracking/delivery/shipment -> shipping\n- app bug/login/technical failure -> technical\n\nGoal: {goal}\nPlan: {plan}\nReasoning: {reasoning}`,
    });

    await agent.init();

    const trainingGoals = [
      "Customer was charged twice and wants a refund for invoice #4421.",
      "Package tracking has not updated for 5 days after dispatch.",
    ];

    for (const goal of trainingGoals) {
      const trajectory = await agent.train(new SupportTicketEnvironment(), goal);
      assert.equal(trajectory.success, true, `training failed for goal: ${goal}`);
    }

    const inferenceGoal = "User cannot log in after password reset and keeps seeing a timeout.";
    const inference = await agent.run(new SupportTicketEnvironment(), inferenceGoal);
    assert.equal(inference.success, true, "inference triage failed");

    const stats = agent.getStats();
    console.log(`Stored trajectories: ${stats.totalTrajectories}`);
    console.log("example:support passed");
  } finally {
    cleanupTempDir(dbPath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
