"use client";

import { useState, useEffect } from "react";
import { QuestionInput } from "@/components/QuestionInput";
import { AnswerChoice } from "@/components/AnswerChoice";
import { ExamplesList } from "@/components/ExamplesList";
import { SuccessMessage } from "@/components/SuccessMessage";
import { generateAnswerOptions, submitFeedback, checkApiStatus } from "@/lib/actions";
import type { GeneratedAnswers, FeedbackResult } from "@/lib/types";

type AppState = "input" | "choosing" | "success";
type Tab = "ask" | "database";

export default function Home() {
  const [state, setState] = useState<AppState>("input");
  const [tab, setTab] = useState<Tab>("ask");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedData, setGeneratedData] = useState<GeneratedAnswers | null>(null);
  const [feedbackResult, setFeedbackResult] = useState<FeedbackResult | null>(null);
  const [apiStatus, setApiStatus] = useState<{ configured: boolean; message: string } | null>(null);

  useEffect(() => {
    checkApiStatus().then(setApiStatus);
  }, []);

  const handleQuestionSubmit = async (question: string) => {
    setIsLoading(true);
    try {
      const data = await generateAnswerOptions(question);
      setGeneratedData(data);
      setState("choosing");
    } catch (error) {
      console.error("Error generating answers:", error);
      alert("Failed to generate answers. Please try again.");
    }
    setIsLoading(false);
  };

  const handleAnswerSelect = async (
    chosen: string,
    rejected: string | undefined,
    isCustom: boolean
  ) => {
    if (!generatedData) return;

    setIsSubmitting(true);
    try {
      const result = await submitFeedback(
        generatedData.question,
        chosen,
        rejected,
        isCustom
      );
      setFeedbackResult(result);
      setState("success");
    } catch (error) {
      console.error("Error submitting feedback:", error);
      alert("Failed to save feedback. Please try again.");
    }
    setIsSubmitting(false);
  };

  const handleReset = () => {
    setState("input");
    setGeneratedData(null);
    setFeedbackResult(null);
  };

  return (
    <main className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <span className="text-emerald-400">ICRL</span>
                <span className="text-gray-400 font-normal">RLHF Demo</span>
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                In-Context Reinforcement Learning with Human Feedback
              </p>
            </div>
            <a
              href="https://github.com/SuperAce100/icrl"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </div>
        </div>
      </header>

      {/* API Status Banner */}
      {apiStatus && !apiStatus.configured && (
        <div className="bg-yellow-900/30 border-b border-yellow-800/50">
          <div className="max-w-4xl mx-auto px-4 py-2">
            <p className="text-xs text-yellow-400 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              {apiStatus.message}
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex gap-1">
            <button
              onClick={() => setTab("ask")}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === "ask"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-gray-400 hover:text-gray-300"
              }`}
            >
              Ask & Train
            </button>
            <button
              onClick={() => setTab("database")}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === "database"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-gray-400 hover:text-gray-300"
              }`}
            >
              Database
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {tab === "ask" ? (
          <div className="max-w-2xl mx-auto">
            {/* How it works */}
            {state === "input" && (
              <div className="mb-8 bg-gray-900/50 rounded-lg p-4 border border-gray-800">
                <h2 className="text-sm font-medium text-white mb-2">How it works:</h2>
                <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
                  <li>Ask any question</li>
                  <li>The system retrieves similar examples from the database</li>
                  <li>Two answer options are generated (influenced by examples)</li>
                  <li>You choose the better answer (or write your own)</li>
                  <li>Your choice is stored and improves future answers</li>
                </ol>
              </div>
            )}

            {/* Main content based on state */}
            {state === "input" && (
              <QuestionInput onSubmit={handleQuestionSubmit} isLoading={isLoading} />
            )}

            {state === "choosing" && generatedData && (
              <div className="space-y-4">
                <button
                  onClick={handleReset}
                  className="text-sm text-gray-400 hover:text-gray-300 flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 19l-7-7m0 0l7-7m-7 7h18"
                    />
                  </svg>
                  Back
                </button>
                <AnswerChoice
                  data={generatedData}
                  onSelect={handleAnswerSelect}
                  isSubmitting={isSubmitting}
                />
              </div>
            )}

            {state === "success" && feedbackResult && (
              <SuccessMessage message={feedbackResult.message} onReset={handleReset} />
            )}
          </div>
        ) : (
          <ExamplesList />
        )}
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <p className="text-center text-xs text-gray-500">
            Built with{" "}
            <a href="https://github.com/SuperAce100/icrl" className="text-emerald-400 hover:underline">
              ICRL
            </a>{" "}
            • In-Context Reinforcement Learning for LLM Agents
          </p>
        </div>
      </footer>
    </main>
  );
}
