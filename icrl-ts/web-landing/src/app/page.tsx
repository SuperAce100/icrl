import type { Metadata } from "next";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Bot,
  CheckCircle2,
  Code2,
  Database,
  Globe,
  Home,
  MessageSquare,
  PenLine,
  Terminal,
  ThumbsUp,
} from "lucide-react";

import { CopyableInstallSnippet } from "@/components/copyable-install-snippet";
import { InstallLinks } from "@/components/install-links";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "ICRL — In-Context Reinforcement Learning for LLM Agents",
  description:
    "ICRL is a trajectory-learning framework that lets LLM agents improve continuously at runtime. Store successful trajectories, retrieve by goal and step, and curate over time — no retraining required.",
  alternates: {
    canonical: "https://icrl.dev",
  },
};

const jsonLd = [
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "ICRL",
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Cross-platform",
    description:
      "A trajectory-learning framework that lets LLM agents improve continuously at runtime without retraining.",
    url: "https://icrl.dev",
    downloadUrl: "https://www.npmjs.com/package/icrl",
    softwareVersion: "0.1.0",
    author: {
      "@type": "Organization",
      name: "Stanford Graphics Lab",
      url: "https://graphics.stanford.edu",
    },
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    keywords:
      "ICRL, in-context reinforcement learning, LLM agents, trajectory learning, AI agents, agent memory, continuous learning",
  },
  {
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    headline:
      "Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks",
    url: "https://arxiv.org/abs/2505.00234",
    author: {
      "@type": "Organization",
      name: "Stanford Graphics Lab",
    },
    publisher: {
      "@type": "Organization",
      name: "arXiv",
    },
    about:
      "Research showing that converting successful trajectories into retrieval-time reinforcement improves LLM agent performance on ALFWorld, InterCode-SQL, and Wordcraft benchmarks.",
  },
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "ICRL",
    url: "https://icrl.dev",
    description:
      "ICRL — In-Context Reinforcement Learning for LLM Agents. A trajectory-learning framework for continuous agent improvement without retraining.",
    potentialAction: {
      "@type": "SearchAction",
      target: "https://icrl.dev/docs?q={search_term_string}",
      "query-input": "required name=search_term_string",
    },
  },
];

const GITHUB_BASE = "https://github.com/SuperAce100/icrl/tree/main";

const comparisonRows = [
  {
    dimension: "When it improves",
    icrl: "Immediately, on the next similar task",
    traditional: "After a full retraining cycle",
  },
  {
    dimension: "What changes",
    icrl: "In-context examples (retrieval memory)",
    traditional: "Model weights / policy parameters",
  },
  {
    dimension: "Infrastructure",
    icrl: "Lightweight trajectory DB + retrieval",
    traditional: "GPU training pipelines + eval + rollouts",
  },
  {
    dimension: "Feedback latency",
    icrl: "Instant — same session",
    traditional: "Batch-delayed — hours to days",
  },
  {
    dimension: "Works with frozen models",
    icrl: "Yes — no fine-tuning needed",
    traditional: "No — requires weight updates",
  },
  {
    dimension: "Computational cost",
    icrl: "Minimal — storage + retrieval, no training",
    traditional: "High — full training runs, GPUs, evals",
  },
  {
    dimension: "Interpretability",
    icrl: "Explicit — retrievable examples show what worked",
    traditional: "Implicit — behavior encoded in weights",
  },
];

const useCases = [
  {
    title: "Coding agents",
    detail:
      "Coding workflows and Terminal-Bench style tasks get better from successful trajectories.",
    path: "examples/harbor_coding_agent.py",
    icon: Code2,
  },
  {
    title: "Filesystem / task agents",
    detail:
      "Shell-style environments become more reliable as the agent accumulates experience across repeated goals.",
    path: "examples/file_api_env.py",
    icon: Terminal,
  },
  {
    title: "Support triage",
    detail:
      "Routing and reply quality improve as successful triage outputs are retained and reused.",
    path: "icrl-ts/examples/support-triage-demo.ts",
    icon: Bot,
  },
  {
    title: "Human-in-the-loop workflows",
    detail:
      "Human choices between candidate answers become durable training signals for future retrieval.",
    path: "icrl-ts/web-example",
    icon: Database,
  },
];

