"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Save, RotateCcw, Info } from "lucide-react";
import type { Id } from "../../convex/_generated/dataModel";

const DEFAULT_SYSTEM_PROMPT = `You are a helpful, knowledgeable assistant. You provide clear, accurate, and thoughtful responses.

Your responses should be:
- Informative and well-structured
- Friendly but professional in tone
- Concise yet comprehensive`;

interface SystemPromptEditorProps {
  databaseId: Id<"databases"> | null;
}

export function SystemPromptEditor({ databaseId }: SystemPromptEditorProps) {
  const database = useQuery(api.databases.get, databaseId ? { id: databaseId } : "skip");
  const updateDatabase = useMutation(api.databases.update);

  const [prompt, setPrompt] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Sync prompt with database
  useEffect(() => {
    if (database) {
      setPrompt(database.systemPrompt ?? DEFAULT_SYSTEM_PROMPT);
      setHasChanges(false);
    }
  }, [database]);

  const handleSave = async () => {
    if (!databaseId) return;

    setIsSaving(true);
    try {
      await updateDatabase({
        id: databaseId,
        systemPrompt: prompt.trim() || undefined,
      });
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save system prompt:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setPrompt(DEFAULT_SYSTEM_PROMPT);
    setHasChanges(true);
  };

  const handleChange = (value: string) => {
    setPrompt(value);
    setHasChanges(value !== (database?.systemPrompt ?? DEFAULT_SYSTEM_PROMPT));
  };

  if (!databaseId) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Select a database to configure its system prompt.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold">System Prompt</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Configure the AI&apos;s persona and response style.
        </p>
      </div>

      {/* Info Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Define the assistant&apos;s personality, expertise, and tone. The training instructions
          are automatically appended during generation.
        </AlertDescription>
      </Alert>

      {/* Editor */}
      <div className="space-y-4">
        <div className="grid gap-2">
          <Label htmlFor="system-prompt">Prompt Template</Label>
          <Textarea
            id="system-prompt"
            value={prompt}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Enter your system prompt..."
            className="min-h-[300px] font-mono text-sm"
          />
        </div>

        <div className="flex items-center justify-between">
          <Button variant="outline" onClick={handleReset} disabled={isSaving}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset to Default
          </Button>

          <Button onClick={handleSave} disabled={!hasChanges || isSaving}>
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>

        {hasChanges && <p className="text-sm text-muted-foreground">You have unsaved changes.</p>}
      </div>
    </div>
  );
}
