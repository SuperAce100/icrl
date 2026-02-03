"use server";

/**
 * Server actions for the ICRL demo.
 *
 * This uses the icrl library with Convex storage and Anthropic Vertex.
 */

import { ConvexHttpClient } from "convex/browser";
import { api } from "../../convex/_generated/api";
import type { Id } from "../../convex/_generated/dataModel";
import {
  isAnthropicVertexConfigured,
  getConfigStatus,
  generateCompletion,
} from "./anthropic-vertex";
import { formatExamples as icrlFormatExamples, type StepExample } from "../../../src/models";

// Convex client for server-side use
function getConvexClient(): ConvexHttpClient {
  const url = process.env.NEXT_PUBLIC_CONVEX_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_CONVEX_URL is not set");
  }
  return new ConvexHttpClient(url);
}

// Default persona prompt (configurable by user)
const DEFAULT_PERSONA_PROMPT = `You are a helpful, knowledgeable assistant. You provide clear, accurate, and thoughtful responses.

Your responses should be:
- Informative and well-structured
- Friendly but professional in tone
- Concise yet comprehensive`;

// Fixed training instructions (always appended for training mode)
const TRAINING_INSTRUCTIONS = `
---
TRAINING MODE INSTRUCTIONS:

You will be given a question. Generate TWO different answers:
- Answer A: A high-quality, detailed, helpful answer
- Answer B: A different but also reasonable answer (could be shorter, different perspective, or alternative approach)

Both answers should be valid, but they should be noticeably different from each other.

Here are examples of good answers from previous training:
{examples}

Respond in this exact JSON format:
{
  "answerA": "Your first answer here",
  "answerB": "Your second answer here"
}`;

export interface Example {
  question: string;
  chosenAnswer: string;
}

export interface GeneratedAnswers {
  answerA: string;
  answerB: string;
}

/**
 * Convert legacy examples to icrl StepExample format.
 *
 * This adapts the simpler Q&A example format to the trajectory-based
 * StepExample format used by the icrl library.
 */
function exampleToStepExample(ex: Example, index: number): StepExample {
  return {
    goal: ex.question,
    plan: "Answer the question helpfully and accurately.",
    observation: `User asked: ${ex.question}`,
    reasoning: "I should provide a helpful, accurate response.",
    action: ex.chosenAnswer,
    trajectoryId: `example-${index}`,
    stepIndex: 0,
  };
}

/**
 * Format examples for inclusion in the prompt using icrl's formatting.
 */
function formatExamplesForPrompt(examples: Example[]): string {
  if (examples.length === 0) {
    return "No similar examples available.";
  }

  // Convert to StepExample format and use icrl's formatter
  const stepExamples = examples.map(exampleToStepExample);
  return icrlFormatExamples(stepExamples, {
    maxExamples: 5,
    maxChars: 3000,
  });
}

/**
 * Search for similar examples using vector similarity.
 *
 * Uses the embeddings table in Convex for semantic search.
 * Also increments the retrieval count for the fetched examples.
 */
export async function searchSimilarExamples(
  databaseId: string,
  query: string,
  k: number = 3
): Promise<Example[]> {
  // For now, fall back to fetching recent examples
  // Full vector search would require embedding the query
  const client = getConvexClient();

  try {
    const examples = await client.query(api.databases.getExamples, {
      databaseId: databaseId as Id<"databases">,
      limit: k,
    });

    // Increment retrieval count for fetched examples
    if (examples.length > 0) {
      const exampleIds = examples.map((ex) => ex._id);
      await client.mutation(api.examples.incrementRetrievalCount, {
        ids: exampleIds,
      });
    }

    return examples.map((ex) => ({
      question: ex.question,
      chosenAnswer: ex.chosenAnswer,
    }));
  } catch (error) {
    console.error("Error fetching examples:", error);
    return [];
  }
}

/**
 * Generate two answer options using Anthropic Vertex and icrl formatting.
 */
