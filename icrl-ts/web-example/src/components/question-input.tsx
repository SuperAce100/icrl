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
import { Sparkles, Loader2 } from "lucide-react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const sampleQuestions = [
  "What's the best way to learn a new language?",
  "How do I stay motivated when working from home?",
  "What are some tips for better sleep?",
  "How can I improve my public speaking skills?",
  "What's a good strategy for saving money?",
];

export function QuestionInput({
  onSubmit,
  isLoading,
  disabled,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading && !disabled) {
      onSubmit(question.trim());
    }
  };

  const handleSampleClick = (sample: string) => {
    setQuestion(sample);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          Ask a Question
        </CardTitle>
        <CardDescription>
          Enter a question to generate two answer options. Your feedback will
          help train the model.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="question">Your Question</Label>
            <Textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your question here..."
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
          <p className="text-sm text-muted-foreground mb-3">
            Or try a sample question:
          </p>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.map((sample, i) => (
              <Badge
                key={i}
                variant="outline"
                className="cursor-pointer hover:bg-muted transition-colors"
                onClick={() => handleSampleClick(sample)}
              >
                {sample.length > 35 ? sample.slice(0, 35) + "..." : sample}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
