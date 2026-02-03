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
import { Sparkles, Database, Settings, AlertTriangle, Github, Zap, BookOpen } from "lucide-react";
import Image from "next/image";
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
      <header className="border-b border-border/50 bg-card/80 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Image
                src="/logo_light.png"
                alt="ICRL"
                width={40}
                height={40}
                className="dark:hidden"
              />
              <Image
                src="/logo_dark.png"
                alt="ICRL"
                width={40}
                height={40}
                className="hidden dark:block"
              />
              <div>
                <h1 className="text-xl font-semibold tracking-tight">
                  <span className="text-primary">ICRL</span>
                  <span className="text-muted-foreground font-normal ml-2">Playground</span>
                </h1>
                <p className="text-xs text-muted-foreground">In-Context Reinforcement Learning</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <a
                href="https://icrl.mintlify.app"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted"
              >
                <BookOpen className="h-4 w-4" />
                <span className="hidden sm:inline">Docs</span>
              </a>
              <a
                href="https://github.com/SuperAce100/icrl"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted"
              >
                <Github className="h-4 w-4" />
                <span className="hidden sm:inline">GitHub</span>
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* API Status Banner */}
      {apiStatus && !apiStatus.configured && (
        <div className="bg-primary/5 border-b border-primary/20">
          <div className="max-w-6xl mx-auto px-6 py-2">
            <div className="flex items-center gap-2 text-sm text-primary">
              <AlertTriangle className="h-4 w-4" />
              <span>{apiStatus.message}</span>
            </div>
          </div>
        </div>
      )}

      {/* Database Selector */}
      <div className="border-b border-border/50 bg-muted/30">
        <div className="max-w-6xl mx-auto px-6 py-3">
          <DatabaseSelector selectedId={selectedDbId} onSelect={setSelectedDbId} />
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
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

            {/* Ask & Train Tab */}
            <TabsContent value="ask" className="space-y-6">
              <div className="w-full">
                {/* How it works + YOLO mode button */}
                {state === "input" && (
                  <div className="mb-8 space-y-6">
                    {/* Hero Section */}
                    <div className="text-center space-y-3 mb-8">
                      <h2 className="text-2xl font-semibold tracking-tight">Train Your AI</h2>
                      <p className="text-muted-foreground max-w-xl mx-auto">
                        Ask questions and choose the best answers. Your preferences are stored and
                        used to improve future responses.
                      </p>
                    </div>

                    {/* How it works */}
                    <div className="bg-card rounded-xl p-6 border shadow-sm">
                      <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">
                        How it works
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                        <div className="flex flex-col items-center text-center p-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold mb-2">
                            1
                          </div>
                          <p className="text-sm">Enter a prompt</p>
                        </div>
                        <div className="flex flex-col items-center text-center p-3">
                          <div className="w-10 h-10 rounded-full bg-icrl-blue/10 flex items-center justify-center text-icrl-blue font-semibold mb-2">
                            2
                          </div>
                          <p className="text-sm">Retrieve examples</p>
                        </div>
                        <div className="flex flex-col items-center text-center p-3">
                          <div className="w-10 h-10 rounded-full bg-icrl-yellow/30 flex items-center justify-center text-icrl-stone-dark font-semibold mb-2">
                            3
                          </div>
                          <p className="text-sm">Generate options</p>
                        </div>
                        <div className="flex flex-col items-center text-center p-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold mb-2">
                            4
                          </div>
                          <p className="text-sm">Choose the best</p>
                        </div>
                        <div className="flex flex-col items-center text-center p-3">
                          <div className="w-10 h-10 rounded-full bg-icrl-blue/10 flex items-center justify-center text-icrl-blue font-semibold mb-2">
                            5
                          </div>
                          <p className="text-sm">Store & learn</p>
                        </div>
                      </div>
                    </div>

                    {/* YOLO Mode Banner */}
                    <div className="bg-linear-to-r from-primary/10 via-primary/5 to-icrl-yellow/10 rounded-xl p-6 border border-primary/20">
                      <div className="flex items-center justify-between flex-wrap gap-4">
                        <div className="flex items-center gap-4">
                          <div className="p-3 rounded-xl bg-primary/20">
                            <Zap className="h-6 w-6 text-primary" />
                          </div>
                          <div>
                            <h3 className="font-semibold">YOLO Mode</h3>
                            <p className="text-sm text-muted-foreground">
                              Let AI generate prompts and answers. Just pick your preference!
                            </p>
                          </div>
                        </div>
                        <Button
                          onClick={enterYoloMode}
                          className="bg-primary hover:bg-primary/90 text-white"
                        >
                          <Zap className="h-4 w-4 mr-2" />
                          Start YOLO Mode
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
