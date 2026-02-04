"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Kbd } from "@/components/ui/kbd";
import { Loader2, ArrowLeft, CornerDownLeft } from "lucide-react";
import { cn } from "@/lib/utils";

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

  const handleSelectA = useCallback(() => {
    if (isSubmitting) return;
    setSelectedOption("A");
    onSelect(answerA, answerB, false);
  }, [isSubmitting, onSelect, answerA, answerB]);

  const handleSelectB = useCallback(() => {
    if (isSubmitting) return;
    setSelectedOption("B");
    onSelect(answerB, answerA, false);
  }, [isSubmitting, onSelect, answerA, answerB]);

  const handleSubmitCustom = useCallback(() => {
    if (customAnswer.trim() && !isSubmitting) {
      setSelectedOption("custom");
      onSelect(customAnswer.trim(), undefined, true);
    }
  }, [customAnswer, isSubmitting, onSelect]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in the custom answer field
      if (document.activeElement === customInputRef.current) {
        // Allow Enter to submit custom answer
        if (e.key === "Enter" && !e.shiftKey && customAnswer.trim()) {
          e.preventDefault();
          handleSubmitCustom();
        }
        return;
      }

      if (isSubmitting) return;

      if (e.key.toLowerCase() === "a") {
        e.preventDefault();
        handleSelectA();
      } else if (e.key.toLowerCase() === "b") {
        e.preventDefault();
        handleSelectB();
      } else if (e.key === "Escape") {
        e.preventDefault();
        onBack();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSubmitting, customAnswer, handleSelectA, handleSelectB, handleSubmitCustom, onBack]);

  return (
    <div className="flex flex-col items-center">
      <div className="w-full max-w-xl space-y-6">
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
        <p className="text-lg font-medium">{question}</p>

        {/* Answer Options */}
        <div className="space-y-3">
          {/* Option A */}
          <button
            onClick={handleSelectA}
            disabled={isSubmitting}
            className={cn(
              "w-full text-left p-4 rounded-xl border-2 bg-card shadow-sm transition-all",
              selectedOption === "A"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50",
              isSubmitting && "opacity-50 cursor-not-allowed"
            )}
          >
            <div className="flex items-start gap-3">
              <Kbd
                className={cn(
                  "h-7 w-7 text-sm shrink-0",
                  selectedOption === "A" && "bg-primary text-primary-foreground"
                )}
              >
                A
              </Kbd>
              <p className="text-sm leading-relaxed">{answerA}</p>
            </div>
          </button>

          {/* Option B */}
          <button
            onClick={handleSelectB}
            disabled={isSubmitting}
            className={cn(
              "w-full text-left p-4 rounded-xl border-2 bg-card shadow-sm transition-all",
              selectedOption === "B"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50",
              isSubmitting && "opacity-50 cursor-not-allowed"
            )}
          >
            <div className="flex items-start gap-3">
              <Kbd
                className={cn(
                  "h-7 w-7 text-sm shrink-0",
                  selectedOption === "B" && "bg-primary text-primary-foreground"
                )}
              >
                B
              </Kbd>
              <p className="text-sm leading-relaxed">{answerB}</p>
            </div>
          </button>
        </div>

        {/* Custom Answer - Always visible */}
        <div className="relative">
          <Textarea
            ref={customInputRef}
            value={customAnswer}
            onChange={(e) => setCustomAnswer(e.target.value)}
            placeholder="Or write your own answer..."
            disabled={isSubmitting}
            rows={2}
            className="pr-12 resize-none"
          />
          <Button
            type="button"
            size="icon"
            variant="ghost"
            onClick={handleSubmitCustom}
            disabled={!customAnswer.trim() || isSubmitting}
            className="absolute bottom-2 right-2 h-7 w-7"
            title="Submit custom answer (Enter)"
          >
            <CornerDownLeft className="h-4 w-4" />
          </Button>
        </div>

        {/* Submitting indicator */}
        {isSubmitting && (
          <div className="flex items-center justify-center gap-2 text-primary">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Saving...</span>
          </div>
        )}
      </div>
    </div>
  );
}