export async function generateAnswers(
  question: string,
  examples: Example[],
  personaPrompt?: string
): Promise<GeneratedAnswers> {
  // Use icrl's formatting for examples
  const examplesText = formatExamplesForPrompt(examples);

  // Combine persona prompt with training instructions
  const persona = personaPrompt || DEFAULT_PERSONA_PROMPT;
  const trainingInstructions = TRAINING_INSTRUCTIONS.replace("{examples}", examplesText);
  const prompt = `${persona}\n${trainingInstructions}`;

  // Check if API is configured
  if (!isAnthropicVertexConfigured()) {
    throw new Error("Anthropic Vertex not configured. Please set GOOGLE_CREDENTIALS_JSON.");
  }

  const response = await generateCompletion({
    messages: [{ role: "user", content: `Question: ${question}` }],
    systemPrompt: prompt,
    model: "claude-opus-4-5",
    temperature: 0.8,
    maxTokens: 2000,
  });

  // Parse JSON response
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const parsed = JSON.parse(jsonMatch[0]);
    if (!parsed.answerA || !parsed.answerB) {
      throw new Error("Failed to parse answer response: missing answerA or answerB");
    }
    return {
      answerA: parsed.answerA,
      answerB: parsed.answerB,
    };
  }

  throw new Error("Failed to parse JSON response from model");
}

/**
 * Store a training example as a trajectory in the icrl format.
 *
 * This converts the simple Q&A example into a trajectory that can be
 * used by the icrl library's retrieval and curation systems.
 */
export async function storeTrainingExample(
  databaseId: string,
  question: string,
  chosenAnswer: string,
  rejectedAnswer?: string
): Promise<void> {
  const client = getConvexClient();

  // Store in the examples table (backward compatible)
  await client.mutation(api.databases.addExample, {
    databaseId: databaseId as Id<"databases">,
    question,
    chosenAnswer,
    rejectedAnswer,
    isCustom: false,
  });

  // Also store as a trajectory for icrl library integration
  // Note: For full icrl integration, we would also:
  // 1. Generate embeddings for the trajectory
  // 2. Store them in the embeddings table
  // 3. Use the TrajectoryDatabase class
  //
  // This is left as future work since embedding requires an
  // embedding model (e.g., OpenAI text-embedding-3-small)
}

/**
 * Check if the API is properly configured.
 */
export async function checkApiStatus(): Promise<{
  configured: boolean;
  message: string;
}> {
  return getConfigStatus();
}

// Curriculum learning prompt for generating suggestions
const SUGGESTION_GENERATION_PROMPT = `You are a curriculum designer for an AI training system. Your goal is to suggest prompts that DRAMATICALLY EXPAND the training coverage into completely new territory.

CRITICAL RULES:
- NEVER suggest duplicates or rephrasings of existing examples
- NEVER suggest prompts that are semantically similar to what's already covered
- Each suggestion must explore a COMPLETELY DIFFERENT domain/topic
- Think EXPANSIVELY - push into entirely new subject areas, industries, contexts
- The goal is maximum diversity, not incremental improvement

Given the existing training examples below, generate 5 COMPLETELY NOVEL prompts that:
1. Explore ENTIRELY NEW topics - not variations of existing ones
2. Cover DIFFERENT DOMAINS (tech, arts, science, business, personal, social, creative, analytical, etc.)
3. Vary in TYPE (factual, opinion, how-to, comparison, creative, hypothetical, troubleshooting, planning)
4. Vary in COMPLEXITY (some simple, some requiring deep thought)
5. Would MASSIVELY expand the sphere of covered topics - think of the example space as a map, and you're exploring uncharted regions

EXISTING EXAMPLES (DO NOT repeat or rephrase ANY of these):
{examples_summary}

BE BOLD! Suggest prompts about topics that seem completely unrelated to what exists. The more diverse, the better. Cover gaps like: different industries, different life situations, different types of tasks, different levels of abstraction.

Respond in this exact JSON format:
{
  "suggestions": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"],
  "reasoning": "Brief explanation of what new territories these prompts explore"
}`;

