/**
 * Simple in-memory database for RLHF examples
 * In production, you'd use a real database + vector store
 */

import { v4 as uuidv4 } from "uuid";
import type { Example, Stats } from "./types";

// In-memory store (persists across requests in dev, resets on restart)
const examples: Map<string, Example> = new Map();

// Seed with some initial examples
const seedExamples: Omit<Example, "id" | "createdAt" | "timesRetrieved" | "timesHelpful">[] = [
  {
    question: "What is the capital of France?",
    chosenAnswer: "The capital of France is Paris. It's known as the 'City of Light' and is famous for the Eiffel Tower, the Louvre Museum, and its rich cultural heritage.",
    rejectedAnswer: "France's capital is Lyon.",
  },
  {
    question: "How do I make a good cup of coffee?",
    chosenAnswer: "For a great cup of coffee: 1) Use freshly roasted beans, 2) Grind just before brewing, 3) Use water at 195-205°F, 4) Use a ratio of about 1:16 coffee to water, 5) Brew for 3-4 minutes depending on method.",
    rejectedAnswer: "Just add hot water to instant coffee.",
  },
  {
    question: "What's the best way to learn programming?",
    chosenAnswer: "The best approach is: 1) Start with fundamentals (variables, loops, functions), 2) Build small projects to apply what you learn, 3) Read other people's code, 4) Practice consistently, 5) Don't be afraid to make mistakes - debugging is learning!",
    rejectedAnswer: "Watch YouTube videos all day.",
  },
];

// Initialize with seed data
if (examples.size === 0) {
  for (const seed of seedExamples) {
    const id = uuidv4();
    examples.set(id, {
      ...seed,
      id,
      createdAt: new Date().toISOString(),
      timesRetrieved: 0,
      timesHelpful: 0,
    });
  }
}

/**
 * Simple keyword-based similarity (in production, use embeddings)
 */
function computeSimilarity(query: string, text: string): number {
  const queryWords = new Set(query.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  const textWords = new Set(text.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  
  let matches = 0;
  for (const word of queryWords) {
    if (textWords.has(word)) matches++;
  }
  
  return queryWords.size > 0 ? matches / queryWords.size : 0;
}

/**
 * Search for similar examples
 */
export function searchExamples(query: string, k: number = 3): Example[] {
  const scored = Array.from(examples.values()).map(ex => ({
    example: ex,
    score: computeSimilarity(query, ex.question + " " + ex.chosenAnswer),
  }));
  
  scored.sort((a, b) => b.score - a.score);
  
  const results = scored.slice(0, k).filter(s => s.score > 0).map(s => s.example);
  
  // Update retrieval counts
  for (const ex of results) {
    ex.timesRetrieved++;
  }
  
  return results;
}

/**
 * Add a new example from human feedback
 */
export function addExample(
  question: string,
  chosenAnswer: string,
  rejectedAnswer?: string,
  customAnswer: boolean = false
): Example {
  const id = uuidv4();
  const example: Example = {
    id,
    question,
    chosenAnswer,
    rejectedAnswer,
    customAnswer,
    createdAt: new Date().toISOString(),
    timesRetrieved: 0,
    timesHelpful: 0,
  };
  
  examples.set(id, example);
  return example;
}

/**
 * Record that an example was helpful
 */
export function recordHelpful(exampleId: string): void {
  const example = examples.get(exampleId);
  if (example) {
    example.timesHelpful++;
  }
}

/**
 * Get all examples
 */
export function getAllExamples(): Example[] {
  return Array.from(examples.values()).sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
}

/**
 * Get database stats
 */
export function getStats(): Stats {
  const all = Array.from(examples.values());
  return {
    totalExamples: all.length,
    totalFeedback: all.reduce((sum, ex) => sum + ex.timesRetrieved, 0),
    customAnswers: all.filter(ex => ex.customAnswer).length,
  };
}

/**
 * Delete an example
 */
export function deleteExample(id: string): boolean {
  return examples.delete(id);
}
