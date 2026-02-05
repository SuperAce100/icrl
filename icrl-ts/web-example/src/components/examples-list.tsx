"use client";

import { useState, useRef, useCallback, useMemo } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Trash2, MessageSquare, ArrowUpDown, TrendingUp, Calendar } from "lucide-react";
import type { Id, Doc } from "../../convex/_generated/dataModel";
import { cn } from "@/lib/utils";

type ExampleDoc = Doc<"examples">;
type SortOption = "newest" | "oldest" | "most-retrieved" | "least-retrieved";

// ICRL brand colors for interpolation
const ICRL_ORANGE = { r: 248, g: 141, b: 57 }; // #F88D39
const ICRL_BLUE = { r: 24, g: 138, b: 212 }; // #188AD4

/**
 * Interpolate between two colors based on a ratio (0-1).
 * Returns an RGB string.
 */
function interpolateColor(
  from: { r: number; g: number; b: number },
  to: { r: number; g: number; b: number },
  ratio: number
): string {
  const r = Math.round(from.r + (to.r - from.r) * ratio);
  const g = Math.round(from.g + (to.g - from.g) * ratio);
  const b = Math.round(from.b + (to.b - from.b) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Get interpolated color based on retrieval count relative to max.
 * Returns { color, border, borderWidth } for styling.
 */
function getRetrievalStyles(
  count: number,
  maxCount: number
): { color: string; border: string; borderWidth: number } {
  if (maxCount === 0 || count === 0) {
    return {
      color: "inherit",
      border: "transparent",
      borderWidth: 0,
    };
  }

  const ratio = count / maxCount;
  const color = interpolateColor(ICRL_ORANGE, ICRL_BLUE, ratio);

  // Border width scales with ratio
  const borderWidth = ratio >= 0.5 ? 4 : ratio >= 0.1 ? 2 : 1;

  return {
    color,
    border: color,
    borderWidth,
  };
}

// Hold-to-delete button component
interface HoldToDeleteButtonProps {
  onDelete: () => void;
  holdDuration?: number;
  disabled?: boolean;
}

function HoldToDeleteButton({
  onDelete,
  holdDuration = 1500,
  disabled = false,
}: HoldToDeleteButtonProps) {
  const [progress, setProgress] = useState(0);
  const [isHolding, setIsHolding] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const startHold = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (disabled) return;

      setIsHolding(true);
      startTimeRef.current = Date.now();

      intervalRef.current = setInterval(() => {
        if (!startTimeRef.current) return;
        const elapsed = Date.now() - startTimeRef.current;
        const newProgress = Math.min((elapsed / holdDuration) * 100, 100);
        setProgress(newProgress);

        if (newProgress >= 100) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setIsHolding(false);
          setProgress(0);
          startTimeRef.current = null;
          onDelete();
        }
      }, 16);
    },
    [disabled, holdDuration, onDelete]
  );

  const cancelHold = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsHolding(false);
    setProgress(0);
    startTimeRef.current = null;
  }, []);

  return (
    <button
      type="button"
      onMouseDown={startHold}
      onMouseUp={cancelHold}
      onMouseLeave={cancelHold}
      onTouchStart={startHold}
      onTouchEnd={cancelHold}
      onTouchCancel={cancelHold}
      disabled={disabled}
      className={cn(
        "relative overflow-hidden inline-flex items-center justify-center gap-1 px-3 py-1.5 text-sm rounded-md transition-colors select-none",
        disabled
          ? "opacity-50 cursor-not-allowed bg-muted text-muted-foreground"
          : "text-destructive hover:bg-destructive/10 cursor-pointer",
        isHolding && "bg-destructive/10"
      )}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
    >
      <div
        className="absolute inset-0 bg-destructive/20 transition-all duration-75"
        style={{ width: `${progress}%` }}
      />
      <span className="relative z-10 flex items-center gap-1">
        <Trash2 className="h-4 w-4" />
        Hold to Delete
      </span>
    </button>
  );
}

interface ExamplesListProps {
  databaseId: Id<"databases"> | null;
}