// YOLO mode prompt for generating a novel prompt (answers generated separately with retrieved examples)
const YOLO_PROMPT_GENERATION = `You are a curriculum designer for an AI training system.

Your task: Generate a SINGLE prompt that explores COMPLETELY NEW TERRITORY not covered by existing examples.

CRITICAL RULES:
- NEVER generate a duplicate or rephrasing of any existing example
- NEVER generate something semantically similar to what's already covered
- The prompt MUST explore a COMPLETELY DIFFERENT domain or topic
- Think EXPANSIVELY - venture into entirely new subject areas
- Be BOLD and creative - the more different from existing examples, the better

Based on the existing examples below, create a prompt that:
- Explores an ENTIRELY NEW topic or domain (not a variation of existing ones)
- Is in a DIFFERENT category (if examples are about productivity, try science, art, relationships, etc.)
- Would SIGNIFICANTLY expand the training coverage into uncharted territory
- Is clear and specific enough to generate meaningful responses

EXISTING EXAMPLES (DO NOT duplicate, rephrase, or create variations of ANY of these):
{examples_summary}

Think of the example space as a map. Your job is to explore regions that are FAR from existing examples. Consider: different industries, life contexts, problem types, domains of knowledge, types of tasks.

Respond in this exact JSON format:
{
  "prompt": "Your completely novel prompt here",
  "reasoning": "What new territory this explores that's different from all existing examples"
}`;

// YOLO mode prompt for generating MULTIPLE novel prompts at once (more efficient)
const YOLO_BATCH_PROMPT_GENERATION = `You are a curriculum designer for an AI training system.

Your task: Generate {count} COMPLETELY NOVEL prompts that explore NEW TERRITORY not covered by existing examples.

CRITICAL RULES:
- NEVER generate duplicates or rephrasings of any existing example
- NEVER generate something semantically similar to what's already covered
- Each prompt MUST explore a COMPLETELY DIFFERENT domain or topic
- The {count} prompts should ALL be different from EACH OTHER too
- Think EXPANSIVELY - venture into entirely new subject areas
- Be BOLD and creative - maximum diversity is the goal

EXISTING EXAMPLES (DO NOT duplicate, rephrase, or create variations of ANY of these):
{examples_summary}

Generate {count} prompts that:
- Each explores an ENTIRELY NEW topic or domain
- Cover DIFFERENT categories from each other (mix of tech, science, arts, business, personal, health, creativity, etc.)
- Would MASSIVELY expand the training coverage into uncharted territory
- Are clear and specific enough to generate meaningful responses

Think of the example space as a map. Generate prompts that explore {count} DIFFERENT regions, all FAR from existing examples AND far from each other.

Respond in this exact JSON format:
{
  "prompts": ["prompt1", "prompt2", "prompt3", ...],
  "reasoning": "Brief explanation of the diverse territories covered"
}`;

/**
 * Create a summary of existing examples for curriculum learning.
 * Includes all examples to help the AI avoid duplicates and identify gaps.
 */
function summarizeExamplesForCurriculum(examples: Example[]): string {
  if (examples.length === 0) {
    return "No existing examples yet. This is the first training session - generate diverse foundational prompts across many different domains (tech, personal development, science, arts, business, relationships, health, creativity, etc.)";
  }

  // Include more examples to help avoid duplicates
  const maxExamples = Math.min(examples.length, 30);
  const summary = examples
    .slice(0, maxExamples)
    .map(
      (ex, i) => `${i + 1}. "${ex.question.slice(0, 120)}${ex.question.length > 120 ? "..." : ""}"`
    )
    .join("\n");

  // Add explicit instruction about what's covered
  const coverageNote =
    examples.length > maxExamples
      ? `\n\n(Showing ${maxExamples} of ${examples.length} total examples. There are more examples not shown - be extra careful to explore NEW territory.)`
      : "";

  return `ALREADY COVERED (${examples.length} examples - DO NOT duplicate or rephrase any of these):\n${summary}${coverageNote}\n\nYou MUST suggest prompts about topics NOT listed above.`;
}

/**
 * Create a hash of example questions for cache invalidation.
 */
function hashExamples(examples: Example[]): string {
  // Simple hash based on questions - just use first 5 chars of each recent question
  return examples
    .slice(0, 10)
    .map((ex) => ex.question.slice(0, 5))
    .join("");
}

