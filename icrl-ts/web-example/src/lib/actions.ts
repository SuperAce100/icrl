"use server";

/**
 * Server actions for the RLHF demo
 */

import { searchExamples, addExample, getAllExamples, getStats, deleteExample } from "./database";
import { generateAnswers, isOpenAIConfigured } from "./llm";
import type { GeneratedAnswers, FeedbackResult, Example, Stats } from "./types";

/**
 * Generate two answer options for a question
 */
export async function generateAnswerOptions(question: string): Promise<GeneratedAnswers> {
  // Search for similar examples
  const retrievedExamples = searchExamples(question, 3);

  // Generate answers using LLM (with retrieved examples as context)
  const { answerA, answerB } = await generateAnswers(question, retrievedExamples);

  return {
    question,
    answerA,
    answerB,
    retrievedExamples,
  };
}

/**
 * Submit human feedback (chosen answer)
 */
export async function submitFeedback(
  question: string,
  chosenAnswer: string,
  rejectedAnswer: string | undefined,
  isCustom: boolean
): Promise<FeedbackResult> {
  try {
    const example = addExample(question, chosenAnswer, rejectedAnswer, isCustom);

    return {
      success: true,
      exampleId: example.id,
      message: isCustom
        ? "Your custom answer has been added to the database!"
        : "Your preference has been recorded and added to the database!",
    };
  } catch (error) {
    console.error("Error submitting feedback:", error);
    return {
      success: false,
      message: "Failed to save feedback. Please try again.",
    };
  }
}

/**
 * Get all examples in the database
 */
export async function fetchAllExamples(): Promise<Example[]> {
  return getAllExamples();
}

/**
 * Get database statistics
 */
export async function fetchStats(): Promise<Stats> {
  return getStats();
}

/**
 * Delete an example from the database
 */
export async function removeExample(id: string): Promise<boolean> {
  return deleteExample(id);
}

/**
 * Check if the API is properly configured
 */
export async function checkApiStatus(): Promise<{ configured: boolean; message: string }> {
  const configured = isOpenAIConfigured();
  return {
    configured,
    message: configured
      ? "OpenAI API is configured"
      : "OpenAI API key not found. Set OPENAI_API_KEY environment variable. Using mock responses.",
  };
}
