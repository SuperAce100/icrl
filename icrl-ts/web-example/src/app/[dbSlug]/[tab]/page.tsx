"use client";

import { useState } from "react";
import { useParams, notFound } from "next/navigation";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../convex/_generated/api";
import { QuestionInput } from "@/components/question-input";
import { AnswerChoice } from "@/components/answer-choice";
import { ExamplesList } from "@/components/examples-list";
import { SystemPromptEditor } from "@/components/system-prompt-editor";
import { YoloMode } from "@/components/yolo-mode";
import { generateAnswers, searchSimilarExamples } from "@/lib/actions";
import { isValidTabSlug } from "@/lib/slug";
import { Loader2 } from "lucide-react";

type AppState = "input" | "choosing" | "yolo";

interface GeneratedData {
  question: string;
  answerA: string;
  answerB: string;
  retrievedExamples: Array<{ question: string; chosenAnswer: string }>;
}

export default function TabPage() {
  const params = useParams();
  const dbSlug = params.dbSlug as string;
  const tab = params.tab as string;

  // Validate tab
  if (!isValidTabSlug(tab)) {
    notFound();
  }

  const database = useQuery(api.databases.getBySlug, { slug: dbSlug });
  const createExample = useMutation(api.examples.create);

  const [state, setState] = useState<AppState>("input");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedData, setGeneratedData] = useState<GeneratedData | null>(null);

  // Loading
  if (database === undefined) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Not found
  if (database === null) {
    return null;
  }

  const databaseId = database._id;

  const handleQuestionSubmit = async (question: string) => {
    setIsLoading(true);
    try {
      const retrievedExamples = await searchSimilarExamples(databaseId, question, 3);
      const { answerA, answerB } = await generateAnswers(
        question,
        retrievedExamples,
        database.systemPrompt ?? undefined
      );

      setGeneratedData({ question, answerA, answerB, retrievedExamples });
      setState("choosing");
    } catch (error) {
      console.error("Error generating answers:", error);
      alert("Failed to generate answers. Please try again.");
    }
    setIsLoading(false);
  };

  const handleAnswerSelect = async (
    chosen: string,
    rejected: string | undefined,
    isCustom: boolean
  ) => {
    if (!generatedData) return;

    setIsSubmitting(true);
    try {
      await createExample({
        databaseId,
        question: generatedData.question,
        chosenAnswer: chosen,
        rejectedAnswer: rejected,
        isCustom,
      });
      handleReset();
    } catch (error) {
      console.error("Error submitting feedback:", error);
      alert("Failed to save feedback. Please try again.");
    }
    setIsSubmitting(false);
  };

  const handleReset = () => {
    setState("input");
    setGeneratedData(null);
  };

  const handleYoloSelect = async (
    prompt: string,
    chosen: string,
    rejected: string | undefined,
    isCustom: boolean
  ) => {
    await createExample({
      databaseId,
      question: prompt,
      chosenAnswer: chosen,
      rejectedAnswer: rejected,
      isCustom,
    });
  };

  const enterYoloMode = () => {
    setState("yolo");
    setGeneratedData(null);
  };

  const exitYoloMode = () => {
    setState("input");
  };

  // Render content based on tab
  if (tab === "train") {
    return (
      <>
        {state === "input" && (
          <QuestionInput
            databaseId={databaseId}
            onSubmit={handleQuestionSubmit}
            isLoading={isLoading}
            disabled={false}
            onEnterYoloMode={enterYoloMode}
          />
        )}

        {state === "choosing" && generatedData && (
          <AnswerChoice
            question={generatedData.question}
            answerA={generatedData.answerA}
            answerB={generatedData.answerB}
            retrievedExamples={generatedData.retrievedExamples}
            onSelect={handleAnswerSelect}
            onBack={handleReset}
            isSubmitting={isSubmitting}
          />
        )}

        {state === "yolo" && (
          <YoloMode
            databaseId={databaseId}
            systemPrompt={database.systemPrompt ?? undefined}
            onSelectAnswer={handleYoloSelect}
            onExit={exitYoloMode}
          />
        )}
      </>
    );
  }

  if (tab === "memory") {
    return <ExamplesList databaseId={databaseId} />;
  }

  if (tab === "settings") {
    return <SystemPromptEditor databaseId={databaseId} />;
  }

  return null;
}
