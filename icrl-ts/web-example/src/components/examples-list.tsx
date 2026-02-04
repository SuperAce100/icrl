"use client";

import { useState, useRef, useCallback } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronDown, ChevronUp, Trash2, Search, MessageSquare, RefreshCw } from "lucide-react";
import type { Id, Doc } from "../../convex/_generated/dataModel";

type ExampleDoc = Doc<"examples">;

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
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const startHold = useCallback(() => {
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
  }, [disabled, holdDuration, onDelete]);

  const cancelHold = useCallback(() => {
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
      onMouseDown={startHold}
      onMouseUp={cancelHold}
      onMouseLeave={cancelHold}
      onTouchStart={startHold}
      onTouchEnd={cancelHold}
      onTouchCancel={cancelHold}
      disabled={disabled}
      className={`
        relative overflow-hidden inline-flex items-center justify-center gap-1 
        px-3 py-1.5 text-sm rounded-md transition-colors
        ${disabled ? "opacity-50 cursor-not-allowed bg-muted text-muted-foreground" : "text-destructive hover:bg-destructive/10 cursor-pointer"}
        ${isHolding ? "bg-destructive/10" : ""}
      `}
      onClick={(e) => e.stopPropagation()}
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Training Examples</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Examples are used as context when generating new answers.
          </p>
        </div>
        {stats && (
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-1">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <span>{stats.totalExamples}</span>
            </div>
            <div className="flex items-center gap-1">
              <Search className="h-4 w-4 text-muted-foreground" />
              <span>{stats.totalRetrievals}</span>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-muted/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-primary">{stats.totalExamples}</p>
            <p className="text-xs text-muted-foreground">Total Examples</p>
          </div>
          <div className="bg-muted/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-icrl-blue">{stats.totalRetrievals}</p>
            <p className="text-xs text-muted-foreground">Times Retrieved</p>
          </div>
          <div className="bg-muted/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-purple-500">{stats.customAnswers}</p>
            <p className="text-xs text-muted-foreground">Custom Answers</p>
          </div>
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
        <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
          {examples.map((example: ExampleDoc) => (
            <div key={example._id} className="border rounded-lg overflow-hidden">
              <button
                onClick={() => setExpandedId(expandedId === example._id ? null : example._id)}
                className="w-full text-left p-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {example.isCustom && (
                        <Badge variant="secondary" className="text-xs">
                          Custom
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {formatDate(example.createdAt)}
                      </span>
                    </div>
                    <p className="text-sm font-medium truncate">{example.question}</p>
                    <p className="text-xs text-muted-foreground truncate mt-1">
                      {example.chosenAnswer}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <Badge variant="outline" className="text-xs font-normal gap-1">
                      <RefreshCw className="h-3 w-3" />
                      {example.timesRetrieved ?? 0}
                    </Badge>
                    {expandedId === example._id ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </div>
                </div>
              </button>

              {expandedId === example._id && (
                <div className="px-4 pb-4 space-y-3 border-t bg-muted/20">
                  <div className="pt-3">
                    <p className="text-xs font-medium text-green-600 mb-1">Chosen Answer:</p>
                    <p className="text-sm bg-background rounded p-3">{example.chosenAnswer}</p>
                  </div>
                  {example.rejectedAnswer && (
                    <div>
                      <p className="text-xs font-medium text-red-600 mb-1">Rejected Answer:</p>
                      <p className="text-sm bg-background rounded p-3 text-muted-foreground">
                        {example.rejectedAnswer}
                      </p>
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <RefreshCw className="h-3 w-3" />
                      <span>
                        Retrieved{" "}
                        <strong className="text-foreground">{example.timesRetrieved ?? 0}</strong>{" "}
                        time
                        {(example.timesRetrieved ?? 0) !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <HoldToDeleteButton
                      onDelete={() => handleDelete(example._id)}
                      disabled={deletingId === example._id}
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
