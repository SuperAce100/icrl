"use client";

import {
  ArrowRight,
  BookOpen,
  Bot,
  Braces,
  ChartColumnBig,
  CheckCircle2,
  Database,
  Gauge,
  GitBranch,
  Layers,
  Rocket,
  Target,
  Zap,
} from "lucide-react";
import { GrainGradient } from "@paper-design/shaders-react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const loopSteps = [
  {
    title: "Attempt",
    description: "Run the task in your real environment with your current prompts and tools.",
  },
  {
    title: "Store Success",
    description: "Successful trajectories are written to memory with plan, reasoning, and actions.",
  },
  {
    title: "Retrieve",
    description: "Next task pulls the most relevant successful trajectories as in-context examples.",
  },
  {
    title: "Improve",
    description: "Agent quality rises immediately through better context, no model retraining required.",
  },
];

const useCases = [
  {
    title: "Ops and support agents",
    description: "Every resolved case becomes a reusable playbook for the next similar ticket.",
    icon: Bot,
  },
  {
    title: "Coding and DevOps copilots",
    description: "Tool-call sequences that worked once become high-signal context on subsequent tasks.",
    icon: Braces,
  },
  {
    title: "SQL and data agents",
    description: "Successful exploratory query patterns get reused for faster, more reliable answers.",
    icon: Target,
  },
  {
    title: "Workflow automation",
    description: "Multi-step browser and API flows get better as successful trajectories accumulate.",
    icon: Rocket,
  },
];

const compareRows = [
  {
    dimension: "How feedback is applied",
    rl: "Used for policy updates across training jobs",
    icrl: "Converted into memory that can help the very next task",
  },
  {
    dimension: "Operational overhead",
    rl: "Rollouts, reward tuning, training infrastructure",
    icrl: "Trajectory DB, retrieval, and your existing LLM API",
  },
  {
    dimension: "Time to benefit",
    rl: "Usually delayed until retraining",
    icrl: "Immediate after successful episodes",
  },
  {
    dimension: "Best fit",
    rl: "Full policy optimization at large scale",
    icrl: "Fast self-improvement for practical tool-using agents",
  },
];

const benchmarks = [
  { name: "ALFWorld", fixed: 73, traj: 89, best: 93 },
  { name: "InterCode-SQL", fixed: 75, traj: 79, best: 82 },
  { name: "Wordcraft", fixed: 55, traj: 64, best: 72 },
];

function Background() {
  return (
    <div className="fixed inset-0 -z-10">
      <GrainGradient
        style={{ width: "100%", height: "100%" }}
        colors={["#ffedd6", "#ffe7c0", "#fff3dc"]}
        colorBack="#fafaf9"
        softness={0.72}
        intensity={0.11}
        noise={0.48}
        shape="wave"
        speed={0.88}
        scale={1.16}
      />
      <div className="page-grid absolute inset-0" />
    </div>
  );
}

