"use client";

import { useState, useEffect } from "react";
import type { Example, Stats } from "@/lib/types";
import { fetchAllExamples, fetchStats, removeExample } from "@/lib/actions";

export function ExamplesList() {
  const [examples, setExamples] = useState<Example[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [examplesData, statsData] = await Promise.all([
        fetchAllExamples(),
        fetchStats(),
      ]);
      setExamples(examplesData);
      setStats(statsData);
    } catch (error) {
      console.error("Error loading data:", error);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this example?")) {
      await removeExample(id);
      loadData();
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <svg className="animate-spin h-8 w-8 text-emerald-500" viewBox="0 0 24 24">
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
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 text-center">
            <p className="text-2xl font-bold text-emerald-400">{stats.totalExamples}</p>
            <p className="text-xs text-gray-400">Total Examples</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 text-center">
            <p className="text-2xl font-bold text-blue-400">{stats.totalFeedback}</p>
            <p className="text-xs text-gray-400">Times Retrieved</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 text-center">
            <p className="text-2xl font-bold text-purple-400">{stats.customAnswers}</p>
            <p className="text-xs text-gray-400">Custom Answers</p>
          </div>
        </div>
      )}

      {/* Refresh button */}
      <div className="flex justify-end">
        <button
          onClick={loadData}
          className="text-sm text-gray-400 hover:text-gray-300 flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Examples list */}
      <div className="space-y-3">
        {examples.length === 0 ? (
          <p className="text-center text-gray-500 py-8">No examples yet. Start by asking a question!</p>
        ) : (
          examples.map((example) => (
            <div
              key={example.id}
              className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden"
            >
              <button
                onClick={() => setExpandedId(expandedId === example.id ? null : example.id)}
                className="w-full text-left p-4 hover:bg-gray-800/80 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {example.customAnswer && (
                        <span className="text-xs px-2 py-0.5 bg-purple-900/50 text-purple-400 rounded-full">
                          Custom
                        </span>
                      )}
                      <span className="text-xs text-gray-500">{formatDate(example.createdAt)}</span>
                    </div>
                    <p className="text-sm text-white font-medium truncate">{example.question}</p>
                    <p className="text-xs text-gray-400 mt-1 truncate">{example.chosenAnswer}</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span title="Times retrieved">🔍 {example.timesRetrieved}</span>
                    <svg
                      className={`w-4 h-4 transition-transform ${
                        expandedId === example.id ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
              </button>

              {expandedId === example.id && (
                <div className="px-4 pb-4 space-y-3 border-t border-gray-700 pt-3">
                  <div>
                    <p className="text-xs text-emerald-400 mb-1">✓ Chosen Answer:</p>
                    <p className="text-sm text-gray-300 bg-gray-900/50 rounded p-3">
                      {example.chosenAnswer}
                    </p>
                  </div>
                  {example.rejectedAnswer && (
                    <div>
                      <p className="text-xs text-red-400 mb-1">✗ Rejected Answer:</p>
                      <p className="text-sm text-gray-400 bg-gray-900/50 rounded p-3">
                        {example.rejectedAnswer}
                      </p>
                    </div>
                  )}
                  <div className="flex justify-end">
                    <button
                      onClick={() => handleDelete(example.id)}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
