/**
 * Zod schemas and TypeScript types for ICRL trajectories and messages.
 * Equivalent to Python's Pydantic models.
 */

import { z } from "zod";
import { v4 as uuidv4 } from "uuid";

// ============================================================================
// Message
// ============================================================================

export const MessageSchema = z.object({
  role: z.string(),
  content: z.string(),
});

export type Message = z.infer<typeof MessageSchema>;

// ============================================================================
// Step
// ============================================================================

export const StepSchema = z.object({
  observation: z.string(),
  reasoning: z.string(),
  action: z.string(),
});

export type Step = z.infer<typeof StepSchema>;

// ============================================================================
// StepExample
// ============================================================================

export const StepExampleSchema = z.object({
  goal: z.string(),
  plan: z.string(),
  observation: z.string(),
  reasoning: z.string(),
  action: z.string(),
  trajectoryId: z.string(),
  stepIndex: z.number(),
});

export type StepExample = z.infer<typeof StepExampleSchema>;

/**
 * Format a step example as an in-context example string.
 */
export function stepExampleToString(example: StepExample): string {
  // Truncate observation aggressively (full obs can be 8000+ chars)
  let obs = example.observation.replace(/\n/g, " ");
  if (obs.length > 500) {
    obs = obs.slice(0, 500) + "...";
  }

  let reasoning = example.reasoning.replace(/\n/g, " ").trim();
  if (reasoning.length > 300) {
    reasoning = reasoning.slice(0, 300) + "...";
  }

  let action = example.action.replace(/\n/g, " ").trim();
  if (action.length > 250) {
    action = action.slice(0, 250) + "...";
  }

  return `Observation: ${obs}\nReasoning: ${reasoning}\nAction: ${action}`;
}

// ============================================================================
// Trajectory
// ============================================================================

export const TrajectorySchema = z.object({
  id: z.string().default(() => uuidv4()),
  goal: z.string(),
  plan: z.string(),
  steps: z.array(StepSchema),
  success: z.boolean(),
  metadata: z.record(z.any()).default({}),
});

export type Trajectory = z.infer<typeof TrajectorySchema>;

/**
 * Convert trajectory to a string format suitable for in-context examples.
 */
export function trajectoryToExampleString(trajectory: Trajectory): string {
  const lines: string[] = [
    `Goal: ${trajectory.goal}`,
    `Plan: ${trajectory.plan}`,
    "Steps:",
  ];

  trajectory.steps.forEach((step, i) => {
    lines.push(`  Step ${i + 1}:`);
    lines.push(`    Observation: ${step.observation}`);
    lines.push(`    Reasoning: ${step.reasoning}`);
    lines.push(`    Action: ${step.action}`);
  });

  lines.push(`Success: ${trajectory.success}`);
  return lines.join("\n");
}

// ============================================================================
// StepContext
// ============================================================================

export const StepContextSchema = z.object({
  goal: z.string(),
  plan: z.string(),
  observation: z.string(),
  reasoning: z.string().default(""),
  history: z.array(StepSchema).default([]),
  examples: z.array(StepExampleSchema).default([]),
});

export type StepContext = z.infer<typeof StepContextSchema>;

/**
 * Format retrieved step examples as a string.
 */
export function formatExamples(
  examples: StepExample[],
  options: { maxExamples?: number; maxChars?: number } = {}
): string {
  const maxExamples = options.maxExamples ?? 3;
  const maxChars = options.maxChars ?? 4000;

  if (!examples.length || maxExamples <= 0 || maxChars <= 0) {
    return "No examples available.";
  }

  const parts: string[] = [];
  let total = 0;
  let omitted = 0;

  const considered = Math.min(examples.length, maxExamples);
  for (let i = 0; i < considered; i++) {
    const ex = examples[i]!;
    const s = stepExampleToString(ex);
    if (total + s.length > maxChars) {
      omitted++;
      continue;
    }
    parts.push(s);
    total += s.length;
  }

  omitted += Math.max(0, examples.length - considered);
  if (omitted > 0) {
    parts.push(`[${omitted} example(s) omitted to fit context budget]`);
  }

  return parts.join("\n\n---\n\n");
}

/**
 * Format step history as a string (truncated for context window).
 */
export function formatHistory(history: Step[]): string {
  if (!history.length) {
    return "No previous steps.";
  }

  const lines: string[] = [];
  // Only show last 5 steps to keep context manageable
  const recent = history.length > 5 ? history.slice(-5) : history;
  const startIdx = history.length - recent.length + 1;

  if (history.length > 5) {
    lines.push(`[${history.length - 5} earlier steps omitted]`);
  }

  recent.forEach((step, i) => {
    // Truncate observation in history
    let obs = step.observation.replace(/\n/g, " ");
    if (obs.length > 300) {
      obs = obs.slice(0, 300) + "...";
    }

    let action = step.action.replace(/\n/g, " ").trim();
    if (action.length > 200) {
      action = action.slice(0, 200) + "...";
    }

    lines.push(`Step ${startIdx + i}: ${action} -> ${obs}`);
  });

  return lines.join("\n");
}

// ============================================================================
// CurationMetadata
// ============================================================================

export const DeferredValidationSchema = z.object({
  validatedAt: z.date().default(() => new Date()),
  validatorType: z.string(),
  score: z.number().min(0).max(1),
  reason: z.string().default(""),
  details: z.record(z.any()).default({}),
});

export type DeferredValidation = z.infer<typeof DeferredValidationSchema>;

export const CurationMetadataSchema = z.object({
  trajectoryId: z.string(),
  createdAt: z.date().default(() => new Date()),

  // Retrieval-based signals
  timesRetrieved: z.number().default(0),
  timesLedToSuccess: z.number().default(0),

  // Deferred validation history
  validations: z.array(DeferredValidationSchema).default([]),

  // Computed scores
  retrievalScore: z.number().nullable().default(null),
  persistenceScore: z.number().nullable().default(null),
  utilityScore: z.number().default(1.0),

  // Status
  isDeprecated: z.boolean().default(false),
  deprecatedAt: z.date().nullable().default(null),
  deprecationReason: z.string().nullable().default(null),
  supersededBy: z.string().nullable().default(null),
});

export type CurationMetadata = z.infer<typeof CurationMetadataSchema>;

/**
 * Update utility score based on all available signals.
 */
export function updateCurationUtility(meta: CurationMetadata): CurationMetadata {
  const scores: number[] = [];
  const weights: number[] = [];

  // Signal 1: Retrieval success rate (if enough data)
  if (meta.timesRetrieved >= 3) {
    meta.retrievalScore = meta.timesLedToSuccess / meta.timesRetrieved;
    scores.push(meta.retrievalScore);
    weights.push(1.0);
  }

  // Signal 2: Persistence score (if validated)
  if (meta.persistenceScore !== null) {
    scores.push(meta.persistenceScore);
    weights.push(2.0); // Weight persistence more heavily
  }

  if (scores.length > 0) {
    const weightedSum = scores.reduce((acc, s, i) => acc + s * weights[i]!, 0);
    const totalWeight = weights.reduce((acc, w) => acc + w, 0);
    meta.utilityScore = weightedSum / totalWeight;
  } else {
    // No signals yet - stay optimistic
    meta.utilityScore = 1.0;
  }

  return meta;
}