export default function LandingPage() {
  return (
    <main className="relative min-h-screen soft-noise">
      <Background />
      <SiteHeader />

      <section className="mx-auto max-w-6xl px-6 pb-14 pt-18 md:pt-24">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6 stagger">
            <Badge variant="secondary" className="rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em]">
              ICRL TypeScript Package
            </Badge>
            <h1 className="text-balance text-4xl font-semibold leading-tight tracking-tight sm:text-5xl md:text-[3.4rem]">
              Instant reinforcement learning for LLM agents.
            </h1>
            <p className="max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
              ICRL turns successful trajectories into immediate in-context training signal. Your agent improves while it works,
              not after a long retraining cycle.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Button asChild size="lg" className="rounded-full px-6">
                <a href="#get-started">
                  Start with ICRL
                  <ArrowRight className="size-4" />
                </a>
              </Button>
              <Button asChild size="lg" variant="outline" className="rounded-full px-6">
                <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                  Original paper
                </a>
              </Button>
            </div>
          </div>

          <Card className="stagger border-primary/25 bg-card/95" data-delay="1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="size-4 text-primary" />
                Immediate Value Loop
              </CardTitle>
              <CardDescription>
                One successful run can strengthen the next related run in the same session.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {loopSteps.map((step, index) => (
                <div key={step.title} className="glow-line rounded-xl border border-border/70 bg-background/80 px-4 py-3 pl-5">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Step {index + 1}</p>
                  <p className="mt-1 text-sm font-medium">{step.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{step.description}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>

      <section id="why" className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Card className="stagger h-fit border-border/80" data-delay="1">
            <CardHeader>
              <CardTitle className="text-2xl tracking-tight">Why ICRL</CardTitle>
              <CardDescription>
                It is built for teams that need measurable agent improvement without RL infrastructure overhead.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
                Better outcomes through trajectory quality and retrieval relevance.
              </p>
              <p className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
                No policy-gradient training loop required to improve behavior.
              </p>
              <p className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
                Improvement signal comes from real production-like task completions.
              </p>
            </CardContent>
          </Card>

          <Card className="stagger border-primary/20" data-delay="2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <Gauge className="size-5 text-primary" />
                Instant reinforcement in practice
              </CardTitle>
              <CardDescription>
                In ICRL, reinforcement happens through memory updates. The next call can already benefit.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="overflow-x-auto rounded-xl border border-border/70 bg-stone-950 p-4 text-xs leading-relaxed text-stone-100 sm:text-sm">
{`const trajectory = await agent.train(env, goal)

if (trajectory.success) {
  // stored now
  // available for retrieval on the next similar task
}

const next = await agent.run(env, nextGoal)`}
              </pre>
            </CardContent>
          </Card>
        </div>
      </section>

      <section id="use-cases" className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <Layers className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Where instant self-improvement matters</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {useCases.map((item, index) => (
            <Card key={item.title} className="stagger border-border/70" data-delay={String((index % 3) + 1)}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <item.icon className="size-5 text-primary" />
                  {item.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-muted-foreground">{item.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="vs-rl" className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <GitBranch className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">ICRL vs Traditional RL</h2>
        </div>
        <Card className="border-border/70">
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[690px] text-sm">
                <thead>
                  <tr className="border-b border-border/70 text-left text-muted-foreground">
                    <th className="py-3 pr-4 font-medium">Dimension</th>
                    <th className="py-3 pr-4 font-medium">Traditional RL pipelines</th>
                    <th className="py-3 pr-4 font-medium">ICRL</th>
                  </tr>
                </thead>
                <tbody>
                  {compareRows.map((row) => (
                    <tr key={row.dimension} className="border-b border-border/50 last:border-0">
                      <td className="py-3 pr-4 font-medium">{row.dimension}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{row.rl}</td>
                      <td className="py-3 pr-4 text-foreground">{row.icrl}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <ChartColumnBig className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Evidence behind the concept</h2>
        </div>
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="text-xl">Reported benchmark gains</CardTitle>
            <CardDescription>
              From the paper &quot;Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks&quot;.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {benchmarks.map((row) => (
              <div key={row.name} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <p className="font-medium">{row.name}</p>
                  <p className="text-muted-foreground">
                    {row.fixed}% to {row.best}%
                  </p>
                </div>
                <div className="grid gap-2">
                  <div className="h-2 rounded-full bg-secondary">
                    <div className="h-2 rounded-full bg-muted-foreground/60" style={{ width: `${row.fixed}%` }} />
                  </div>
                  <div className="h-2 rounded-full bg-secondary">
                    <div className="h-2 rounded-full bg-primary/75" style={{ width: `${row.traj}%` }} />
                  </div>
                  <div className="h-2 rounded-full bg-secondary">
                    <div className="h-2 rounded-full bg-primary" style={{ width: `${row.best}%` }} />
                  </div>
                </div>
              </div>
            ))}
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1"><span className="size-2 rounded-full bg-muted-foreground/60" />Fixed-DB</span>
              <span className="inline-flex items-center gap-1"><span className="size-2 rounded-full bg-primary/75" />Traj-Bootstrap</span>
              <span className="inline-flex items-center gap-1"><span className="size-2 rounded-full bg-primary" />Best curated variant</span>
            </div>
            <Button asChild variant="outline" className="w-fit rounded-full px-5">
              <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                <BookOpen className="size-4" />
                Read the original paper
              </a>
            </Button>
          </CardContent>
        </Card>
      </section>

      <section id="get-started" className="mx-auto max-w-6xl px-6 pb-24 pt-10 md:pt-14">
        <Card className="border-primary/30 bg-card">
          <CardHeader>
            <CardTitle className="text-2xl tracking-tight">Get started with ICRL</CardTitle>
            <CardDescription>
              Connect your model provider, run training episodes, and let successful trajectories improve the next task.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <pre className="overflow-x-auto rounded-xl border border-border/70 bg-stone-950 p-4 text-xs leading-relaxed text-stone-100 sm:text-sm">
{`npm install icrl
npm install openai`}
            </pre>
            <div className="flex flex-wrap items-center gap-3">
              <Button asChild className="rounded-full px-5">
                <a href="https://github.com/SuperAce100/icrl/tree/main/icrl-ts" target="_blank" rel="noreferrer noopener">
                  <Database className="size-4" />
                  View TypeScript package
                </a>
              </Button>
              <Button asChild variant="ghost" className="rounded-full px-5">
                <a href="https://icrl.mintlify.app" target="_blank" rel="noreferrer noopener">
                  Docs
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
