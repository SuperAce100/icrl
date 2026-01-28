"use client";

import { useState } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ChevronDown,
  ChevronUp,
  Trash2,
  Search,
  MessageSquare,
  RefreshCw,
} from "lucide-react";
import type { Id, Doc } from "../../convex/_generated/dataModel";

type ExampleDoc = Doc<"examples">;

interface ExamplesListProps {
  databaseId: Id<"databases"> | null;
}

export function ExamplesList({ databaseId }: ExamplesListProps) {
  const examples = useQuery(
    api.examples.listByDatabase,
    databaseId ? { databaseId } : "skip"
  );
  const stats = useQuery(
    api.databases.getStats,
    databaseId ? { id: databaseId } : "skip"
  );
  const deleteExample = useMutation(api.examples.remove);

  const [expandedId, setExpandedId] = useState<Id<"examples"> | null>(null);
  const [deleteId, setDeleteId] = useState<Id<"examples"> | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!deleteId) return;

    setIsDeleting(true);
    try {
      await deleteExample({ id: deleteId });
      setDeleteId(null);
    } catch (error) {
      console.error("Failed to delete example:", error);
    } finally {
      setIsDeleting(false);
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
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center py-8">
            Select a database to view its examples.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Training Examples</span>
          {stats && (
            <div className="flex gap-4 text-sm font-normal">
              <div className="flex items-center gap-1">
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
                <span>{stats.totalExamples} examples</span>
              </div>
              <div className="flex items-center gap-1">
                <Search className="h-4 w-4 text-muted-foreground" />
                <span>{stats.totalRetrievals} retrievals</span>
              </div>
            </div>
          )}
        </CardTitle>
        <CardDescription>
          Examples are used as context when generating new answers. More examples
          lead to better personalized responses.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-muted/50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-primary">
                {stats.totalExamples}
              </p>
              <p className="text-xs text-muted-foreground">Total Examples</p>
            </div>
            <div className="bg-muted/50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-blue-500">
                {stats.totalRetrievals}
              </p>
              <p className="text-xs text-muted-foreground">Times Retrieved</p>
            </div>
            <div className="bg-muted/50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-500">
                {stats.customAnswers}
              </p>
              <p className="text-xs text-muted-foreground">Custom Answers</p>
            </div>
          </div>
        )}

        <Separator className="mb-4" />

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
            <p className="text-sm">
              Start asking questions to build your training data!
            </p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-3">
              {examples.map((example: ExampleDoc) => (
                <div
                  key={example._id}
                  className="border rounded-lg overflow-hidden"
                >
                  <button
                    onClick={() =>
                      setExpandedId(
                        expandedId === example._id ? null : example._id
                      )
                    }
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
                        <p className="text-sm font-medium truncate">
                          {example.question}
                        </p>
                        <p className="text-xs text-muted-foreground truncate mt-1">
                          {example.chosenAnswer}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1" title="Times retrieved">
                          <RefreshCw className="h-3 w-3" />
                          {example.timesRetrieved}
                        </div>
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
                        <p className="text-xs font-medium text-green-600 mb-1">
                          Chosen Answer:
                        </p>
                        <p className="text-sm bg-background rounded p-3">
                          {example.chosenAnswer}
                        </p>
                      </div>
                      {example.rejectedAnswer && (
                        <div>
                          <p className="text-xs font-medium text-red-600 mb-1">
                            Rejected Answer:
                          </p>
                          <p className="text-sm bg-background rounded p-3 text-muted-foreground">
                            {example.rejectedAnswer}
                          </p>
                        </div>
                      )}
                      <div className="flex justify-end pt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteId(example._id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Example</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this example? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
