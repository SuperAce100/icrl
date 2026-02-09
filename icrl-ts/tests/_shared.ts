import * as assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { Embedder, Environment, LLMProvider, Message, StepResult } from "../src";

export const DEFAULT_PROMPTS = {
  plan: `Goal: {goal}\n\nExamples:\n{examples}\n\nCreate a plan in one sentence.`,
  reason: `Goal: {goal}\nPlan: {plan}\nHistory:\n{history}\nObservation: {observation}\nExamples:\n{examples}\n\nThink step by step.`,
  act: `Goal: {goal}\nPlan: {plan}\nReasoning: {reasoning}\nHistory:\n{history}\nExamples:\n{examples}\n\nRespond with ONLY the action in the format answer:<number>.`,
} as const;

export function createTempDir(prefix: string): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), `icrl-ts-${prefix}-`));
}

export function cleanupTempDir(dir: string): void {
  fs.rmSync(dir, { recursive: true, force: true });
}

export function parseMathGoal(goal: string): number {
  const numbers = (goal.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
  if (numbers.length < 2) return 0;

  if (/multiply|times|product/i.test(goal)) {
    return numbers[0]! * numbers[1]!;
  }

  return numbers[0]! + numbers[1]!;
}

function extractGoal(prompt: string): string {
  const match = prompt.match(/Goal:\s*([^\n]+)/i);
  return match?.[1]?.trim() ?? "";
}

export class ScriptedMathLLM implements LLMProvider {
  async complete(messages: Message[]): Promise<string> {
    const prompt = messages.at(-1)?.content ?? "";

    if (/Respond with ONLY the action|Next action/i.test(prompt)) {
      const goal = extractGoal(prompt);
      return `answer:${parseMathGoal(goal)}`;
    }

    if (/Think step by step|Reasoning|Observation/i.test(prompt)) {
      return "Compute the answer from the goal and return answer:<number>.";
    }

    return "Calculate the requested value and provide answer:<number>.";
  }
}

function normalize(vec: number[]): number[] {
  const norm = Math.sqrt(vec.reduce((acc, value) => acc + value * value, 0));
  if (norm === 0) return vec;
  return vec.map((value) => value / norm);
}

function textToVector(text: string): number[] {
  const lower = text.toLowerCase();
  const vector = [
    /add|sum|plus|calculate/.test(lower) ? 1 : 0,
    /multiply|times|product/.test(lower) ? 1 : 0,
    /correct|success|done/.test(lower) ? 1 : 0,
    text.length % 17,
    text.split(/\s+/).length % 23,
    [...text].reduce((acc, char) => acc + char.charCodeAt(0), 0) % 29,
  ];
  return normalize(vector);
}

export class DeterministicEmbedder implements Embedder {
  readonly dimension = 6;

  async embed(texts: string[]): Promise<number[][]> {
    return texts.map((text) => textToVector(text));
  }

  async embedSingle(text: string): Promise<number[]> {
    return textToVector(text);
  }
}

export class MathEnvironment implements Environment {
  private expected = 0;

  reset(goal: string): string {
    this.expected = parseMathGoal(goal);
    return `Solve this task: ${goal}`;
  }

  step(action: string): StepResult {
    const match = action.match(/answer:\s*(-?\d+(?:\.\d+)?)/i);
    const got = match ? Number(match[1]) : Number.NaN;
    const success = Number.isFinite(got) && got === this.expected;

    return {
      observation: success
        ? `Correct: ${got}`
        : `Incorrect action '${action}'. Expected answer:${this.expected}.`,
      done: true,
      success,
    };
  }
}

export function assertSuccessful(label: string, success: boolean): void {
  assert.equal(success, true, `${label} was expected to succeed`);
}
