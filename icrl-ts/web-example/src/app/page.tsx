"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { ApiStatusBanner } from "@/components/api-status-banner";
import { TrainHero } from "@/components/train-hero";
import { HowItWorks } from "@/components/how-it-works";
import { YoloModeBanner } from "@/components/yolo-mode-banner";
import { DatabaseSelector } from "@/components/database-selector";
import { QuestionInput } from "@/components/question-input";
import { AnswerChoice } from "@/components/answer-choice";
import { ExamplesList } from "@/components/examples-list";
import { SystemPromptEditor } from "@/components/system-prompt-editor";
import { YoloMode } from "@/components/yolo-mode";
import { generateAnswers, checkApiStatus, searchSimilarExamples } from "@/lib/actions";
import { Sparkles, Database, Settings } from "lucide-react";
import type { Id } from "../../convex/_generated/dataModel";

type AppState = "input" | "choosing" | "yolo";

interface GeneratedData {
  question: string;
  answerA: string;
  answerB: string;
  retrievedExamples: Array<{ question: string; chosenAnswer: string }>;
}

export default function Home() {
  const [selectedDbId, setSelectedDbId] = useState<Id<"databases"> | null>(null);
  const [state, setState] = useState<AppState>("input");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedData, setGeneratedData] = useState<GeneratedData | null>(null);
  const [apiStatus, setApiStatus] = useState<{
    configured: boolean;
    message: string;
  } | null>(null);

  // Convex queries and mutations
  const databases = useQuery(api.databases.list);
  const selectedDb = useQuery(api.databases.get, selectedDbId ? { id: selectedDbId } : "skip");
  const createExample = useMutation(api.examples.create);

  // Auto-select first database
  useEffect(() => {
    if (databases && databases.length > 0 && !selectedDbId) {
      setSelectedDbId(databases[0]._id);
    }
  }, [databases, selectedDbId]);

  // Check API status on mount
  useEffect(() => {
    checkApiStatus().then(setApiStatus);
  }, []);

  const handleQuestionSubmit = async (question: string) => {
    if (!selectedDbId) return;

    setIsLoading(true);
    try {
      const retrievedExamples = await searchSimilarExamples(selectedDbId, question, 3);
      const { answerA, answerB } = await generateAnswers(
        question,
        retrievedExamples,
        selectedDb?.systemPrompt ?? undefined
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
    if (!selectedDbId || !generatedData) return;

    setIsSubmitting(true);
    try {
      await createExample({
        databaseId: selectedDbId,
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
    if (!selectedDbId) return;

    await createExample({
      databaseId: selectedDbId,
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

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header />

      {apiStatus && !apiStatus.configured && <ApiStatusBanner message={apiStatus.message} />}

      {/* Database Selector */}
      <div className="border-b border-border/50 bg-muted/30">
        <div className="max-w-6xl mx-auto px-6 py-3">
          <DatabaseSelector selectedId={selectedDbId} onSelect={setSelectedDbId} />
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8 flex-1 w-full">
        {!selectedDbId ? (
          <Alert>
            <Database className="h-4 w-4" />
            <AlertTitle>No Database Selected</AlertTitle>
            <AlertDescription>
              Create or select a database to get started. Each database stores its own examples and
              system prompt.
            </AlertDescription>
          </Alert>
        ) : (
          <Tabs defaultValue="ask" className="space-y-8">
            <TabsList className="grid w-full max-w-md grid-cols-3 mx-auto">
              <TabsTrigger
                value="ask"
                className="flex items-center gap-2 data-[state=active]:text-primary"
              >
                <Sparkles className="h-4 w-4" />
                Train
              </TabsTrigger>
              <TabsTrigger
                value="database"
                className="flex items-center gap-2 data-[state=active]:text-primary"
              >
                <Database className="h-4 w-4" />
                Memory
              </TabsTrigger>
              <TabsTrigger
                value="settings"
                className="flex items-center gap-2 data-[state=active]:text-primary"
              >
                <Settings className="h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>

            {/* Train Tab */}
            <TabsContent value="ask" className="space-y-6">
              <div className="w-full">
                {state === "input" && (
                  <div className="mb-8 space-y-6">
                    <TrainHero />
                    <HowItWorks />
                    <YoloModeBanner onStart={enterYoloMode} />
                  </div>
                )}

                {state === "input" && (
                  <QuestionInput
                    databaseId={selectedDbId}
                    onSubmit={handleQuestionSubmit}
                    isLoading={isLoading}
                    disabled={!selectedDbId}
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

                {state === "yolo" && selectedDbId && (
                  <YoloMode
                    databaseId={selectedDbId}
                    systemPrompt={selectedDb?.systemPrompt ?? undefined}
                    onSelectAnswer={handleYoloSelect}
                    onExit={exitYoloMode}
                  />
                )}
              </div>
            </TabsContent>

            {/* Memory Tab */}
            <TabsContent value="database">
              <ExamplesList databaseId={selectedDbId} />
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings">
              <SystemPromptEditor databaseId={selectedDbId} />
            </TabsContent>
          </Tabs>
        )}
      </div>

      <Footer />
    </main>
  );
}
