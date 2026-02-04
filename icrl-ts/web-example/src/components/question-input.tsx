"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowRight, Loader2, RefreshCw, Zap } from "lucide-react";
import { generateSuggestions } from "@/lib/actions";

interface QuestionInputProps {
  databaseId: string | null;
  onSubmit: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  yoloMode?: boolean;
  onYoloModeChange?: (enabled: boolean) => void;
}

export function QuestionInput({
  databaseId,
  onSubmit,
  isLoading,
  disabled,
  yoloMode = false,
  onYoloModeChange,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Refs to prevent double-triggering
  const isFetchingRef = useRef(false);
  const lastDatabaseIdRef = useRef<string | null>(null);

  // Fetch AI-generated suggestions
  const fetchSuggestions = useCallback(
    async (forceRefresh: boolean = false) => {
      if (!databaseId) return;

      if (!forceRefresh && isFetchingRef.current && lastDatabaseIdRef.current === databaseId) {
        return;
      }

      isFetchingRef.current = true;
      lastDatabaseIdRef.current = databaseId;

      setIsLoadingSuggestions(true);
      try {
        const result = await generateSuggestions(databaseId, forceRefresh);
        setSuggestions(result.suggestions);
      } catch (error) {
        console.error("Error fetching suggestions:", error);
        setSuggestions([]);
      } finally {
        setIsLoadingSuggestions(false);
        isFetchingRef.current = false;
      }
    },
    [databaseId]
  );

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading && !disabled) {
      onSubmit(question.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (question.trim() && !isLoading && !disabled) {
        onSubmit(question.trim());
      }
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuestion(suggestion);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex flex-col items-center justify-center flex-1">
      <div className="w-full space-y-4">
        {/* Input Container */}
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter a prompt to train..."
              disabled={isLoading || disabled}
              rows={3}
              className="w-full resize-none rounded-xl border border-input bg-card px-4 py-3 pr-24 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/20 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:border-ring transition-all"
            />

            {/* Bottom bar with YOLO toggle and submit */}
            <div className="absolute bottom-3 right-1.5 flex items-center gap-2">
              {/* YOLO Toggle */}
              {onYoloModeChange && (
                <div className="flex items-center gap-2">
                  <Label
                    htmlFor="yolo-toggle"
                    className="text-xs text-muted-foreground cursor-pointer flex items-center gap-1"
                  >
                    <Zap className="h-3 w-3" />
                    YOLO
                  </Label>
                  <Switch
                    id="yolo-toggle"
                    checked={yoloMode}
                    onCheckedChange={onYoloModeChange}
                    disabled={isLoading}
                    className="scale-75"
                  />
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                size="icon-sm"
                disabled={!question.trim() || isLoading || disabled}
                
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

        {/* Suggestions Grid */}
        {isLoadingSuggestions ? (
          <div className="grid grid-cols-2 gap-2 px-2">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))}
          </div>
        ) : suggestions.length > 0 ? (
          <div className="relative">
            <div className="grid grid-cols-2 gap-2 px-2">
              {suggestions.slice(0, 6).map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(suggestion)}
                  disabled={isLoading}
                  className="p-3 text-left text-sm rounded-lg border border-border bg-background hover:bg-muted hover:border-primary/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="">{suggestion}</span>
                </button>
              ))}
            </div>
            
          </div>
        ) : null}
      </div>
    </div>
  );
}
