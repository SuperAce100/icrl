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
    console.warn("Anthropic Vertex not configured, returning fallback suggestions");
    return getFallbackSuggestions(examples);
  }

  const examplesSummary = summarizeExamplesForCurriculum(examples);
  const prompt = SUGGESTION_GENERATION_PROMPT.replace("{examples_summary}", examplesSummary);

  try {
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

    // Fallback if parsing fails
    return getFallbackSuggestions(examples);
  } catch (error) {
    console.error("Error calling Haiku for suggestions:", error);
    return getFallbackSuggestions(examples);
  }
}

/**
 * Get fallback suggestions based on existing examples.
 */
function getFallbackSuggestions(examples: Example[]): string[] {
  const baseSuggestions = [
    "What's the best way to learn a new skill quickly?",
    "How do I stay motivated when facing challenges?",
    "What are some tips for effective time management?",
    "How can I improve my decision-making process?",
    "What strategies help with creative problem-solving?",
  ];

  // If we have examples, try to generate complementary suggestions
  if (examples.length > 0) {
    // Check for topics not covered
    const existingTopics = examples.map((ex) => ex.question.toLowerCase());
    const hasLearning = existingTopics.some((t) => t.includes("learn"));
    const hasProductivity = existingTopics.some(
      (t) => t.includes("product") || t.includes("efficien")
    );
    const hasHealth = existingTopics.some((t) => t.includes("health") || t.includes("sleep"));
    const hasCommunication = existingTopics.some(
      (t) => t.includes("communic") || t.includes("speak")
    );
    const hasFinance = existingTopics.some(
      (t) => t.includes("money") || t.includes("save") || t.includes("financ")
    );

    const diverseSuggestions: string[] = [];
    if (!hasLearning)
      diverseSuggestions.push("What's the most effective way to learn something new?");
    if (!hasProductivity) diverseSuggestions.push("How can I be more productive in my daily work?");
    if (!hasHealth)
      diverseSuggestions.push("What habits contribute to better mental and physical health?");
    if (!hasCommunication)
      diverseSuggestions.push("How do I communicate more effectively with others?");
    if (!hasFinance)
      diverseSuggestions.push("What are smart strategies for personal financial planning?");

    // Fill remaining with base suggestions
    while (diverseSuggestions.length < 5) {
      const remaining = baseSuggestions.filter((s) => !diverseSuggestions.includes(s));
      if (remaining.length > 0) {
        diverseSuggestions.push(remaining[0]);
        baseSuggestions.splice(baseSuggestions.indexOf(remaining[0]), 1);
      } else {
        break;
      }
    }

    return diverseSuggestions.slice(0, 5);
  }

  return baseSuggestions;
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
    // Generate fallback content
    const fallbackPrompt = "What's the best approach to continuous learning and self-improvement?";
    const fallbackAnswers = generateMockAnswers(fallbackPrompt, []);
    return {
      prompt: fallbackPrompt,
      answerA: fallbackAnswers.answerA,
      answerB: fallbackAnswers.answerB,
      retrievedExamples: [],
    };
  }
}

/**
 * Generate just the prompt for YOLO mode using Claude Haiku.
 * Answers are generated separately using retrieved examples.
 */
async function generateYoloPromptWithHaiku(examples: Example[]): Promise<string> {
  // Check if API is configured
  if (!isAnthropicVertexConfigured()) {
    console.warn("Anthropic Vertex not configured, returning mock prompt");
    return generateMockYoloPrompt(examples);
  }

  const examplesSummary = summarizeExamplesForCurriculum(examples);
  const prompt = YOLO_PROMPT_GENERATION.replace("{examples_summary}", examplesSummary);

  try {
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

    // Fallback if parsing fails
    return generateMockYoloPrompt(examples);
  } catch (error) {
    console.error("Error calling Haiku for YOLO prompt:", error);
    return generateMockYoloPrompt(examples);
  }
}

/**
 * Generate a mock prompt for YOLO mode when API is not configured.
 */
function generateMockYoloPrompt(examples: Example[]): string {
  const mockPrompts = [
    "What's the most effective approach to learning a new technical skill?",
    "How can I improve my focus during deep work sessions?",
    "What strategies help with making difficult decisions?",
    "How do I build better habits that actually stick?",
    "What's the best way to give and receive constructive feedback?",
  ];

  // Pick one that doesn't overlap with existing examples
  const existingQuestions = examples.map((ex) => ex.question.toLowerCase());
  for (const mockPrompt of mockPrompts) {
    const isNovel = !existingQuestions.some(
      (q) =>
        q.includes(mockPrompt.toLowerCase().slice(0, 20)) ||
        mockPrompt.toLowerCase().includes(q.slice(0, 20))
    );
    if (isNovel) {
      return mockPrompt;
    }
  }

  // Default to first one if all overlap
  return mockPrompts[0];
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