export interface SuggestionsResult {
  suggestions: string[];
  fromCache: boolean;
}

/**
 * Generate AI-powered prompt suggestions using curriculum learning.
 * Uses caching to avoid regenerating when examples haven't changed.
 */
export async function generateSuggestions(
  databaseId: string,
  forceRefresh: boolean = false
): Promise<SuggestionsResult> {
  const client = getConvexClient();

  try {
    // Get all examples for the database
    const examples = await client.query(api.suggestions.getAllExamples, {
      databaseId: databaseId as Id<"databases">,
    });

    const exampleCount = examples.length;

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cached = await client.query(api.suggestions.getCached, {
        databaseId: databaseId as Id<"databases">,
        currentExampleCount: exampleCount,
      });

      if (cached && cached.length > 0) {
        return { suggestions: cached, fromCache: true };
      }
    }

    // Generate new suggestions using Haiku
    const suggestions = await generateSuggestionsWithHaiku(examples);

    // Cache the results
    await client.mutation(api.suggestions.setCache, {
      databaseId: databaseId as Id<"databases">,
      suggestions,
      exampleCount,
      exampleHash: hashExamples(examples),
    });

    return { suggestions, fromCache: false };
  } catch (error) {
    console.error("Error generating suggestions:", error);
    throw error;
  }
}

/**
 * Generate suggestions using Claude Haiku.
 */
async function generateSuggestionsWithHaiku(examples: Example[]): Promise<string[]> {
  // Check if API is configured
  if (!isAnthropicVertexConfigured()) {
    throw new Error("Anthropic Vertex not configured. Please set GOOGLE_CREDENTIALS_JSON.");
  }

  const examplesSummary = summarizeExamplesForCurriculum(examples);
  const prompt = SUGGESTION_GENERATION_PROMPT.replace("{examples_summary}", examplesSummary);

  const response = await generateCompletion({
    messages: [{ role: "user", content: "Generate 5 diverse prompt suggestions for training." }],
    systemPrompt: prompt,
    model: "claude-haiku-4-5",
    temperature: 0.9, // Higher temperature for more diverse suggestions
    maxTokens: 1000,
  });

  // Parse JSON response
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const parsed = JSON.parse(jsonMatch[0]);
    if (Array.isArray(parsed.suggestions) && parsed.suggestions.length > 0) {
      return parsed.suggestions.slice(0, 5);
    }
  }

  throw new Error("Failed to parse suggestions response from model");
}

export interface YoloRoundResult {
  prompt: string;
  answerA: string;
  answerB: string;
  retrievedExamples: Example[];
}

/**
 * Generate a complete YOLO round: prompt + two answer options.
 * Uses curriculum learning to generate novel prompts that expand coverage.
 * Then retrieves similar examples and uses them to generate contextual answers.
 */
export async function generateYoloRound(
  databaseId: string,
  systemPrompt?: string
): Promise<YoloRoundResult> {
  const client = getConvexClient();

  try {
    // Get all examples for curriculum analysis
    const allExamples = await client.query(api.suggestions.getAllExamples, {
      databaseId: databaseId as Id<"databases">,
    });

    // Step 1: Generate a novel prompt using curriculum learning
    const generatedPrompt = await generateYoloPromptWithHaiku(allExamples);

    // Step 2: Retrieve similar examples based on the generated prompt
    const retrievedExamples = await searchSimilarExamples(databaseId, generatedPrompt, 3);

    // Step 3: Generate answers using the retrieved examples (like regular flow)
    const { answerA, answerB } = await generateAnswers(
      generatedPrompt,
      retrievedExamples,
      systemPrompt
    );

    return {
      prompt: generatedPrompt,
      answerA,
      answerB,
      retrievedExamples,
    };
  } catch (error) {
    console.error("Error generating YOLO round:", error);
    throw error;
  }
}

/**
 * Generate just the prompt for YOLO mode using Claude Haiku.
 * Answers are generated separately using retrieved examples.
 */
