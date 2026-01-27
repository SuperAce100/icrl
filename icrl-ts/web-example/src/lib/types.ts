/**
 * Types for the RLHF demo
 */

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface Example {
  id: string;
  question: string;
  chosenAnswer: string;
  rejectedAnswer?: string;
  customAnswer?: boolean;
  createdAt: string;
  timesRetrieved: number;
  timesHelpful: number;
}

export interface GeneratedAnswers {
  question: string;
  answerA: string;
  answerB: string;
  retrievedExamples: Example[];
}

export interface FeedbackResult {
  success: boolean;
  exampleId?: string;
  message: string;
}

export interface Stats {
  totalExamples: number;
  totalFeedback: number;
  customAnswers: number;
}
