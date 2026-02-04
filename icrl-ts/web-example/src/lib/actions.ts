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
const SUGGESTION_GENERATION_PROMPT = `You are a curriculum designer for an AI training system. Your goal is to suggest prompts that expand training coverage into new territory while maintaining stylistic consistency.

STYLE MATCHING (CRITICAL):
- Study the TONE of existing examples (formal/casual, technical/conversational, etc.) and MATCH IT
- Study the LENGTH of existing examples and generate prompts of SIMILAR LENGTH
- Study the STRUCTURE of existing examples (questions, requests, scenarios) and FOLLOW IT
- The new prompts should feel like they belong in the same dataset

CONTENT RULES:
- NEVER suggest duplicates or rephrasings of existing examples
- Each suggestion must explore DIFFERENT subject matter/material
- The TOPICS should be new, but the STYLE should be familiar
- Think of it as: same voice, different subjects

Given the existing training examples below, generate 5 prompts that:
1. MATCH the tone, style, and approximate length of existing examples
2. Explore DIFFERENT topics/material - not variations of existing ones
3. Cover different domains (tech, arts, science, business, personal, creative, etc.)
4. Vary in type (factual, opinion, how-to, comparison, creative, hypothetical)
5. Would expand topic coverage while feeling stylistically consistent

EXISTING EXAMPLES (match their style, avoid their topics):
{examples_summary}

Generate prompts that a user would believe came from the same person who wrote the existing examples, just asking about different subjects.

Respond in this exact JSON format:
{
  "suggestions": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"],
  "reasoning": "Brief explanation of style matched and new topics explored"
}`;

// YOLO mode prompt for generating a novel prompt (answers generated separately with retrieved examples)
const YOLO_PROMPT_GENERATION = `You are a curriculum designer for an AI training system.

Your task: Generate a SINGLE prompt that explores NEW subject matter while matching the style of existing examples.

STYLE MATCHING (CRITICAL):
- Study the TONE of existing examples (formal/casual, technical/conversational) and MATCH IT EXACTLY
- Study the LENGTH of existing examples and generate a prompt of SIMILAR LENGTH
- Study the STRUCTURE (questions, requests, scenarios) and FOLLOW THE SAME PATTERN
- The prompt should feel like it belongs in the same dataset - same voice, different subject

CONTENT RULES:
- NEVER generate a duplicate or rephrasing of any existing example
- The TOPIC must be different, but the STYLE must be the same
- Explore new subject matter while maintaining stylistic consistency

Based on the existing examples below, create a prompt that:
- MATCHES the tone, style, and length of the existing examples
- Explores a DIFFERENT topic or subject matter (not covered by existing examples)
- Would expand topic coverage while feeling stylistically consistent
- Is clear and specific enough to generate meaningful responses

EXISTING EXAMPLES (match their style, avoid their topics):
{examples_summary}

Generate a prompt that sounds like it came from the same person who wrote the existing examples, just asking about a different subject.

Respond in this exact JSON format:
{
  "prompt": "Your style-matched prompt about a new topic here",
  "reasoning": "How this matches the style while exploring new material"
}`;

// YOLO mode prompt for generating MULTIPLE novel prompts at once (more efficient)
const YOLO_BATCH_PROMPT_GENERATION = `You are a curriculum designer for an AI training system.

Your task: Generate {count} prompts that explore NEW subject matter while matching the style of existing examples.

STYLE MATCHING (CRITICAL):
- Study the TONE of existing examples (formal/casual, technical/conversational) and MATCH IT EXACTLY
- Study the LENGTH of existing examples and generate prompts of SIMILAR LENGTH
- Study the STRUCTURE (questions, requests, scenarios) and FOLLOW THE SAME PATTERN
- All {count} prompts should feel like they belong in the same dataset - same voice, different subjects

CONTENT RULES:
- NEVER generate duplicates or rephrasings of any existing example
- The TOPICS must be different, but the STYLE must be consistent
- The {count} prompts should cover different subjects from EACH OTHER too
- Explore diverse subject matter while maintaining stylistic consistency

EXISTING EXAMPLES (match their style, avoid their topics):
{examples_summary}

Generate {count} prompts that:
- ALL MATCH the tone, style, and length of existing examples
- Each explores a DIFFERENT topic or subject matter
- Cover different domains (tech, science, arts, business, personal, creative, etc.)
- Would expand topic coverage while feeling stylistically consistent
- Are clear and specific enough to generate meaningful responses

Generate prompts that sound like they all came from the same person who wrote the existing examples, just asking about {count} different subjects.

Respond in this exact JSON format:
{
  "prompts": ["prompt1", "prompt2", "prompt3", ...],
  "reasoning": "Brief explanation of style matched and diverse topics covered"
}`;

/**
 * Create a summary of existing examples for curriculum learning.
 * Includes all examples to help the AI match style and avoid duplicate topics.
 */
function summarizeExamplesForCurriculum(examples: Example[]): string {
  if (examples.length === 0) {
    return "No existing examples yet. This is the first training session - generate diverse foundational prompts. Use a clear, conversational tone and moderate length (1-2 sentences).";
  }

  // Include more examples to help match style and avoid duplicate topics
  const maxExamples = Math.min(examples.length, 30);
  const summary = examples
    .slice(0, maxExamples)
    .map(
      (ex, i) => `${i + 1}. "${ex.question.slice(0, 150)}${ex.question.length > 150 ? "..." : ""}"`
    )
    .join("\n");

  // Add explicit instruction about style matching
  const coverageNote =
    examples.length > maxExamples
      ? `\n\n(Showing ${maxExamples} of ${examples.length} total examples.)`
      : "";

  return `EXISTING EXAMPLES - Study these carefully to match their TONE, LENGTH, and STYLE:\n${summary}${coverageNote}\n\nGenerate prompts that MATCH this style but cover DIFFERENT topics.`;
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
