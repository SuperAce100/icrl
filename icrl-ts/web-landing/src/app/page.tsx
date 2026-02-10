import { ArrowUpRight, BookOpen, Database, Eye, PenSquare, Rocket, Sparkles, Target } from "lucide-react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const highlights = [
  {
    title: "Instant Learning Loop",
    body: "Every successful trajectory is immediately reusable context for future tasks.",
    icon: PenSquare,
    featured: true,
  },
  {
    title: "Reliable Inference",
    body: "Improve output quality without waiting on heavyweight retraining cycles.",
    icon: Eye,
    featured: false,
  },
];

const benefits = [
  {
    title: "Ship faster",
    body: "Agent quality improves while your product is in use, not only after model retraining.",
  },
  {
    title: "Lower complexity",
    body: "Use trajectory memory and retrieval instead of a full RL pipeline and training infra.",
  },
  {
    title: "Higher relevance",
    body: "Examples come from your own successful runs, so guidance matches your real tasks.",
  },
];

const useCases = [
  "Support and operations agents that solve repeated workflows",
  "Coding and DevOps copilots with recurring command and fix patterns",
  "SQL and data assistants in iterative query-and-feedback tasks",
  "Browser and API automation where successful flows repeat",
];

const benchmarkRows = [
  { name: "ALFWorld", result: "73% → 93%" },
  { name: "InterCode-SQL", result: "75% → 82%" },
  { name: "Wordcraft", result: "55% → 72%" },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <SiteHeader />

      <section className="mx-auto max-w-6xl px-6 pb-16 pt-16 md:pt-24">
        <div className="max-w-4xl space-y-6">
          <h1 className="text-balance font-mono text-4xl font-semibold leading-tight tracking-tight text-foreground sm:text-5xl md:text-6xl">
            ICRL turns successful agent runs into immediate reinforcement.
          </h1>
          <p className="max-w-3xl font-mono text-xl leading-relaxed text-muted-foreground">
            Build self-improving LLM agents in production. ICRL stores successful trajectories, retrieves them at the
            right decision points, and improves behavior on the next related task.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <a href="#get-started">
                Get started
                <Rocket className="size-4" />
              </a>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                <BookOpen className="size-4" />
                Read paper
              </a>
            </Button>
          </div>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {highlights.map((item) => (
            <Card
              key={item.title}
              className={
                item.featured
                  ? "border-primary bg-card shadow-none"
                  : "border-border/70 bg-card/80 text-foreground shadow-none"
              }
            >
              <CardHeader className="flex-row items-start justify-between gap-4">
                <item.icon className="size-8 text-primary" />
                <ArrowUpRight className="size-6 text-muted-foreground" />
              </CardHeader>
              <CardContent className="space-y-3">
                <CardTitle className="font-mono text-4xl font-semibold leading-none tracking-tight text-foreground">
                  {item.title}
                </CardTitle>
                <p className="font-mono text-xl leading-relaxed text-muted-foreground">{item.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="why" className="mx-auto max-w-6xl px-6 py-4">
        <div className="grid gap-6 md:grid-cols-3">
          {benefits.map((item) => (
            <Card key={item.title} className="border-border/70 bg-card/80 shadow-none">
              <CardHeader>
                <CardTitle className="font-mono text-3xl font-semibold leading-tight tracking-tight text-foreground">
                  {item.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-xl leading-relaxed text-muted-foreground">{item.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="use-cases" className="mx-auto max-w-6xl px-6 py-12">
        <div className="space-y-6">
          <h2 className="font-mono text-4xl font-semibold tracking-tight text-foreground">Use cases where ICRL wins</h2>
          <Card className="border-border/70 bg-card/80 shadow-none">
            <CardContent className="pt-6">
              <ul className="grid gap-4 md:grid-cols-2">
                {useCases.map((item) => (
                  <li key={item} className="font-mono text-xl leading-relaxed text-muted-foreground">
                    {item}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-4">
        <div className="grid gap-6 md:grid-cols-[1.2fr_0.8fr]">
          <Card className="border-border/70 bg-card/80 shadow-none">
            <CardHeader>
              <CardTitle className="font-mono text-4xl font-semibold tracking-tight text-foreground">
                Why ICRL over traditional RL
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="font-mono text-xl text-muted-foreground">
                Traditional RL pipelines optimize weights over training cycles. ICRL improves behavior through
                retrieval-ready memory, making reinforcement immediate and operationally simpler.
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="bg-muted/60 p-4 font-mono text-xl text-muted-foreground">No retraining lag</div>
                <div className="bg-muted/60 p-4 font-mono text-xl text-muted-foreground">No policy pipeline overhead</div>
                <div className="bg-muted/60 p-4 font-mono text-xl text-muted-foreground">Grounded in real successful runs</div>
                <div className="bg-muted/60 p-4 font-mono text-xl text-muted-foreground">Works with existing model APIs</div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/80 shadow-none">
            <CardHeader>
              <CardTitle className="font-mono text-3xl font-semibold tracking-tight text-foreground">
                Reported gains
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {benchmarkRows.map((row) => (
                <div key={row.name} className="space-y-1">
                  <p className="font-mono text-xl font-semibold text-foreground">{row.name}</p>
                  <p className="font-mono text-xl text-muted-foreground">{row.result}</p>
                </div>
              ))}
              <p className="pt-2 font-mono text-sm text-muted-foreground">Source: arXiv:2505.00234</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section id="get-started" className="mx-auto max-w-6xl px-6 pb-20 pt-12">
        <Card className="border-primary bg-card shadow-none">
          <CardHeader>
            <CardTitle className="font-mono text-4xl font-semibold tracking-tight text-foreground">Start building with ICRL</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <pre className="overflow-x-auto bg-stone-950 p-4 font-mono text-sm leading-relaxed text-stone-100">
{`npm install icrl
npm install openai`}
            </pre>
            <div className="flex flex-wrap items-center gap-3">
              <Button asChild>
                <a href="https://github.com/SuperAce100/icrl/tree/main/icrl-ts" target="_blank" rel="noreferrer noopener">
                  <Database className="size-4" />
                  View TypeScript package
                </a>
              </Button>
              <Button asChild variant="ghost">
                <a href="/docs">
                  <Sparkles className="size-4" />
                  Open docs
                </a>
              </Button>
              <Button asChild variant="ghost">
                <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                  <Target className="size-4" />
                  Paper
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      <SiteFooter />
    </main>
  );
}