async function generateYoloPromptWithHaiku(examples: Example[]): Promise<string> {
  // Check if API is configured
  if (!isAnthropicVertexConfigured()) {
    throw new Error("Anthropic Vertex not configured. Please set GOOGLE_CREDENTIALS_JSON.");
  }

  const examplesSummary = summarizeExamplesForCurriculum(examples);
  const prompt = YOLO_PROMPT_GENERATION.replace("{examples_summary}", examplesSummary);

  const response = await generateCompletion({
    messages: [{ role: "user", content: "Generate a novel prompt for training." }],
    systemPrompt: prompt,
    model: "claude-haiku-4-5",
    temperature: 0.9, // Higher temperature for diverse generation
    maxTokens: 500,
  });

  // Parse JSON response
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const parsed = JSON.parse(jsonMatch[0]);
    if (parsed.prompt) {
      return parsed.prompt;
    }
  }

  throw new Error("Failed to parse YOLO prompt response from model");
}

/**
 * Generate multiple prompts at once using Claude Haiku.
 * More efficient than generating one at a time.
 */
async function generateMultipleYoloPromptsWithHaiku(
  examples: Example[],
  count: number
): Promise<string[]> {
  // Check if API is configured
  if (!isAnthropicVertexConfigured()) {
    throw new Error("Anthropic Vertex not configured. Please set GOOGLE_CREDENTIALS_JSON.");
  }

  const examplesSummary = summarizeExamplesForCurriculum(examples);
  const prompt = YOLO_BATCH_PROMPT_GENERATION.replace(/{count}/g, count.toString()).replace(
    "{examples_summary}",
    examplesSummary
  );

  const response = await generateCompletion({
    messages: [{ role: "user", content: `Generate ${count} novel prompts for training.` }],
    systemPrompt: prompt,
    model: "claude-haiku-4-5",
    temperature: 0.9,
    maxTokens: 1500,
  });

  // Parse JSON response
  const jsonMatch = response.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const parsed = JSON.parse(jsonMatch[0]);
    if (Array.isArray(parsed.prompts) && parsed.prompts.length > 0) {
      return parsed.prompts.slice(0, count);
    }
  }

  throw new Error("Failed to parse batch prompts response from model");
}

/**
 * Generate a single YOLO round from a pre-generated prompt.
 * This allows parallelization of answer generation.
 */
async function generateYoloRoundFromPrompt(
  databaseId: string,
  prompt: string,
  systemPrompt?: string
): Promise<YoloRoundResult> {
  // Retrieve similar examples based on the prompt
  const retrievedExamples = await searchSimilarExamples(databaseId, prompt, 3);

  // Generate answers using the retrieved examples
  const { answerA, answerB } = await generateAnswers(prompt, retrievedExamples, systemPrompt);

  return {
    prompt,
    answerA,
    answerB,
    retrievedExamples,
  };
}

/**
 * Generate multiple YOLO rounds in parallel.
 * This is much faster than generating them sequentially.
 *
 * 1. First generates N prompts in a single API call (efficient)
 * 2. Then parallelizes answer generation for all prompts
 */
export async function generateYoloRoundsParallel(
  databaseId: string,
  count: number,
  systemPrompt?: string
): Promise<YoloRoundResult[]> {
  const client = getConvexClient();

  // Get all examples for curriculum analysis (once)
  const allExamples = await client.query(api.suggestions.getAllExamples, {
    databaseId: databaseId as Id<"databases">,
  });

  // Step 1: Generate all prompts in a single API call
  const prompts = await generateMultipleYoloPromptsWithHaiku(allExamples, count);

  // Step 2: Generate answers for all prompts in parallel
  const roundPromises = prompts.map((prompt) =>
    generateYoloRoundFromPrompt(databaseId, prompt, systemPrompt)
  );

  // Wait for all rounds to complete
  const results = await Promise.all(roundPromises);

  return results;
}

/**
 * Invalidate the suggestion cache for a database.
 */
export async function invalidateSuggestionCache(databaseId: string): Promise<void> {
  const client = getConvexClient();
  await client.mutation(api.suggestions.invalidateCache, {
    databaseId: databaseId as Id<"databases">,
  });
}
