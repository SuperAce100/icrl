"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowRight, Loader2, Copy, Check, RotateCcw } from "lucide-react";
import { generateSingleAnswer, searchSimilarExamples } from "@/lib/actions";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface AskModeProps {
  databaseId: string;
  systemPrompt?: string;
}

export function AskMode({ databaseId, systemPrompt }: AskModeProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    setIsLoading(true);
    setAnswer(null);

    try {
      // Retrieve similar examples
      const retrievedExamples = await searchSimilarExamples(databaseId, question.trim(), 5);

      // Generate single answer
      const response = await generateSingleAnswer(question.trim(), retrievedExamples, systemPrompt);
      setAnswer(response);
    } catch (error) {
      console.error("Error generating answer:", error);
      setAnswer("Sorry, there was an error generating the answer. Please try again.");
    }

    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (question.trim() && !isLoading) {
        handleSubmit(e);
      }
    }
  };

  const handleCopy = async () => {
    if (!answer) return;
    await navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setQuestion("");
    setAnswer(null);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex flex-col items-center justify-center flex-1">
      <div className="w-full space-y-6">
        {/* Logo */}
        <div className="flex items-center justify-center">
          <Image
            src="/logo_hero_dark.svg"
            alt="ICRL"
            width={152}
            height={52}
            className="hidden dark:block"
          />
          <Image
            src="/logo_hero_light.svg"
            alt="ICRL"
            width={602}
            height={52}
            className="block dark:hidden"
          />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              disabled={isLoading}
              rows={3}
              className="w-full resize-none rounded-lg border border-input bg-card px-4 py-3 pr-14 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/20 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:border-ring transition-all"
            />

            {/* Submit Button */}
            <div className="absolute bottom-3.5 right-2">
              <Button
                type="submit"
                size="icon-sm"
                className="rounded-sm"
                disabled={!question.trim() || isLoading}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </form>

        {/* Answer Display */}
        {isLoading && (
          <div className="space-y-3 p-4 rounded-lg border bg-card">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </div>
        )}

        {answer && !isLoading && (
          <div className="space-y-3">
            <div className="p-4 rounded-lg border bg-card">
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{answer}</p>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-muted-foreground"
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Ask another
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className={cn(copied && "text-green-600")}
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
