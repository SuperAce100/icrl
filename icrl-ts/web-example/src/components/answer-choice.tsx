"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Kbd } from "@/components/ui/kbd";
import { Loader2, ArrowLeft, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import Markdown from "@/components/ui/markdown";

interface RetrievedExample {
  question: string;
  chosenAnswer: string;
}

interface AnswerChoiceProps {
  question: string;
  answerA: string;
  answerB: string;
  retrievedExamples: RetrievedExample[];
  onSelect: (chosen: string, rejected: string | undefined, isCustom: boolean) => void;
  onBack: () => void;
  isSubmitting: boolean;
}

export function AnswerChoice({
  question,
  answerA,
  answerB,
  onSelect,
  onBack,
  isSubmitting,
}: AnswerChoiceProps) {
  const [customAnswer, setCustomAnswer] = useState("");
  const [selectedOption, setSelectedOption] = useState<"A" | "B" | "custom" | null>(null);
  const customInputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    if (isSubmitting) return;

    if (selectedOption === "A") {
      onSelect(answerA, answerB, false);
    } else if (selectedOption === "B") {
      onSelect(answerB, answerA, false);
    } else if (selectedOption === "custom" && customAnswer.trim()) {
      onSelect(customAnswer.trim(), undefined, true);
    }
  }, [selectedOption, isSubmitting, onSelect, answerA, answerB, customAnswer]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger A/B if typing in the custom answer field
      const isTypingCustom = document.activeElement === customInputRef.current;

      if (isSubmitting) return;

      if (e.key.toLowerCase() === "a" && !isTypingCustom) {
        e.preventDefault();
        setSelectedOption("A");
      } else if (e.key.toLowerCase() === "b" && !isTypingCustom) {
        e.preventDefault();
        setSelectedOption("B");
      } else if (e.key === "Enter" && !e.shiftKey) {
        // Submit on Enter if something is selected
        if (selectedOption === "A" || selectedOption === "B") {
          e.preventDefault();
          handleSubmit();
        } else if (selectedOption === "custom" && customAnswer.trim() && isTypingCustom) {
          e.preventDefault();
          handleSubmit();
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onBack();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSubmitting, selectedOption, customAnswer, handleSubmit, onBack]);

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
    !isSubmitting;

  return (
    <div className="flex flex-col items-center">
      <div className="w-full space-y-4">
        {/* Back button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          disabled={isSubmitting}
          className="text-muted-foreground hover:text-foreground -ml-2"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
          <Kbd className="ml-2">Esc</Kbd>
        </Button>

        {/* Question */}
        <p className="text-xl font-medium">{question}</p>

        {/* Answer Options - Side by Side */}
        <div className="grid grid-cols-2 gap-4">
          {/* Option A */}
          <button
            onClick={() => setSelectedOption("A")}
            disabled={isSubmitting}
            className={cn(
              "text-left p-4 py-3 rounded-lg border bg-card  transition-all h-full",
              selectedOption === "A"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50",
              isSubmitting && "opacity-50 cursor-not-allowed"
            )}
          >
            <div className="flex items-start gap-2 justify-between flex-col h-full">
              <Markdown className="text-sm leading-relaxed">{answerA}</Markdown>
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
              "text-left p-4 py-3 rounded-lg border bg-card  transition-all h-full",
              selectedOption === "B"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50",
              isSubmitting && "opacity-50 cursor-not-allowed"
            )}
          >
            <div className="flex items-start gap-2 justify-between flex-col h-full">
              <Markdown className="text-sm leading-relaxed">{answerB}</Markdown>
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

        {/* Submit Button */}
        <div className="flex justify-end">
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
      </div>
    </div>
  );
}
