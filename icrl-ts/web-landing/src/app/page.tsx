import type { Metadata } from "next";
import {
  ArrowUpRight,
  BookOpen,
  Bot,
  CheckCircle2,
  Code2,
  Database,
  MessageSquare,
  Package,
  Sparkles,
  Target,
  Terminal,
  ThumbsUp,
} from "lucide-react";

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
      <main className="min-h-screen bg-background">
        <SiteHeader />

        <section
          aria-label="Hero"
          className="mx-auto px-6 pb-12 pt-12 md:pt-32 md:pb-32 max-w-2xl space-y-6 text-center"
        >
          <h1 className="font-heading text-4xl font-semibold leading-[1.04] tracking-tight text-foreground sm:text-5xl md:text-6xl">
            instant, continuous,
            <br />
            reinforcement learning
            <br />
            for LLM agents
          </h1>
          <p className="mx-auto text-base leading-7 text-muted-foreground sm:text-lg text-balance">
            ICRL turns successful trajectories into reusable decision context so agents improve on
            the next task instead of waiting for retraining.
          </p>
          <div className="flex justify-center">
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
            <Card className="border-primary/60 bg-card shadow-none md:col-span-7">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-2xl tracking-tight text-foreground">
                    What is ICRL
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">
                  <span className="font-semibold text-foreground">
                    In-Context Reinforcement Learning (ICRL)
                  </span>{" "}
                  is a framework that lets LLM agents learn from their own experience at runtime —
                  without any fine-tuning, retraining, or prompt engineering. When an agent
                  successfully completes a task, ICRL stores that trajectory. The next time a
                  similar task comes up, the agent retrieves the most relevant past steps and uses
                  them as in-context examples to guide its decisions.
                </p>
                <p className="text-sm leading-6 text-muted-foreground">
                  Think of it as giving your agent a growing memory of what has worked before. Over
                  time, low-quality or outdated trajectories are automatically curated out, so the
                  agent&apos;s experience stays fresh and relevant. The result is an agent that gets
                  measurably better with every task it completes — all while using the same frozen
                  model underneath.
                </p>
                <p className="text-sm leading-6 text-muted-foreground">
                  ICRL works with any LLM provider and any agentic framework. It ships as a
                  lightweight{" "}
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
                    href="https://pypi.org/project/icrl/"
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline underline-offset-2 text-foreground hover:text-primary"
                  >
                    PyPI
                  </a>{" "}
                  package with a simple API: store trajectories, retrieve by goal and step
                  observation, and curate over time.
                </p>
              </CardContent>
            </Card>

            {/* ─── ICRL vs Traditional RL (proper table) ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-5">
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
                        <th className="pb-2 pr-3 text-left font-semibold text-muted-foreground" />
                        <th className="pb-2 px-3 text-left font-semibold text-primary">ICRL</th>
                        <th className="pb-2 pl-3 text-left font-semibold text-muted-foreground">
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
                          <td className="py-2.5 px-3 text-foreground">{row.icrl}</td>
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
                  <div
                    key={item.title}
                    className="space-y-2 border border-border/60 bg-muted/20 p-3"
                  >
                    <div className="flex items-center gap-2">
                      <item.icon className="size-4 text-primary" />
                      <h3 className="text-sm font-semibold text-foreground">{item.title}</h3>
                    </div>
                    <p className="text-xs leading-5 text-muted-foreground">{item.detail}</p>
                    <a
                      href={`${GITHUB_BASE}/${item.path}`}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="inline-flex items-center gap-1 font-mono text-[11px] text-muted-foreground hover:text-primary transition-colors"
                    >
                      {item.path}
                      <ArrowUpRight className="size-3" />
                    </a>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* ─── CLI / Coding Agent ─── */}
            <Card className="border-border/70 bg-card shadow-none md:col-span-5">
              <CardHeader>
                <CardTitle asChild>
                  <h2 className="font-heading text-xl tracking-tight text-foreground">
                    A coding agent that learns your codebase
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">
                  ICRL ships with a built-in coding agent you can run from your terminal — like
                  Claude Code or Codex, but one that{" "}
                  <span className="font-semibold text-foreground">gets better over time</span>.
                  Every task it completes successfully becomes a reference for future work, so it
                  builds up project-specific knowledge that generic assistants never develop.
                </p>
                <pre className="border border-border/60 bg-muted/20 p-3 font-mono text-xs leading-6 text-foreground">{`icrl run "fix failing tests" --compare
icrl run "add input validation to the API"
icrl db stats`}</pre>
                <p className="text-xs leading-5 text-muted-foreground">
                  The more you use it, the better it gets at understanding your project&apos;s
                  patterns, conventions, and architecture. No fine-tuning, no prompt engineering —
                  just accumulated experience from successful trajectories in{" "}
                  <span className="font-mono text-foreground">.icrl/trajectories</span>.
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
                  <span className="font-semibold text-foreground">ICRLHF</span> extends ICRL with
                  human feedback. Instead of only learning from task success, agents can learn from
                  any signal you provide — preferences, corrections, approvals, or rejections. These
                  signals become durable training data retrieved at inference time.
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
                    Built by Stanford researchers, presented at NeurIPS
                  </h2>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">
                  This package was built by the authors of the original ICRL research at{" "}
                  <span className="font-semibold text-foreground">Stanford Graphics Lab</span>. The
                  core ideas were validated in two peer-reviewed papers and presented at{" "}
                  <span className="font-semibold text-foreground">NeurIPS</span>.
                </p>
                <div className="space-y-3">
                  <div className="border border-border/60 bg-muted/20 p-3 space-y-1.5">
                    <p className="text-xs font-semibold text-foreground">
                      Self-Generated In-Context Examples Improve LLM Agents for Sequential
                      Decision-Making Tasks
                    </p>
                    <p className="text-[11px] leading-4 text-muted-foreground">
                      Shows that converting successful trajectories into retrieval-time
                      reinforcement improves LLM agent performance on ALFWorld, InterCode-SQL, and
                      Wordcraft benchmarks.
                    </p>
                    <a
                      href="https://arxiv.org/abs/2505.00234"
                      target="_blank"
                      rel="noreferrer noopener"
                      className="inline-flex items-center gap-1.5 text-xs text-foreground hover:text-primary transition-colors"
                    >
                      <BookOpen className="size-3.5" />
                      arxiv.org/abs/2505.00234
                      <ArrowUpRight className="size-3" />
                    </a>
                  </div>
                  <div className="border border-border/60 bg-muted/20 p-3 space-y-1.5">
                    <p className="text-xs font-semibold text-foreground">
                      In-Context Distillation with Self-Consistency Cascades
                    </p>
                    <p className="text-[11px] leading-4 text-muted-foreground">
                      A training-free method to reduce LLM agent costs by 2-2.5x at iso-accuracy.
                      Combines in-context distillation with self-consistency cascades for
                      economically viable agentic systems.
                    </p>
                    <a
                      href="https://arxiv.org/abs/2512.02543"
                      target="_blank"
                      rel="noreferrer noopener"
                      className="inline-flex items-center gap-1.5 text-xs text-foreground hover:text-primary transition-colors"
                    >
                      <BookOpen className="size-3.5" />
                      arxiv.org/abs/2512.02543
                      <ArrowUpRight className="size-3" />
                    </a>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {["ALFWorld", "InterCode-SQL", "Wordcraft", "AppWorld"].map((bench) => (
                    <div
                      key={bench}
                      className="inline-flex items-center gap-1 border border-border/60 bg-muted/20 px-2.5 py-1 text-xs text-foreground"
                    >
                      <CheckCircle2 className="size-3.5 text-primary" /> {bench}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* ─── CTA ─── */}
            <Card
              className="border-primary/60 bg-card shadow-none md:col-span-12"
              role="complementary"
              aria-label="Call to action"
            >
              <CardContent className="flex flex-col gap-5 py-6 md:flex-row md:items-center md:justify-between">
                <div className="space-y-2">
                  <h2 className="font-heading text-2xl tracking-tight text-foreground">
                    Start building with ICRL
                  </h2>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Install the package, run coding tasks with the CLI, and let successful
                    trajectories continuously improve your agent.
                  </p>
                </div>
                <nav aria-label="Install links" className="flex flex-wrap items-center gap-3">
                  <Button asChild>
                    <a href="/docs">
                      <Target className="size-4" />
                      Open docs
                    </a>
                  </Button>
                  <Button asChild variant="ghost">
                    <a
                      href="https://www.npmjs.com/package/icrl"
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      <Package className="size-4" />
                      npm
                    </a>
                  </Button>
                  <Button asChild variant="ghost">
                    <a
                      href="https://pypi.org/project/icrl/"
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      <Package className="size-4" />
                      PyPI
                    </a>
                  </Button>
                  <Button asChild variant="ghost">
                    <a
                      href="https://github.com/SuperAce100/icrl"
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      <Sparkles className="size-4" />
                      GitHub
                    </a>
                  </Button>
                </nav>
              </CardContent>
            </Card>
          </div>
        </section>

        <SiteFooter />
      </main>
    </>
  );
}
