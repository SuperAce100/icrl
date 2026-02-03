/**
 * Basic example of using ICRL with OpenAI.
 *
 * Run with:
 *   npx ts-node examples/basic.ts
 *
 * Make sure OPENAI_API_KEY is set in your environment.
 */

import OpenAI from "openai";
import { Agent, OpenAIProvider, OpenAIEmbedder } from "../src";
import type { Environment, StepResult } from "../src";

// Simple calculator environment
class CalculatorEnvironment implements Environment {
  private goal: string = "";
  private result: number | null = null;

  reset(goal: string): string {
    this.goal = goal;
    this.result = null;
    return `Calculator ready. Goal: ${goal}`;
  }

  step(action: string): StepResult {
    // Parse action like "calculate 2 + 2" or "add 5 3"
    const lowerAction = action.toLowerCase().trim();

    try {
      if (lowerAction.startsWith("calculate ")) {
        const expr = lowerAction.slice(10);
        // Simple eval for demo (don't do this in production!)
        this.result = Function(`"use strict"; return (${expr})`)();
        return {
          observation: `Result: ${this.result}`,
          done: true,
          success: true,
        };
      }

      if (lowerAction.startsWith("add ")) {
        const [a, b] = lowerAction.slice(4).split(/\s+/).map(Number);
        this.result = a + b;
        return {
          observation: `${a} + ${b} = ${this.result}`,
          done: true,
          success: true,
        };
      }

      if (lowerAction.startsWith("multiply ")) {
        const [a, b] = lowerAction.slice(9).split(/\s+/).map(Number);
        this.result = a * b;
        return {
          observation: `${a} × ${b} = ${this.result}`,
          done: true,
          success: true,
        };
      }

      return {
        observation: `Unknown action: ${action}. Try "calculate <expr>", "add <a> <b>", or "multiply <a> <b>"`,
        done: false,
        success: false,
      };
    } catch (error) {
      return {
        observation: `Error: ${error}`,
        done: false,
        success: false,
      };
    }
  }
}

async function main() {
  const openai = new OpenAI();

  const agent = new Agent({
    llm: new OpenAIProvider(openai, { model: "gpt-4o-mini" }),
    embedder: new OpenAIEmbedder(openai),
    dbPath: "./calculator_trajectories",
    planPrompt: `You are a calculator assistant.

Goal: {goal}

Examples of similar calculations:
{examples}

Create a simple plan to accomplish this calculation.`,
    reasonPrompt: `Goal: {goal}
Plan: {plan}

Current observation:
{observation}

Think about what calculation to perform.`,
    actPrompt: `Goal: {goal}
Plan: {plan}
Your reasoning: {reasoning}

Respond with ONLY the action. Use one of:
- calculate <expression>
- add <a> <b>
- multiply <a> <b>`,
    k: 2,
    maxSteps: 5,
    onStep: (step, context) => {
      console.log(`\n--- Step ${context.stepNumber} ---`);
      console.log(`Observation: ${step.observation}`);
      console.log(`Reasoning: ${step.reasoning.slice(0, 100)}...`);
      console.log(`Action: ${step.action}`);
    },
  });

  // Initialize the agent
  await agent.init();

  console.log("=== Training Phase ===\n");

  // Train on some calculations
  const trainingGoals = [
    "Calculate 15 + 27",
    "What is 8 times 9?",
    "Add 100 and 250",
  ];

  for (const goal of trainingGoals) {
    console.log(`\n>>> Training: ${goal}`);
    const env = new CalculatorEnvironment();
    const trajectory = await agent.train(env, goal);
    console.log(`Result: ${trajectory.success ? "✓ Success" : "✗ Failed"}`);
  }

  console.log("\n=== Inference Phase ===\n");

  // Run inference on new calculations
  const inferenceGoals = [
    "Calculate 42 + 58",
    "Multiply 7 and 11",
  ];

  for (const goal of inferenceGoals) {
    console.log(`\n>>> Inference: ${goal}`);
    const env = new CalculatorEnvironment();
    const trajectory = await agent.run(env, goal);
    console.log(`Result: ${trajectory.success ? "✓ Success" : "✗ Failed"}`);
  }

  // Print stats
  const stats = agent.getStats();
  console.log("\n=== Statistics ===");
  console.log(`Total trajectories: ${stats.totalTrajectories}`);
  console.log(`Successful: ${stats.successfulTrajectories}`);
  console.log(`Success rate: ${(stats.successRate * 100).toFixed(1)}%`);
}

main().catch(console.error);