export function ExamplesList({ databaseId }: ExamplesListProps) {
  const examples = useQuery(api.examples.listByDatabase, databaseId ? { databaseId } : "skip");
  const stats = useQuery(api.databases.getStats, databaseId ? { id: databaseId } : "skip");
  const deleteExample = useMutation(api.examples.remove);

  const [expandedId, setExpandedId] = useState<Id<"examples"> | null>(null);
  const [deletingId, setDeletingId] = useState<Id<"examples"> | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>("newest");

  // Calculate max retrieval count for color scaling
  const maxRetrievalCount = useMemo(() => {
    if (!examples || examples.length === 0) return 0;
    return Math.max(...examples.map((ex) => ex.timesRetrieved ?? 0));
  }, [examples]);

  // Sort examples based on selected option
  const sortedExamples = useMemo(() => {
    if (!examples) return [];

    const sorted = [...examples];
    switch (sortBy) {
      case "newest":
        return sorted.sort((a, b) => b.createdAt - a.createdAt);
      case "oldest":
        return sorted.sort((a, b) => a.createdAt - b.createdAt);
      case "most-retrieved":
        return sorted.sort((a, b) => (b.timesRetrieved ?? 0) - (a.timesRetrieved ?? 0));
      case "least-retrieved":
        return sorted.sort((a, b) => (a.timesRetrieved ?? 0) - (b.timesRetrieved ?? 0));
      default:
        return sorted;
    }
  }, [examples, sortBy]);

  const handleDelete = async (id: Id<"examples">) => {
    setDeletingId(id);
    try {
      await deleteExample({ id });
      if (expandedId === id) {
        setExpandedId(null);
      }
    } catch (error) {
      console.error("Failed to delete example:", error);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (!databaseId) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Select a database to view its examples.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-full overflow-y-auto">
      {/* Header */}
      <h2 className="text-xl font-semibold">Saved Examples</h2>

      {/* Stats */}
      {stats && (
        <div className="flex flex-row gap-6">
          <div>
            <p className="text-5xl font-medium text-primary">{stats.totalExamples}</p>
            <p className="text-xs font-medium tracking-wider text-muted-foreground mb-1">
              Examples Saved
            </p>
          </div>
          <div>
            <p className="text-5xl font-medium text-icrl-blue">{stats.totalRetrievals}</p>
            <p className="text-xs font-medium tracking-wider text-muted-foreground mb-1">
              Times Retrieved
            </p>
          </div>
          <div>
            <p className="text-5xl font-medium text-icrl-yellow">{stats.customAnswers}</p>
            <p className="text-xs font-medium tracking-wider text-muted-foreground mb-1">
              Custom Answers
            </p>
          </div>
        </div>
      )}

      {/* Sorting Controls */}
      {examples && examples.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {examples.length} example{examples.length !== 1 ? "s" : ""}
          </p>
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
            <SelectTrigger className="w-[180px] h-8 text-sm">
              <ArrowUpDown className="h-3.5 w-3.5 mr-2 text-muted-foreground" />
              <SelectValue placeholder="Sort by..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">
                <span className="flex items-center gap-2">
                  <Calendar className="h-3.5 w-3.5" />
                  Newest first
                </span>
              </SelectItem>
              <SelectItem value="oldest">
                <span className="flex items-center gap-2">
                  <Calendar className="h-3.5 w-3.5" />
                  Oldest first
                </span>
              </SelectItem>
              <SelectItem value="most-retrieved">
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Most retrieved
                </span>
              </SelectItem>
              <SelectItem value="least-retrieved">
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-3.5 w-3.5 rotate-180" />
                  Least retrieved
                </span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Examples List */}
      {!examples ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 border rounded-lg">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      ) : examples.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No examples yet.</p>
          <p className="text-sm">Start asking questions to build your training data!</p>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto pr-2">
          {sortedExamples.map((example: ExampleDoc) => {
            const retrievalCount = example.timesRetrieved ?? 0;
            const styles = getRetrievalStyles(retrievalCount, maxRetrievalCount);

            return (
              <div key={example._id} className="border rounded-lg overflow-hidden bg-card">
                <button
                  onClick={() => setExpandedId(expandedId === example._id ? null : example._id)}
                  className="w-full text-left p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {/* Retrieval count with interpolated color */}
                        <span
                          className="text-xs font-semibold tabular-nums flex items-center gap-1"
                          style={{ color: retrievalCount > 0 ? styles.color : undefined }}
                        >
                          <TrendingUp className="h-3 w-3" />
                          {retrievalCount}
                        </span>
                        {example.isCustom && (
                          <Badge variant="secondary" className="text-xs">
                            Custom
                          </Badge>
                        )}
                        <span className="text-xs text-muted-foreground">
                          {formatDate(example.createdAt)}
                        </span>
                      </div>
                      <p className="text-sm font-medium">{example.question}</p>
                    </div>
                  </div>
                </button>

                <div
                  className={cn(
                    expandedId === example._id ? "h-auto" : "h-0",
                    "flex flex-col gap-2 overflow-hidden"
                  )}
                >
                  <div className="px-4 pb-4 space-y-3 border-t bg-muted/20">
                    <div className="pt-3">
                      <p className="text-xs font-medium text-green-600 mb-1">Chosen Answer:</p>
                      <p className="text-sm">{example.chosenAnswer}</p>
                    </div>
                    {example.rejectedAnswer && (
                      <div>
                        <p className="text-xs font-medium text-red-600 mb-1">Rejected Answer:</p>
                        <p className="text-sm text-muted-foreground">{example.rejectedAnswer}</p>
                      </div>
                    )}
                    <div className="flex items-center justify-end pt-2">
                      <HoldToDeleteButton
                        onDelete={() => handleDelete(example._id)}
                        disabled={deletingId === example._id}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
