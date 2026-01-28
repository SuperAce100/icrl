"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  ChevronDown,
  ChevronUp,
  Check,
  Loader2,
  ArrowLeft,
  Info,
  PenLine,
} from "lucide-react";

interface RetrievedExample {
  question: string;
  chosenAnswer: string;
}

interface AnswerChoiceProps {
  question: string;
  answerA: string;
  answerB: string;
  retrievedExamples: RetrievedExample[];
  onSelect: (
    chosen: string,
    rejected: string | undefined,
    isCustom: boolean
  ) => void;
  onBack: () => void;
  isSubmitting: boolean;
}

export function AnswerChoice({
  question,
  answerA,
  answerB,
  retrievedExamples,
  onSelect,
  onBack,
  isSubmitting,
}: AnswerChoiceProps) {
  const [customAnswer, setCustomAnswer] = useState("");
  const [showCustom, setShowCustom] = useState(false);
  const [selectedOption, setSelectedOption] = useState<
    "A" | "B" | "custom" | null
  >(null);

  const handleSelectA = () => {
    setSelectedOption("A");
    onSelect(answerA, answerB, false);
  };

  const handleSelectB = () => {
    setSelectedOption("B");
    onSelect(answerB, answerA, false);
  };

  const handleSubmitCustom = () => {
    if (customAnswer.trim()) {
      setSelectedOption("custom");
      onSelect(customAnswer.trim(), undefined, true);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2 mb-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            disabled={isSubmitting}
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </div>
        <CardTitle>Choose the Better Answer</CardTitle>
        <CardDescription>
          Select the answer you prefer, or write your own. Your choice will be
          saved and used to improve future responses.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Question Display */}
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Question:</p>
          <p className="font-medium">{question}</p>
        </div>

        {/* Retrieved Examples Info */}
        {retrievedExamples.length > 0 && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Retrieved {retrievedExamples.length} similar example(s) from your
              database to help generate these answers.
              <details className="mt-2">
                <summary className="text-xs cursor-pointer hover:text-primary">
                  View retrieved examples
                </summary>
                <div className="mt-2 space-y-2">
                  {retrievedExamples.map((ex, i) => (
                    <div
                      key={i}
                      className="text-xs text-muted-foreground bg-background p-2 rounded"
                    >
                      <span className="font-medium">Q:</span>{" "}
                      {ex.question.slice(0, 80)}
                      {ex.question.length > 80 ? "..." : ""}
                    </div>
                  ))}
                </div>
              </details>
            </AlertDescription>
          </Alert>
        )}

        {/* Answer Options */}
        <div className="space-y-4">
          {/* Option A */}
          <button
            onClick={handleSelectA}
            disabled={isSubmitting}
            className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
              selectedOption === "A"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            } ${isSubmitting ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            <div className="flex items-start gap-3">
              <span
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  selectedOption === "A"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                A
              </span>
              <p className="text-sm leading-relaxed">{answerA}</p>
            </div>
          </button>

          {/* Option B */}
          <button
            onClick={handleSelectB}
            disabled={isSubmitting}
            className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
              selectedOption === "B"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            } ${isSubmitting ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            <div className="flex items-start gap-3">
              <span
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  selectedOption === "B"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                B
              </span>
              <p className="text-sm leading-relaxed">{answerB}</p>
            </div>
          </button>

          {/* Custom Answer Toggle */}
          <div className="pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCustom(!showCustom)}
              disabled={isSubmitting}
              className="text-muted-foreground"
            >
              {showCustom ? (
                <ChevronUp className="h-4 w-4 mr-2" />
              ) : (
                <ChevronDown className="h-4 w-4 mr-2" />
              )}
              <PenLine className="h-4 w-4 mr-2" />
              Neither is good? Write your own answer
            </Button>

            {showCustom && (
              <div className="mt-3 space-y-3 pl-4 border-l-2 border-muted">
                <div className="grid gap-2">
                  <Label htmlFor="custom-answer">Your Answer</Label>
                  <Textarea
                    id="custom-answer"
                    value={customAnswer}
                    onChange={(e) => setCustomAnswer(e.target.value)}
                    placeholder="Type your preferred answer..."
                    className="min-h-[100px]"
                    disabled={isSubmitting}
                  />
                </div>
                <Button
                  onClick={handleSubmitCustom}
                  disabled={!customAnswer.trim() || isSubmitting}
                  variant="secondary"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Submit Custom Answer
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Submitting indicator */}
        {isSubmitting && (
          <div className="flex items-center justify-center gap-2 text-primary">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Saving your feedback...</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
