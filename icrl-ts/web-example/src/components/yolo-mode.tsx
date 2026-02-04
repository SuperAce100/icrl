"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Kbd } from "@/components/ui/kbd";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2, X, RotateCcw, Zap } from "lucide-react";
import { generateYoloRoundsParallel, type YoloRoundResult } from "@/lib/actions";
import { cn } from "@/lib/utils";
import Markdown from "@/components/ui/markdown";

// Number of rounds to precompute in the buffer
const BUFFER_SIZE = 5;
// Number of rounds to generate in each parallel batch
const BATCH_SIZE = 5;

interface YoloModeProps {
  databaseId: string;
  systemPrompt?: string;
  onSelectAnswer: (
    prompt: string,
    chosen: string,
    rejected: string | undefined,
    isCustom: boolean
  ) => Promise<void>;
  onExit: () => void;
}

export function YoloMode({ databaseId, systemPrompt, onSelectAnswer, onExit }: YoloModeProps) {
  const [currentRound, setCurrentRound] = useState<YoloRoundResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedOption, setSelectedOption] = useState<"A" | "B" | "custom" | null>(null);
  const [customAnswer, setCustomAnswer] = useState("");
  const [completedCount, setCompletedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const customInputRef = useRef<HTMLTextAreaElement>(null);
  const bufferRef = useRef<YoloRoundResult[]>([]);
  const isFillingBufferRef = useRef(false);
  const hasInitializedRef = useRef(false);

  // Fill the buffer with precomputed rounds
  const fillBuffer = useCallback(async () => {
    if (isFillingBufferRef.current) return;
    if (bufferRef.current.length >= BUFFER_SIZE) return;

    isFillingBufferRef.current = true;

    try {
      const needed = BUFFER_SIZE - bufferRef.current.length;
      const toGenerate = Math.min(needed, BATCH_SIZE);

      if (toGenerate > 0) {
        const results = await generateYoloRoundsParallel(databaseId, toGenerate, systemPrompt);
        bufferRef.current.push(...results);
      }
    } catch (err) {
      console.error("Error filling buffer:", err);
    } finally {
      isFillingBufferRef.current = false;
    }
  }, [databaseId, systemPrompt]);

  // Advance to the next round
  const advanceToNextRound = useCallback(async () => {
    setIsLoading(true);
    setSelectedOption(null);
    setCustomAnswer("");
    setError(null);

    try {
      // Try to get from buffer first
      if (bufferRef.current.length > 0) {
        const next = bufferRef.current.shift()!;
        setCurrentRound(next);
        fillBuffer(); // Refill in background
      } else {
        // Buffer empty, generate directly
        const results = await generateYoloRoundsParallel(databaseId, 1, systemPrompt);
        if (results.length > 0) {
          setCurrentRound(results[0]);
        }
        fillBuffer();
      }
    } catch (err) {
      console.error("Error getting next round:", err);
      setError(err instanceof Error ? err.message : "Failed to generate round");
      setCurrentRound(null);
    } finally {
      setIsLoading(false);
    }
  }, [databaseId, systemPrompt, fillBuffer]);

  // Initialize
  useEffect(() => {
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    const init = async () => {
      setIsLoading(true);
      try {
        const results = await generateYoloRoundsParallel(databaseId, BATCH_SIZE, systemPrompt);
        if (results.length > 0) {
          setCurrentRound(results[0]);
          bufferRef.current = results.slice(1);
        }
      } catch (err) {
        console.error("Error initializing:", err);
        setError(err instanceof Error ? err.message : "Failed to initialize");
      } finally {
        setIsLoading(false);
      }
    };

    init();
  }, [databaseId, systemPrompt]);

  // Handle submit
  const handleSubmit = useCallback(async () => {
    if (!currentRound || isSubmitting) return;
    if (!selectedOption) return;

    setIsSubmitting(true);

    try {
      let chosen: string;
      let rejected: string | undefined;
      let isCustom = false;

      if (selectedOption === "A") {
        chosen = currentRound.answerA;
        rejected = currentRound.answerB;
      } else if (selectedOption === "B") {
        chosen = currentRound.answerB;
        rejected = currentRound.answerA;
      } else if (selectedOption === "custom" && customAnswer.trim()) {
        chosen = customAnswer.trim();
        rejected = undefined;
        isCustom = true;
      } else {
        return;
      }

      await onSelectAnswer(currentRound.prompt, chosen, rejected, isCustom);
      setCompletedCount((c) => c + 1);
      await advanceToNextRound();
    } catch (err) {
      console.error("Error saving answer:", err);
      setError(err instanceof Error ? err.message : "Failed to save answer");
    } finally {
      setIsSubmitting(false);
    }
  }, [
    currentRound,
    selectedOption,
    customAnswer,
    isSubmitting,
    onSelectAnswer,
    advanceToNextRound,
  ]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isTypingCustom = document.activeElement === customInputRef.current;

      if (isSubmitting || isLoading) return;

      if (e.key.toLowerCase() === "a" && !isTypingCustom) {
        e.preventDefault();
        setSelectedOption("A");
      } else if (e.key.toLowerCase() === "b" && !isTypingCustom) {
        e.preventDefault();
        setSelectedOption("B");
      } else if (e.key === "Enter" && !e.shiftKey) {
        if (selectedOption === "A" || selectedOption === "B") {
          e.preventDefault();
          handleSubmit();
        } else if (selectedOption === "custom" && customAnswer.trim() && isTypingCustom) {
          e.preventDefault();
          handleSubmit();
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onExit();
      } else if (e.key.toLowerCase() === "s" && !isTypingCustom) {
        e.preventDefault();
        advanceToNextRound();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    isSubmitting,
    isLoading,
    selectedOption,
    customAnswer,
    handleSubmit,
    onExit,
    advanceToNextRound,
  ]);

  // Select custom when typing
  const handleCustomChange = (value: string) => {
    setCustomAnswer(value);
    if (value.trim()) {
      setSelectedOption("custom");
    } else if (selectedOption === "custom") {
      setSelectedOption(null);
    }
  };

  const canSubmit =
    (selectedOption === "A" ||
      selectedOption === "B" ||
      (selectedOption === "custom" && customAnswer.trim())) &&
    !isSubmitting &&
    !isLoading;

  return (
    <div className="flex flex-col items-center">
      <div className="w-full space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Zap className="h-4 w-4 text-primary" />
            <span>YOLO Mode</span>
            {completedCount > 0 && <span className="text-xs">· {completedCount} completed</span>}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onExit}
            disabled={isSubmitting}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4 mr-1" />
            Exit
            <Kbd className="ml-2">Esc</Kbd>
          </Button>
        </div>

        {isLoading ? (
          // Loading state
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
            <div className="flex items-center justify-center gap-2 text-muted-foreground py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Generating prompt...</span>
            </div>
          </div>
        ) : error ? (
          // Error state
          <div className="text-center py-12">
            <p className="text-destructive mb-2">Error: {error}</p>
            <Button onClick={advanceToNextRound} variant="outline">
              Try Again
            </Button>
          </div>
        ) : currentRound ? (
          // Round content
          <>
            {/* Question/Prompt */}
            <p className="text-xl font-medium">{currentRound.prompt}</p>

            {/* Answer Options - Side by Side */}
            <div className="grid grid-cols-2 gap-4">
              {/* Option A */}
              <button
                onClick={() => setSelectedOption("A")}
                disabled={isSubmitting}
                className={cn(
                  "text-left p-4 py-3 rounded-lg border bg-card transition-all h-full",
                  selectedOption === "A"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50",
                  isSubmitting && "opacity-50 cursor-not-allowed"
                )}
              >
                <div className="flex items-start gap-2 justify-between flex-col h-full">
                  <Markdown className="text-sm leading-relaxed">{currentRound.answerA}</Markdown>
                  <p className="ml-auto text-xs">
                    <Kbd
                      className={cn(
                        "text-xs shrink-0",
                        selectedOption === "A" && "bg-primary text-primary-foreground"
                      )}
                    >
                      A
                    </Kbd>{" "}
                    to select
                  </p>
                </div>
              </button>

              {/* Option B */}
              <button
                onClick={() => setSelectedOption("B")}
                disabled={isSubmitting}
                className={cn(
                  "text-left p-4 py-3 rounded-lg border bg-card transition-all h-full",
                  selectedOption === "B"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50",
                  isSubmitting && "opacity-50 cursor-not-allowed"
                )}
              >
                <div className="flex items-start gap-2 justify-between flex-col h-full">
                  <Markdown className="text-sm leading-relaxed">{currentRound.answerB}</Markdown>
                  <p className="ml-auto text-xs">
                    <Kbd
                      className={cn(
                        "text-xs shrink-0",
                        selectedOption === "B" && "bg-primary text-primary-foreground"
                      )}
                    >
                      B
                    </Kbd>{" "}
                    to select
                  </p>
                </div>
              </button>
            </div>

            {/* Custom Answer */}
            <div
              className={cn(
                "rounded-lg border transition-all bg-card focus-within:border-primary/50",
                selectedOption === "custom"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <Textarea
                ref={customInputRef}
                value={customAnswer}
                onChange={(e) => handleCustomChange(e.target.value)}
                placeholder="Or write your own answer..."
                disabled={isSubmitting}
                rows={2}
                className="border-0 bg-transparent resize-none focus-visible:ring-0 focus-visible:ring-offset-0 text-sm shadow-none"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={advanceToNextRound}
                disabled={isSubmitting}
                className="text-muted-foreground"
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Skip
                <Kbd className="ml-2">S</Kbd>
              </Button>

              <Button onClick={handleSubmit} disabled={!canSubmit} size="sm">
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Submit
                    <Kbd className="bg-card/30 text-white -mr-1">↵</Kbd>
                  </>
                )}
              </Button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
