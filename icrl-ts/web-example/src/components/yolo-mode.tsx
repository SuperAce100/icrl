"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Zap,
  Loader2,
  X,
  Trophy,
  ArrowRight,
  Sparkles,
  RotateCcw,
  Info,
  Battery,
} from "lucide-react";
import { generateYoloRound, generateYoloRoundsParallel, type YoloRoundResult } from "@/lib/actions";

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
  const [selectedOption, setSelectedOption] = useState<"A" | "B" | null>(null);
  const [completedCount, setCompletedCount] = useState(0);
  const [streak, setStreak] = useState(0);
  const [bufferCount, setBufferCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Buffer of precomputed rounds
  const bufferRef = useRef<YoloRoundResult[]>([]);
  const isFillingBufferRef = useRef(false);
  const hasInitializedRef = useRef(false);

  // Fill the buffer with precomputed rounds (parallelized batch generation)
  const fillBuffer = useCallback(async () => {
    if (isFillingBufferRef.current) return;
    if (bufferRef.current.length >= BUFFER_SIZE) return;

    isFillingBufferRef.current = true;

    try {
      // Calculate how many we need
      const needed = BUFFER_SIZE - bufferRef.current.length;
      const toGenerate = Math.min(needed, BATCH_SIZE);

      if (toGenerate > 0) {
        console.log(`[YOLO Buffer] Generating ${toGenerate} rounds in parallel...`);

        // Generate all rounds in parallel (prompts in one call, answers parallelized)
        const results = await generateYoloRoundsParallel(databaseId, toGenerate, systemPrompt);

        // Add all results to buffer
        bufferRef.current.push(...results);
        setBufferCount(bufferRef.current.length);

        console.log(`[YOLO Buffer] Buffer now has ${bufferRef.current.length} rounds`);
      }
    } catch (err) {
      console.error("Error filling buffer:", err);
      // Don't set error here - we might still have buffered items
    } finally {
      isFillingBufferRef.current = false;
    }
  }, [databaseId, systemPrompt]);

  // Get next round from buffer or generate one
  const getNextRound = useCallback(async (): Promise<YoloRoundResult | null> => {
    // Try to get from buffer first
    if (bufferRef.current.length > 0) {
      const next = bufferRef.current.shift()!;
      setBufferCount(bufferRef.current.length);
      // Start refilling buffer in background
      fillBuffer();
      return next;
    }

    // Buffer empty, generate directly
    try {
      const result = await generateYoloRound(databaseId, systemPrompt);
      // Start filling buffer in background
      fillBuffer();
      return result;
    } catch (err) {
      console.error("Error generating round:", err);
      throw err;
    }
  }, [databaseId, systemPrompt, fillBuffer]);

  // Advance to the next round
  const advanceToNextRound = useCallback(async () => {
    setIsLoading(true);
    setSelectedOption(null);
    setError(null);

    try {
      const next = await getNextRound();
      setCurrentRound(next);
    } catch (err) {
      console.error("Error getting next round:", err);
      setError(err instanceof Error ? err.message : "Failed to generate round");
      setCurrentRound(null);
    } finally {
      setIsLoading(false);
    }
  }, [getNextRound]);

  // Initialize: generate multiple rounds in parallel for fast startup
  useEffect(() => {
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    const init = async () => {
      setIsLoading(true);
      try {
        console.log(`[YOLO Init] Generating ${BATCH_SIZE} rounds in parallel for fast startup...`);

        // Generate multiple rounds in parallel right away
        const results = await generateYoloRoundsParallel(databaseId, BATCH_SIZE, systemPrompt);

        // Use first one as current, rest go to buffer
        if (results.length > 0) {
          setCurrentRound(results[0]);
          bufferRef.current = results.slice(1);
          setBufferCount(bufferRef.current.length);
          console.log(
            `[YOLO Init] Ready! Current round loaded, ${bufferRef.current.length} in buffer`
          );
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

  // Handle answer selection
  const handleSelect = async (choice: "A" | "B") => {
    if (!currentRound || isSubmitting) return;

    setSelectedOption(choice);
    setIsSubmitting(true);

    try {
      const chosen = choice === "A" ? currentRound.answerA : currentRound.answerB;
      const rejected = choice === "A" ? currentRound.answerB : currentRound.answerA;

      // Save answer and advance to next round in parallel
      const [,] = await Promise.all([
        onSelectAnswer(currentRound.prompt, chosen, rejected, false),
        // Small delay for visual feedback, then advance
        new Promise<void>((resolve) => setTimeout(resolve, 300)),
      ]);

      setCompletedCount((c) => c + 1);
      setStreak((s) => s + 1);

      // Immediately advance to next round (should be instant if buffer has items)
      await advanceToNextRound();
    } catch (err) {
      console.error("Error saving answer:", err);
      setStreak(0);
      setError(err instanceof Error ? err.message : "Failed to save answer");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle skip (no preference)
  const handleSkip = async () => {
    setStreak(0);
    await advanceToNextRound();
  };

  return (
    <Card className="border-2 border-yellow-500/50 bg-linear-to-br from-yellow-500/5 to-orange-500/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            YOLO Mode
            <Badge variant="secondary" className="ml-2">
              Auto-generate
            </Badge>
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onExit}>
            <X className="h-4 w-4 mr-1" />
            Exit
          </Button>
        </div>
        <CardDescription>
          AI generates both the prompt and answers. Just pick your preferred response!
        </CardDescription>

        {/* Stats bar */}
        <div className="flex items-center gap-4 mt-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <Trophy className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-medium">{completedCount} completed</span>
          </div>
          {streak > 0 && (
            <div className="flex items-center gap-1">
              <Sparkles className="h-4 w-4 text-orange-500" />
              <span className="text-sm text-orange-500 font-medium">{streak} streak!</span>
            </div>
          )}
          {/* Buffer indicator */}
          <div className="flex items-center gap-1 ml-auto" title="Precomputed prompts ready">
            <Battery
              className={`h-4 w-4 ${bufferCount >= BUFFER_SIZE - 1 ? "text-green-500" : bufferCount > 0 ? "text-yellow-500" : "text-muted-foreground"}`}
            />
            <span className="text-xs text-muted-foreground">{bufferCount} ready</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {isLoading ? (
          // Loading state
          <div className="space-y-4">
            <div className="bg-muted/50 rounded-lg p-4">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-6 w-full" />
            </div>
            <div className="grid gap-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Generating next prompt...</span>
            </div>
          </div>
        ) : currentRound ? (
          // Round content
          <>
            {/* Generated prompt */}
            <div className="bg-muted/50 rounded-lg p-4">
              <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                AI-generated prompt:
              </p>
              <p className="font-medium">{currentRound.prompt}</p>
            </div>

            {/* Retrieved Examples Info */}
            {currentRound.retrievedExamples.length > 0 && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Retrieved {currentRound.retrievedExamples.length} similar example(s) to inform the
                  answers.
                  <details className="mt-2">
                    <summary className="text-xs cursor-pointer hover:text-primary">
                      View retrieved examples
                    </summary>
                    <div className="mt-2 space-y-2">
                      {currentRound.retrievedExamples.map((ex, i) => (
                        <div
                          key={i}
                          className="text-xs text-muted-foreground bg-background p-2 rounded"
                        >
                          <span className="font-medium">Q:</span> {ex.question.slice(0, 80)}
                          {ex.question.length > 80 ? "..." : ""}
                        </div>
                      ))}
                    </div>
                  </details>
                </AlertDescription>
              </Alert>
            )}

            {/* Answer options */}
            <div className="space-y-3">
              {/* Option A */}
              <button
                onClick={() => handleSelect("A")}
                disabled={isSubmitting}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  selectedOption === "A"
                    ? "border-green-500 bg-green-500/10"
                    : "border-border hover:border-primary/50"
                } ${isSubmitting ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                      selectedOption === "A"
                        ? "bg-green-500 text-white"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    A
                  </span>
                  <p className="text-sm leading-relaxed">{currentRound.answerA}</p>
                </div>
              </button>

              {/* Option B */}
              <button
                onClick={() => handleSelect("B")}
                disabled={isSubmitting}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  selectedOption === "B"
                    ? "border-green-500 bg-green-500/10"
                    : "border-border hover:border-primary/50"
                } ${isSubmitting ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                      selectedOption === "B"
                        ? "bg-green-500 text-white"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    B
                  </span>
                  <p className="text-sm leading-relaxed">{currentRound.answerB}</p>
                </div>
              </button>
            </div>

            {/* Skip button */}
            <div className="flex items-center justify-center pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSkip}
                disabled={isSubmitting}
                className="text-muted-foreground"
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Skip this one
              </Button>
            </div>

            {/* Submitting indicator */}
            {isSubmitting && (
              <div className="flex items-center justify-center gap-2 text-primary">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Saving and generating next...</span>
              </div>
            )}
          </>
        ) : error ? (
          // Error state
          <div className="text-center py-8">
            <p className="text-destructive mb-2 font-medium">Error</p>
            <p className="text-muted-foreground mb-4 text-sm">{error}</p>
            <Button onClick={() => advanceToNextRound()}>
              <ArrowRight className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        ) : (
          // No round available
          <div className="text-center py-8">
            <p className="text-muted-foreground mb-4">No round available. Please try again.</p>
            <Button onClick={() => advanceToNextRound()}>
              <ArrowRight className="h-4 w-4 mr-2" />
              Generate
            </Button>
          </div>
        )}

        {/* Progress indicator */}
        {completedCount > 0 && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span>Training progress this session</span>
              <span>{completedCount} examples added</span>
            </div>
            <Progress value={Math.min(completedCount * 10, 100)} className="h-2" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
