"use server";

/**
 * Server actions for the ICRL demo.
 * These handle LLM generation using Anthropic Vertex.
 */

import {
  generateCompletion,
  isAnthropicVertexConfigured,
  getConfigStatus,
} from "./anthropic-vertex";

const DEFAULT_SYSTEM_PROMPT = `You are a helpful assistant. You will be given a question and some examples of good answers to similar questions.

Your task is to generate TWO different answers to the question:
- Answer A: A high-quality, detailed, helpful answer (similar in style to the examples)
- Answer B: A different but also reasonable answer (could be shorter, different perspective, or alternative approach)

Both answers should be valid, but they should be noticeably different from each other.

Here are examples of good answers:
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
 * Format examples for inclusion in the prompt
 */
function formatExamples(examples: Example[]): string {
  if (examples.length === 0) {
    return "No similar examples available.";
  }

  return examples
    .map(
      (ex, i) =>
        `Example ${i + 1}:
Q: ${ex.question}
A: ${ex.chosenAnswer}`
    )
    .join("\n\n");
}

/**
 * Generate two answer options using Anthropic Vertex
 */
export async function generateAnswers(
  question: string,
  examples: Example[],
  systemPrompt?: string
): Promise<GeneratedAnswers> {
  const examplesText = formatExamples(examples);
  
  // Use provided system prompt or default, replacing {examples} placeholder
  const prompt = (systemPrompt || DEFAULT_SYSTEM_PROMPT).replace(
    "{examples}",
    examplesText
  );

  // Check if API is configured
  if (!isAnthropicVertexConfigured()) {
    // Return mock answers for demo purposes
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
    
    // Return mock answers on error
    return generateMockAnswers(question, examples);
  }
}

/**
 * Generate mock answers when API is not configured
 */
function generateMockAnswers(
  question: string,
  examples: Example[]
): GeneratedAnswers {
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
 * Check if the API is properly configured
 */
export async function checkApiStatus(): Promise<{
  configured: boolean;
  message: string;
}> {
  return getConfigStatus();
}
