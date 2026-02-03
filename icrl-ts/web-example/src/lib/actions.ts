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
    console.warn("Anthropic Vertex not configured, returning mock answers");
    return generateMockAnswers(question, examples);
  }

  try {
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
      return {
        answerA: parsed.answerA || "Unable to generate answer A",
        answerB: parsed.answerB || "Unable to generate answer B",
      };
    }

    // Fallback if JSON parsing fails
    return {
      answerA: response,
      answerB: "Alternative answer not available",
    };
  } catch (error) {
    console.error("Error generating answers:", error);
    return generateMockAnswers(question, examples);
  }
}

/**
 * Generate mock answers when API is not configured.
 */
function generateMockAnswers(question: string, examples: Example[]): GeneratedAnswers {
  const hasExamples = examples.length > 0;

  return {
    answerA: hasExamples
      ? `Based on similar questions in your database, here's a detailed answer to "${question}": This is a comprehensive response that draws from the ${examples.length} example(s) in your training data. In a production setup with Anthropic Vertex configured, this would be a real AI-generated response influenced by your examples.`
      : `Here's a helpful answer to "${question}": This is a detailed response covering the key aspects of your question. Configure GOOGLE_CREDENTIALS_JSON to enable real AI-generated answers.`,
    answerB: hasExamples
      ? `Alternative perspective on "${question}": Here's a more concise take that offers a different viewpoint. With more examples in your database, the AI will learn your preferred style.`
      : `Quick answer to "${question}": This is a more concise response. Add examples to your database to personalize future answers.`,
  };
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
