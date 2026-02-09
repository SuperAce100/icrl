"use client";

import { ArrowRight, Bolt, BookOpen, Bot, CheckCircle2, Database, GitBranch, Layers, Rocket, Target } from "lucide-react";
import { GrainGradient } from "@paper-design/shaders-react";

import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/site-footer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const reasons = [
  {
    title: "Instant self-improvement",
    detail:
      "A successful run can become a retrieval example immediately, so the next similar task can benefit right away.",
    icon: Bolt,
  },
  {
    title: "No gradient training loop",
    detail:
      "ICRL improves through trajectory memory and retrieval quality, without policy gradients, reward models, or offline RL pipelines.",
    icon: GitBranch,
  },
  {
    title: "Better outputs with real usage",
    detail:
      "The package gets stronger on your actual tasks because it keeps successful trajectories from your own environment.",
    icon: Database,
  },
];

const useCases = [
  {
    title: "Support and ops agents",
    detail: "Agents that repeatedly handle tickets or workflows can improve after each solved case.",
    icon: Bot,
  },
  {
    title: "Code and DevOps copilots",
    detail: "Tool-using coding agents can reuse successful plans and command sequences across related tasks.",
    icon: Layers,
  },
  {
    title: "SQL and data assistants",
    detail: "Interactive query tasks benefit from remembered successful reasoning and action trajectories.",
    icon: Target,
  },
  {
    title: "Browser and workflow automation",
    detail: "Multi-step web flows can adapt quickly as successful trajectories accumulate over time.",
    icon: Rocket,
  },
];

const resultRows = [
  { benchmark: "ALFWorld", fixed: "73%", traj: "89%", best: "93%" },
  { benchmark: "InterCode-SQL", fixed: "75%", traj: "79%", best: "82%" },
  { benchmark: "Wordcraft", fixed: "55%", traj: "64%", best: "72%" },
];

