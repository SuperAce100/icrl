"use client";

import { useState } from "react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

const sampleQuestions = [
  "What's the best way to learn a new language?",
  "How do I stay motivated when working from home?",
  "What are some tips for better sleep?",
  "How can I improve my public speaking skills?",
  "What's a good strategy for saving money?",
];

export function QuestionInput({ onSubmit, isLoading }: QuestionInputProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSubmit(question.trim());
    }
  };

  const handleSampleClick = (sample: string) => {
    setQuestion(sample);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-300 mb-2">
            Ask a question
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question here..."
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
            rows={3}
            disabled={isLoading}
          />
        </div>
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Generating answers...
            </>
          ) : (
            "Generate Answers"
          )}
        </button>
      </form>

      <div>
        <p className="text-sm text-gray-400 mb-2">Or try a sample question:</p>
        <div className="flex flex-wrap gap-2">
          {sampleQuestions.map((sample, i) => (
            <button
              key={i}
              onClick={() => handleSampleClick(sample)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 rounded-full transition-colors"
            >
              {sample.length > 40 ? sample.slice(0, 40) + "..." : sample}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