const feedbackSignals = [
  {
    icon: ThumbsUp,
    label: "Human preference",
    example: "User picks the best of N candidate outputs",
  },
  {
    icon: CheckCircle2,
    label: "Task success / failure",
    example: "Tests pass, build succeeds, goal reached",
  },
  {
    icon: Code2,
    label: "Code review signals",
    example: "PR approved, changes requested, comments",
  },
  {
    icon: MessageSquare,
    label: "Conversational corrections",
    example: "User edits, rephrases, or overrides the output",
  },
];

export default function LandingPage() {
  return (
    <>
      {jsonLd.map((item, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(item) }}
        />
      ))}
      <main className="min-h-screen bg-background bg-linear-to-b from-background to-primary/20 dark:from-background dark:to-background">
        <SiteHeader />

        <section
          aria-label="Hero"
          className="mx-auto px-6 pb-12 pt-12 md:pt-28 md:pb-28 max-w-2xl space-y-8 text-center"
        >
          <h1 className="font-heading text-4xl  leading-[1.04] tracking-tight text-foreground sm:text-5xl md:text-6xl">
            instant, continuous,
            <br />
            reinforcement learning
            <br />
            for LLM agents
          </h1>
          <p className="mx-auto text-base leading-7 text-muted-foreground sm:text-lg text-balance">
            In-context reinforcement learning improves agents in real time by putting agent&apos;s
            most useful past actions into context for the next task.
          </p>
          <div className="flex flex-wrap justify-center items-center gap-4">
            <CopyableInstallSnippet />
            <Button asChild>
              <a href="/docs">
                <BookOpen className="size-4" />
                Open docs
              </a>
            </Button>
          </div>
        </section>

        {/* ── Bento grid ── */}
        <section aria-label="Features" className="mx-auto max-w-6xl px-6 pb-20">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-12 md:auto-rows-[minmax(190px,auto)]">
            {/* ─── What is ICRL (text-heavy intro) ─── */}
            <Card className="bg-card shadow-none md:col-span-5">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-2xl tracking-tight text-foreground">
                    What is ICRL
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">
                  At LLM scale, traditional reinforcement learning requires retraining the model
                  with every new experience, a very expensive process that doesn&apos;s even work
                  for the closed-source frontier and takes weeks to successfully complete.
                  <span className="font-semibold text-foreground">
                    In-Context Reinforcement Learning (ICRL)
                  </span>{" "}
                  lets LLM agents improve continuously without any post-training work at all. When
                  an agent successfully completes a task, ICRL stores that trajectory, so the next
                  time a similar task comes up, the can will retrieve the most relevant past steps
                  and use them as in-context examples to guide its decisions.
                </p>
                <p className="text-sm leading-6 text-muted-foreground">
                  When the attention mechanism attends to repeated in context examples, it forms
                  what is functionally a LoRA on top of the base model equivalent to a small fine
                  tune on the in context data{" "}
                  <span className="font-semibold text-foreground">1</span>. We see improvements
                  across a wide range of tasks, from coding to support triage to RLHF type tasks{" "}
                  <span className="font-semibold text-foreground">2</span>.
                </p>
                <p className="text-sm leading-6 text-muted-foreground">
                  ICRL works with any LLM provider, even closed-source ones. It ships as a{" "}
                  <a
                    href="https://www.npmjs.com/package/icrl"
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline underline-offset-2 text-foreground hover:text-primary"
                  >
                    npm
                  </a>{" "}
                  and{" "}
                  <a
                    href="https://pypi.org/project/icrl-py/"
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline underline-offset-2 text-foreground hover:text-primary"
                  >
                    pip
                  </a>{" "}
                  package, so you can apply our research right away.
                </p>
              </CardContent>
            </Card>

            {/* ─── ICRL vs Traditional RL (proper table) ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-7">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-2xl tracking-tight text-foreground">
                    ICRL vs traditional RL
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border/60">
                        <th className="pb-2 pt-2 pr-3 text-left font-semibold text-muted-foreground" />
                        <th className="bg-primary/5 px-3 pb-2 pt-2 text-left font-semibold text-primary">
                          ICRL
                        </th>
                        <th className="pb-2 pt-2 pl-3 text-left font-semibold text-muted-foreground">
                          Traditional RL
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonRows.map((row) => (
                        <tr key={row.dimension} className="border-b border-border/30 last:border-0">
                          <td className="py-2.5 pr-3 font-medium text-foreground whitespace-nowrap">
                            {row.dimension}
                          </td>
                          <td className="bg-primary/5 py-2.5 px-3 text-foreground">{row.icrl}</td>
                          <td className="py-2.5 pl-3 text-muted-foreground">{row.traditional}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* ─── Common use cases (with GitHub links) ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-7">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-xl tracking-tight text-foreground">
                    Common use cases
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                {useCases.map((item) => (
                  <a
                    key={item.title}
                    href={`${GITHUB_BASE}/${item.path}`}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="block space-y-2 border border-border/60 bg-muted/20 p-3 hover:border-primary/80"
                  >
                    <div className="flex items-center gap-2">
                      <item.icon className="size-4 text-primary" />
                      <h3 className="text-sm font-semibold text-foreground">{item.title}</h3>
                      <ArrowUpRight className="ml-auto size-3 text-muted-foreground" />
                    </div>
                    <p className="text-xs leading-5 text-muted-foreground">{item.detail}</p>
                    <span className="inline-flex items-center gap-1 font-mono text-[11px] text-muted-foreground">
                      {item.path}
                    </span>
                  </a>
                ))}
              </CardContent>
            </Card>

            {/* ─── CLI / Coding Agent ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-5">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-xl tracking-tight text-foreground">
                    Codebase specific agents
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm leading-6 text-muted-foreground">
                  ICRL enables you to specialize an agent to a specific codebase. Using the ICRL
                  CLI, you can launch a terminal UI like Claude Code or Codex that creates an
                  interactive coding assistant in your shell. Unlike static assistants, it{" "}
                  <span className="font-semibold text-foreground">gets better over time</span> as
                  successful trajectories are stored and retrieved for future tasks.
                </p>
                <pre className="border border-border/60 bg-muted/20 p-3 font-mono text-xs text-foreground">{`uv run icrl chat`}</pre>
                <p className="text-sm leading-6 text-muted-foreground">
                  The more you use it, the better it gets at understanding your project&apos;s
                  patterns, conventions, and architecture, like a custom model fine-tuned to your
                  codebase.
                </p>
              </CardContent>
            </Card>

            {/* ─── ICRLHF ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-5">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-xl tracking-tight text-foreground">
                    ICRLHF — learning from any feedback signal
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">
                  ICRL can be used with any feedback signal, not just task success. With ICRLHF,
                  agents can learn from human preferences in real time, reacting to the first thumbs
                  up or down signal they receive.
                </p>
                <div className="grid gap-2">
                  {feedbackSignals.map((signal) => (
                    <div
                      key={signal.label}
                      className="flex items-start gap-2.5 border border-border/60 bg-muted/20 px-3 py-2"
                    >
                      <signal.icon className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      <div>
                        <p className="text-xs font-semibold text-foreground">{signal.label}</p>
                        <p className="text-[11px] leading-4 text-muted-foreground">
                          {signal.example}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* ─── Stanford Research ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-7">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-xl tracking-tight text-foreground">
                    Built out of academic research
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">
                  This package was built by Stanford Graphics Lab researchers who have been
                  developing ICRL since 2024. You can read more about the research in the following
                  papers:
                </p>
                <div className="space-y-3">
                  <div className="space-y-2">
                    <a
                      href="https://arxiv.org/abs/2505.00234"
                      target="_blank"
                      rel="noreferrer noopener"
                      className="block border border-border/60 bg-muted/20 p-3 space-y-1.5 hover:border-primary/80"
                    >
                      <p className="text-xs font-semibold text-foreground">
                        Self-Generated In-Context Examples Improve LLM Agents for Sequential
                        Decision-Making Tasks{" "}
                        <span className="text-muted-foreground italic">(NeurIPS 2025)</span>
                      </p>
                      <p className="text-[11px] leading-4 text-muted-foreground">
                        Converting successful trajectories into retrieval-time reinforcement
                        improves agent performance. Exceeds gpt-4o-mini→gpt-4o upgrade gains.
                      </p>
                      <span className="inline-flex items-center gap-1.5 text-xs text-foreground">
                        <BookOpen className="size-3.5" />
                        arxiv.org/abs/2505.00234
                        <ArrowUpRight className="size-3" />
                      </span>
                    </a>
                    <div className="flex flex-row flex-wrap gap-2">
                      {[
                        { name: "ALFWorld", stat: "73%→93%", icon: Home },
                        { name: "InterCode-SQL", stat: "75%→79%", icon: Database },
                        { name: "Wordcraft", stat: "55%→64%", icon: PenLine },
                      ].map(({ name, stat, icon: Icon }) => (
                        <span
                          key={name}
                          className="inline-flex items-center gap-1 border border-border/60 bg-muted/20 px-2 py-0.5 text-[11px]"
                        >
                          <Icon className="size-3 text-primary" />
                          {name} {stat}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <a
                      href="https://arxiv.org/abs/2512.02543"
                      target="_blank"
                      rel="noreferrer noopener"
                      className="block border border-border/60 bg-muted/20 p-3 space-y-1.5 hover:border-primary/80"
                    >
                      <p className="text-xs font-semibold text-foreground">
                        In-Context Distillation with Self-Consistency Cascades: A Simple,
                        Training-Free Way to Reduce LLM Agent Costs
                      </p>
                      <p className="text-[11px] leading-4 text-muted-foreground">
                        Training-free cost reduction by using a larger model to generate in-context
                        examples for a smaller model. GPT-4.1-mini with distillation exceeds Claude
                        4.5 Sonnet performance.
                      </p>
                      <span className="inline-flex items-center gap-1.5 text-xs text-foreground">
                        <BookOpen className="size-3.5" />
                        arxiv.org/abs/2512.02543
                        <ArrowUpRight className="size-3" />
                      </span>
                    </a>
                    <div className="flex flex-row flex-wrap gap-2">
                      {[
                        { name: "ALFWorld", stat: "2.5× cost ↓", icon: Home },
                        { name: "AppWorld", stat: "2× cost ↓", icon: Globe },
                      ].map(({ name, stat, icon: Icon }) => (
                        <span
                          key={name}
                          className="inline-flex items-center gap-1 border border-border/60 bg-muted/20 px-2 py-0.5 text-[11px]"
                        >
                          <Icon className="size-3 text-primary" />
                          {name} {stat}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* ─── CTA ─── */}
            <Card
              className="border-primary/60 bg-card shadow-none md:col-span-12 px-6"
              role="complementary"
              aria-label="Call to action"
            >
              <CardContent className="flex flex-col items-center gap-5 py-6 text-center md:flex-row md:justify-between md:gap-6 md:text-left">
                <div className="space-y-1 max-md:max-w-md">
                  <h2 className="font-heading text-4xl text-foreground">
                    Start improving your agents{" "}
                    <ArrowRight className="size-8 text-primary inline" />
                  </h2>
                </div>
                <div className="flex shrink-0 flex-col items-center md:items-end">
                  <InstallLinks />
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <SiteFooter />
      </main>
    </>
  );
}
