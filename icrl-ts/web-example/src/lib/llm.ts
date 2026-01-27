/**
 * LLM integration for generating answers
 */

import OpenAI from "openai";
import type { Example } from "./types";

// Initialize OpenAI client (uses OPENAI_API_KEY env var)
const openai = new OpenAI();

/**
 * Format examples for the prompt
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
 * Generate two different answer options for a question
 */
export async function generateAnswers(
  question: string,
  examples: Example[]
): Promise<{ answerA: string; answerB: string }> {
  const examplesText = formatExamples(examples);

  const systemPrompt = `You are a helpful assistant. You will be given a question and some examples of good answers to similar questions.

Your task is to generate TWO different answers to the question:
- Answer A: A high-quality, detailed, helpful answer (similar in style to the examples)
- Answer B: A different but also reasonable answer (could be shorter, different perspective, or alternative approach)

Both answers should be valid, but they should be noticeably different from each other.

Here are examples of good answers:
${examplesText}

Respond in this exact JSON format:
{
  "answerA": "Your first answer here",
  "answerB": "Your second answer here"
}`;

  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `Question: ${question}` },
      ],
      temperature: 0.8,
      max_tokens: 1000,
    });

    const content = response.choices[0]?.message?.content || "";
    
    // Parse JSON response
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        answerA: parsed.answerA || "Unable to generate answer A",
        answerB: parsed.answerB || "Unable to generate answer B",
      };
    }

    // Fallback if JSON parsing fails
    return {
      answerA: content,
      answerB: "Alternative answer not available",
    };
  } catch (error) {
    console.error("Error generating answers:", error);
    
    // Return mock answers if API fails (for demo purposes)
    return {
      answerA: `Here's a helpful answer to "${question}": This is a detailed response that addresses your question comprehensively.`,
      answerB: `Quick answer to "${question}": Here's a more concise response.`,
    };
  }
}

/**
 * Check if OpenAI API is configured
 */
export function isOpenAIConfigured(): boolean {
  return !!process.env.OPENAI_API_KEY;
}
