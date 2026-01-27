"use client";

import { useState } from "react";
import type { GeneratedAnswers, Example } from "@/lib/types";

interface AnswerChoiceProps {
  data: GeneratedAnswers;
  onSelect: (chosen: string, rejected: string | undefined, isCustom: boolean) => void;
  isSubmitting: boolean;
}

export function AnswerChoice({ data, onSelect, isSubmitting }: AnswerChoiceProps) {
  const [customAnswer, setCustomAnswer] = useState("");
  const [showCustom, setShowCustom] = useState(false);
  const [selectedOption, setSelectedOption] = useState<"A" | "B" | "custom" | null>(null);

  const handleSelectA = () => {
    setSelectedOption("A");
    onSelect(data.answerA, data.answerB, false);
  };

  const handleSelectB = () => {
    setSelectedOption("B");
    onSelect(data.answerB, data.answerA, false);
  };

  const handleSubmitCustom = () => {
    if (customAnswer.trim()) {
      setSelectedOption("custom");
      onSelect(customAnswer.trim(), undefined, true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Question */}
      <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
        <p className="text-sm text-gray-400 mb-1">Question:</p>
        <p className="text-white font-medium">{data.question}</p>
      </div>

      {/* Retrieved Examples */}
      {data.retrievedExamples.length > 0 && (
        <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-800/50">
          <p className="text-sm text-blue-400 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Retrieved {data.retrievedExamples.length} similar example(s) from database
          </p>
          <div className="space-y-2">
            {data.retrievedExamples.map((ex, i) => (
              <div key={ex.id} className="text-xs text-gray-400">
                <span className="text-blue-400">#{i + 1}:</span> {ex.question.slice(0, 60)}...
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Answer Options */}
      <div className="space-y-4">
        <p className="text-sm text-gray-300 font-medium">Choose the better answer:</p>

        {/* Option A */}
        <button
          onClick={handleSelectA}
          disabled={isSubmitting}
          className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
            selectedOption === "A"
              ? "border-emerald-500 bg-emerald-900/30"
              : "border-gray-700 bg-gray-800/50 hover:border-gray-600"
          } ${isSubmitting ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <div className="flex items-start gap-3">
            <span
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                selectedOption === "A"
                  ? "bg-emerald-500 text-white"
                  : "bg-gray-700 text-gray-300"
              }`}
            >
              A
            </span>
            <p className="text-gray-200 text-sm leading-relaxed">{data.answerA}</p>
          </div>
        </button>

        {/* Option B */}
        <button
          onClick={handleSelectB}
          disabled={isSubmitting}
          className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
            selectedOption === "B"
              ? "border-emerald-500 bg-emerald-900/30"
              : "border-gray-700 bg-gray-800/50 hover:border-gray-600"
          } ${isSubmitting ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <div className="flex items-start gap-3">
            <span
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                selectedOption === "B"
                  ? "bg-emerald-500 text-white"
                  : "bg-gray-700 text-gray-300"
              }`}
            >
              B
            </span>
            <p className="text-gray-200 text-sm leading-relaxed">{data.answerB}</p>
          </div>
        </button>

        {/* Custom Answer Toggle */}
        <div className="pt-2">
          <button
            onClick={() => setShowCustom(!showCustom)}
            disabled={isSubmitting}
            className="text-sm text-gray-400 hover:text-gray-300 flex items-center gap-2"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showCustom ? "rotate-90" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            Neither is good? Write your own answer
          </button>

          {showCustom && (
            <div className="mt-3 space-y-3">
              <textarea
                value={customAnswer}
                onChange={(e) => setCustomAnswer(e.target.value)}
                placeholder="Type your preferred answer..."
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                rows={4}
                disabled={isSubmitting}
              />
              <button
                onClick={handleSubmitCustom}
                disabled={!customAnswer.trim() || isSubmitting}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
              >
                Submit Custom Answer
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Submitting indicator */}
      {isSubmitting && (
        <div className="flex items-center justify-center gap-2 text-emerald-400">
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
          Saving your feedback...
        </div>
      )}
    </div>
  );
}
