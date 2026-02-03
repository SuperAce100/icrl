"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Sparkles, Loader2, RefreshCw, Wand2, AlertCircle } from "lucide-react";
import { generateSuggestions } from "@/lib/actions";

interface QuestionInputProps {
  databaseId: string | null;
  onSubmit: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function QuestionInput({ databaseId, onSubmit, isLoading, disabled }: QuestionInputProps) {
  const [question, setQuestion] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [suggestionsFromCache, setSuggestionsFromCache] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);

  // Refs to prevent double-triggering in React Strict Mode
  const isFetchingRef = useRef(false);
  const lastDatabaseIdRef = useRef<string | null>(null);

  // Fetch AI-generated suggestions
  const fetchSuggestions = useCallback(
    async (forceRefresh: boolean = false) => {
      if (!databaseId) return;

      // Prevent double-triggering (unless force refresh or database changed)
      if (!forceRefresh && isFetchingRef.current && lastDatabaseIdRef.current === databaseId) {
        return;
      }

      isFetchingRef.current = true;
      lastDatabaseIdRef.current = databaseId;

      setIsLoadingSuggestions(true);
      setSuggestionsError(null);
      try {
        const result = await generateSuggestions(databaseId, forceRefresh);
        setSuggestions(result.suggestions);
        setSuggestionsFromCache(result.fromCache);
      } catch (error) {
        console.error("Error fetching suggestions:", error);
        setSuggestions([]);
        setSuggestionsError(
          error instanceof Error ? error.message : "Failed to generate suggestions"
        );
      } finally {
        setIsLoadingSuggestions(false);
        isFetchingRef.current = false;
      }
    },
    [databaseId]
  );

  // Fetch suggestions on mount and when database changes
  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading && !disabled) {
      onSubmit(question.trim());
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuestion(suggestion);
  };

  const handleRefreshSuggestions = () => {
    fetchSuggestions(true);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          Enter a Prompt
        </CardTitle>
        <CardDescription>
          Enter a prompt to generate two response options. Your feedback will help train the model.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="question">Your Prompt</Label>
            <Textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your prompt here..."
              className="min-h-[100px] resize-none"
              disabled={isLoading || disabled}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={!question.trim() || isLoading || disabled}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating answers...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Answers
              </>
            )}
          </Button>
        </form>

        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                AI-suggested prompts
                {suggestionsFromCache && <span className="text-xs ml-1 opacity-70">(cached)</span>}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshSuggestions}
              disabled={isLoadingSuggestions || isLoading}
              className="h-7 px-2 text-xs"
            >
              <RefreshCw className={`h-3 w-3 mr-1 ${isLoadingSuggestions ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          {isLoadingSuggestions ? (
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-6 w-32" />
              ))}
            </div>
          ) : suggestionsError ? (
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{suggestionsError}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefreshSuggestions}
                className="h-6 px-2 text-xs"
              >
                Retry
              </Button>
            </div>
          ) : suggestions.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, i) => (
                <Badge
                  key={i}
                  variant="outline"
                  className="cursor-pointer hover:bg-muted transition-colors"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {suggestion.length > 40 ? suggestion.slice(0, 40) + "..." : suggestion}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No suggestions available</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