function Background() {
  return (
    <div className="fixed inset-0 -z-10">
      <GrainGradient
        style={{ width: "100%", height: "100%" }}
        colors={["#ffedd6", "#ffe7c0", "#fff3dc"]}
        colorBack="#fafaf9"
        softness={0.74}
        intensity={0.1}
        noise={0.45}
        shape="wave"
        speed={0.82}
        scale={1.15}
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

      <section className="mx-auto max-w-6xl px-6 pb-14 pt-20 md:pt-28">
        <div className="mx-auto max-w-4xl space-y-7 text-center">
          <Badge variant="secondary" className="rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em]">
            TypeScript Package · npm install icrl
          </Badge>
          <h1 className="text-balance text-4xl font-semibold leading-tight tracking-tight sm:text-5xl md:text-6xl">
            ICRL gives your agent instant reinforcement learning through memory.
          </h1>
          <p className="mx-auto max-w-3xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            ICRL is the production implementation of the self-improving trajectory bootstrapping approach. When your agent
            succeeds, ICRL stores that trajectory and immediately turns it into in-context training signal for future tasks.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg" className="rounded-full px-6">
              <a href="#get-started">
                Start with ICRL
                <ArrowRight className="size-4" />
              </a>
            </Button>
            <Button asChild size="lg" variant="outline" className="rounded-full px-6">
              <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                Read the paper
              </a>
            </Button>
          </div>
        </div>
      </section>

      <section id="why" className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <CheckCircle2 className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Why teams use ICRL</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {reasons.map((item) => (
            <Card key={item.title} className="border-border/70">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <item.icon className="size-5 text-primary" />
                  {item.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-muted-foreground">{item.detail}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="mt-5 border-primary/25 bg-card/90">
          <CardHeader>
            <CardTitle className="text-xl">What &quot;instant reinforcement learning&quot; means in ICRL</CardTitle>
            <CardDescription>
              Not gradient updates. Immediate reinforcement happens by turning successful episodes into reusable context.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-xl border border-border/70 bg-stone-950 p-4 text-xs leading-relaxed text-stone-100 sm:text-sm">
{`const trajectory = await agent.train(env, goal)

if (trajectory.success) {
  // stored now, retrievable on the very next task
  // so success signal is applied immediately
}

const result = await agent.run(env, nextGoal)`}
            </pre>
          </CardContent>
        </Card>
      </section>

      <section id="use-cases" className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <Bot className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Use cases for immediate self-improvement</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {useCases.map((item) => (
            <Card key={item.title} className="border-border/70">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <item.icon className="size-5 text-primary" />
                  {item.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-muted-foreground">{item.detail}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="vs-rl" className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <GitBranch className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Why ICRL over traditional RL for LLM agents</h2>
        </div>

        <Card className="border-border/70">
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-sm">
                <thead>
                  <tr className="border-b border-border/70 text-left text-muted-foreground">
                    <th className="py-3 pr-4 font-medium">Dimension</th>
                    <th className="py-3 pr-4 font-medium">Traditional RL Pipelines</th>
                    <th className="py-3 pr-4 font-medium">ICRL</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border/50">
                    <td className="py-3 pr-4 font-medium">Feedback usage</td>
                    <td className="py-3 pr-4 text-muted-foreground">Used for weight updates during training cycles</td>
                    <td className="py-3 pr-4 text-muted-foreground">Used as trajectory memory for immediate in-context reuse</td>
                  </tr>
                  <tr className="border-b border-border/50">
                    <td className="py-3 pr-4 font-medium">Infra complexity</td>
                    <td className="py-3 pr-4 text-muted-foreground">Reward models, rollouts, tuning loops, retraining</td>
                    <td className="py-3 pr-4 text-muted-foreground">Trajectory DB + retrieval + your existing model API</td>
                  </tr>
                  <tr className="border-b border-border/50">
                    <td className="py-3 pr-4 font-medium">Update latency</td>
                    <td className="py-3 pr-4 text-muted-foreground">Often delayed until next training run</td>
                    <td className="py-3 pr-4 text-muted-foreground">Near-immediate after successful episodes</td>
                  </tr>
                  <tr>
                    <td className="py-3 pr-4 font-medium">Best fit</td>
                    <td className="py-3 pr-4 text-muted-foreground">When you need full policy optimization and can afford RL infra</td>
                    <td className="py-3 pr-4 text-muted-foreground">When you want fast, practical self-improvement in tool-using agents</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="mb-6 flex items-center gap-2">
          <BookOpen className="size-5 text-primary" />
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Evidence from the paper</h2>
        </div>
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="text-xl">Reported benchmark gains</CardTitle>
            <CardDescription>
              From &quot;Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks&quot;.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[620px] text-sm">
                <thead>
                  <tr className="border-b border-border/70 text-left text-muted-foreground">
                    <th className="py-3 pr-4 font-medium">Benchmark</th>
                    <th className="py-3 pr-4 font-medium">Fixed-DB</th>
                    <th className="py-3 pr-4 font-medium">Traj-Bootstrap</th>
                    <th className="py-3 pr-4 font-medium">Best curated</th>
                  </tr>
                </thead>
                <tbody>
                  {resultRows.map((row) => (
                    <tr key={row.benchmark} className="border-b border-border/50 last:border-0">
                      <td className="py-3 pr-4 font-medium">{row.benchmark}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{row.fixed}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{row.traj}</td>
                      <td className="py-3 pr-4 text-primary">{row.best}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4">
              <a
                className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                href="https://arxiv.org/abs/2505.00234"
                target="_blank"
                rel="noreferrer noopener"
              >
                Open original paper
                <ArrowRight className="size-4" />
              </a>
            </div>
          </CardContent>
        </Card>
      </section>

      <section id="get-started" className="mx-auto max-w-6xl px-6 pb-24 pt-10 md:pt-14">
        <Card className="border-primary/25 bg-card/90">
          <CardHeader>
            <CardTitle className="text-2xl tracking-tight">Get started with ICRL</CardTitle>
            <CardDescription>
              Install the package, connect your model provider, and start storing successful trajectories.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <pre className="overflow-x-auto rounded-xl border border-border/70 bg-stone-950 p-4 text-xs leading-relaxed text-stone-100 sm:text-sm">
{`npm install icrl
npm install openai`}
            </pre>
            <p className="text-sm text-muted-foreground">
              ICRL is designed for teams that want reinforcement-style improvement now, without waiting for heavyweight RL training cycles.
            </p>
          </CardContent>
        </Card>
      </section>

      <SiteFooter />
    </main>
  );
}
