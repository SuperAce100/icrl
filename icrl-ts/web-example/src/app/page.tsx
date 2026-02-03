"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { DatabaseSelector } from "@/components/database-selector";
import { QuestionInput } from "@/components/question-input";
import { AnswerChoice } from "@/components/answer-choice";
import { ExamplesList } from "@/components/examples-list";
import { SystemPromptEditor } from "@/components/system-prompt-editor";
import { YoloMode } from "@/components/yolo-mode";
import { generateAnswers, checkApiStatus, searchSimilarExamples } from "@/lib/actions";
import { Sparkles, Database, Settings, AlertTriangle, Github, Zap } from "lucide-react";
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
      // Retrieve similar examples from the database (increments their retrieval count)
      const retrievedExamples = await searchSimilarExamples(
        selectedDbId,
        question,
        3 // Retrieve up to 3 similar examples
      );

      const { answerA, answerB } = await generateAnswers(
        question,
        retrievedExamples,
        selectedDb?.systemPrompt ?? undefined
      );

      setGeneratedData({
        question,
        answerA,
        answerB,
        retrievedExamples,
      });
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

      // Go straight back to input screen
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

  // YOLO mode: handle answer selection from auto-generated prompts
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
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <span>ICRL</span>
                <span className="text-muted-foreground font-normal">Demo</span>
              </h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                In-Context Reinforcement Learning with Human Feedback
              </p>
            </div>
            <a
              href="https://github.com/SuperAce100/icrl"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <Github className="h-5 w-5" />
            </a>
          </div>
        </div>
      </header>

      {/* API Status Banner */}
      {apiStatus && !apiStatus.configured && (
        <div className="bg-yellow-500/10 border-b border-yellow-500/20">
          <div className="max-w-5xl mx-auto px-4 py-2">
            <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
              <AlertTriangle className="h-4 w-4" />
              <span>{apiStatus.message}</span>
            </div>
          </div>
        </div>
      )}

      {/* Database Selector */}
      <div className="border-b">
        <div className="max-w-5xl mx-auto px-4 py-3">
          <DatabaseSelector selectedId={selectedDbId} onSelect={setSelectedDbId} />
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 py-6">
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
          <Tabs defaultValue="ask" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="ask" className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Ask & Train
              </TabsTrigger>
              <TabsTrigger value="database" className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                Database
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>

            {/* Ask & Train Tab */}
            <TabsContent value="ask" className="space-y-4">
              <div className="max-w-2xl mx-auto">
                {/* How it works + YOLO mode button */}
                {state === "input" && (
                  <div className="mb-6 space-y-4">
                    <div className="bg-muted/50 rounded-lg p-4 border">
                      <h2 className="text-sm font-medium mb-2">How it works:</h2>
                      <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                        <li>Enter a prompt (or use AI suggestions)</li>
                        <li>The system retrieves similar examples from the database</li>
                        <li>Two answer options are generated (influenced by examples)</li>
                        <li>You choose the better answer (or write your own)</li>
                        <li>Your choice is stored and improves future answers</li>
                      </ol>
                    </div>

                    {/* YOLO Mode Banner */}
                    <div className="bg-linear-to-r from-yellow-500/10 to-orange-500/10 rounded-lg p-4 border border-yellow-500/30">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-full bg-yellow-500/20">
                            <Zap className="h-5 w-5 text-yellow-500" />
                          </div>
                          <div>
                            <h3 className="text-sm font-medium">YOLO Mode</h3>
                            <p className="text-xs text-muted-foreground">
                              Let AI generate both prompts and answers. Just pick your preference!
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={enterYoloMode}
                          className="border-yellow-500/50 hover:bg-yellow-500/10"
                        >
                          <Zap className="h-4 w-4 mr-1 text-yellow-500" />
                          Start YOLO
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Main content based on state */}
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

            {/* Database Tab */}
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

      {/* Footer */}
      <footer className="border-t mt-auto">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <p className="text-center text-xs text-muted-foreground">
            Built with{" "}
            <a href="https://github.com/SuperAce100/icrl" className="text-primary hover:underline">
              ICRL
            </a>{" "}
            &bull; In-Context Reinforcement Learning for LLM Agents
          </p>
        </div>
      </footer>
    </main>
  );
}
