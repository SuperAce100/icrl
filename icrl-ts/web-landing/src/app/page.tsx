import Image from "next/image";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Code2,
  Database,
  GitBranch,
  Package,
  Sparkles,
  Target,
  Terminal,
} from "lucide-react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const loopStages = [
  "Attempt tasks in an environment",
  "Store successful trajectories",
  "Retrieve by goal + step observation",
  "Curate low-utility trajectories over time",
];

const comparisonRows = [
  {
    label: "When behavior improves",
    icrl: "During runtime on the next similar task",
    traditional: "After a retraining cycle completes",
  },
  {
    label: "What is updated",
    icrl: "In-context memory (trajectory retrieval)",
    traditional: "Model/policy weights",
  },
  {
    label: "Infra profile",
    icrl: "Trajectory DB + retrieval + curation",
    traditional: "Training pipelines + eval + deployment rollouts",
  },
  {
    label: "Feedback latency",
    icrl: "Immediate",
    traditional: "Batch-delayed",
  },
];

const codingTools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"];

const useCases = [
  {
    title: "Coding agents",
    detail: "Harbor coding workflows and Terminal-Bench style tasks improve from successful trajectories.",
    source: "examples/harbor_coding_agent.py",
    icon: Code2,
  },
  {
    title: "Filesystem/task agents",
    detail: "Command-style environments (`ls`, `cd`, `cat`, `find`) become more reliable across repeated goals.",
    source: "examples/file_api_env.py",
    icon: Terminal,
  },
  {
    title: "Support triage",
    detail: "Routing and reply quality improve as successful triage outputs are retained and reused.",
    source: "icrl-ts/examples/support-triage-demo.ts",
    icon: Bot,
  },
  {
    title: "Feedback-driven web workflows",
    detail: "Human choices between candidate answers become durable training signals for future retrieval.",
    source: "icrl-ts/web-example",
    icon: Database,
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <SiteHeader />

      <section className="mx-auto max-w-6xl px-6 pb-12 pt-12 md:pt-16">
        <div className="mx-auto max-w-4xl space-y-6 text-center">
          <div className="flex items-center justify-center">
            <Image src="/logo_hero_light.svg" alt="ICRL" width={280} height={24} className="dark:hidden" priority />
            <Image src="/logo_hero_dark.svg" alt="ICRL" width={280} height={24} className="hidden dark:block" priority />
          </div>
          <h1 className="font-[family-name:var(--font-archivo)] text-4xl font-semibold leading-[1.04] tracking-tight text-foreground sm:text-5xl md:text-6xl">
            instant, continuous,
            <br />
            reinforcement learning
            <br />
            for LLM agents
          </h1>
          <p className="mx-auto max-w-3xl text-base leading-7 text-muted-foreground sm:text-lg">
            ICRL turns successful trajectories into reusable decision context so agents improve on the next task instead
            of waiting for retraining.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-12 md:auto-rows-[minmax(190px,auto)]">
          <Card className="border-primary/60 bg-card shadow-none md:col-span-7">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                What is ICRL
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <p className="text-sm leading-6 text-muted-foreground">
                ICRL is a trajectory-learning framework where the agent runs tasks, keeps successful episodes, retrieves
                similar prior steps during future runs, and curates stale/low-signal entries over time.
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {loopStages.map((stage) => (
                  <div key={stage} className="flex items-center gap-2 border border-border/60 bg-muted/20 px-3 py-2">
                    <ArrowRight className="size-3 text-primary" />
                    <span className="text-xs text-foreground">{stage}</span>
                  </div>
                ))}
              </div>
              <div className="inline-flex items-center gap-2 border border-border/60 bg-muted/20 px-3 py-1.5 text-xs text-muted-foreground">
                <GitBranch className="size-3.5 text-primary" />
                ReAct loop with step-level retrieval (`retrieve_for_plan`, `retrieve_for_step`)
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-5">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                ICRL vs traditional RL
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {comparisonRows.map((row) => (
                <div key={row.label} className="grid gap-2 border border-border/60 bg-muted/20 p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary">{row.label}</p>
                  <p className="text-xs leading-5 text-foreground">
                    <span className="font-semibold">ICRL:</span> {row.icrl}
                  </p>
                  <p className="text-xs leading-5 text-muted-foreground">
                    <span className="font-semibold text-foreground">Traditional RL:</span> {row.traditional}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-7">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Common use cases
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              {useCases.map((item) => (
                <div key={item.title} className="space-y-2 border border-border/60 bg-muted/20 p-3">
                  <div className="flex items-center gap-2">
                    <item.icon className="size-4 text-primary" />
                    <p className="text-sm font-semibold text-foreground">{item.title}</p>
                  </div>
                  <p className="text-xs leading-5 text-muted-foreground">{item.detail}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">{item.source}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-5">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">CLI</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <pre className="border border-border/60 bg-muted/20 p-3 font-mono text-xs leading-6 text-foreground">{`icrl run "fix failing tests in this repo" --compare\nicrl db stats\nicrl db search "pytest fixture" -k 5\nicrl db validate --dir .`}</pre>
              <div className="grid grid-cols-2 gap-2">
                {codingTools.map((tool) => (
                  <div key={tool} className="border border-border/60 bg-background px-2 py-1 text-center text-[11px] text-foreground">
                    {tool}
                  </div>
                ))}
              </div>
              <p className="text-xs leading-5 text-muted-foreground">
                Project-local storage defaults to <span className="font-mono text-foreground">.icrl/trajectories</span>.
                Use <span className="font-mono text-foreground">--global</span> to target shared DB, and use
                <span className="font-mono text-foreground"> db validate</span> / <span className="font-mono text-foreground">db prune</span>
                for code-persistence-aware curation.
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-5">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">ICRLHF</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="inline-flex items-center gap-2 text-sm text-foreground">
                <BrainCircuit className="size-4 text-primary" />
                In-context reinforcement from human preference signals
              </p>
              <div className="space-y-2">
                <div className="border border-border/60 bg-muted/20 px-3 py-2 text-xs text-muted-foreground">1. Generate multiple candidate answers</div>
                <div className="border border-border/60 bg-muted/20 px-3 py-2 text-xs text-muted-foreground">2. Human selects best answer or writes a better one</div>
                <div className="border border-border/60 bg-muted/20 px-3 py-2 text-xs text-muted-foreground">3. Store chosen/rejected outputs for retrieval-time reinforcement</div>
              </div>
              <p className="text-xs leading-5 text-muted-foreground">
                Implemented in the web example with Convex tables like
                <span className="font-mono text-foreground"> examples</span>,
                <span className="font-mono text-foreground"> trajectories</span>, and
                <span className="font-mono text-foreground"> curationMetadata</span>.
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-7">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Proven through Stanford research
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm leading-6 text-muted-foreground">
                The paper, <span className="text-foreground">Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks</span>,
                reports gains from converting successful trajectories into retrieval-time reinforcement.
              </p>
              <div className="flex flex-wrap gap-2">
                <div className="inline-flex items-center gap-1 border border-border/60 bg-muted/20 px-2.5 py-1 text-xs text-foreground">
                  <CheckCircle2 className="size-3.5 text-primary" /> ALFWorld
                </div>
                <div className="inline-flex items-center gap-1 border border-border/60 bg-muted/20 px-2.5 py-1 text-xs text-foreground">
                  <CheckCircle2 className="size-3.5 text-primary" /> InterCode-SQL
                </div>
                <div className="inline-flex items-center gap-1 border border-border/60 bg-muted/20 px-2.5 py-1 text-xs text-foreground">
                  <CheckCircle2 className="size-3.5 text-primary" /> Wordcraft
                </div>
              </div>
              <a
                href="https://arxiv.org/abs/2505.00234"
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-2 text-sm text-foreground hover:text-primary"
              >
                <BookOpen className="size-4" />
                Read original paper
                <ArrowUpRight className="size-4" />
              </a>
            </CardContent>
          </Card>

          <Card className="border-primary/60 bg-card shadow-none md:col-span-12">
            <CardContent className="flex flex-col gap-5 py-6 md:flex-row md:items-center md:justify-between">
              <div className="space-y-2">
                <p className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">Start building with ICRL</p>
                <p className="text-sm leading-6 text-muted-foreground">
                  Install the package, run coding tasks with the CLI, and let successful trajectories continuously improve your agent.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button asChild>
                  <a href="/docs">
                    <Target className="size-4" />
                    Open docs
                  </a>
                </Button>
                <Button asChild variant="ghost">
                  <a href="https://www.npmjs.com/package/icrl" target="_blank" rel="noreferrer noopener">
                    <Package className="size-4" />
                    npm
                  </a>
                </Button>
                <Button asChild variant="ghost">
                  <a href="https://pypi.org/project/icrl/" target="_blank" rel="noreferrer noopener">
                    <Package className="size-4" />
                    PyPI
                  </a>
                </Button>
                <Button asChild variant="ghost">
                  <a href="https://github.com/SuperAce100/icrl" target="_blank" rel="noreferrer noopener">
                    <Sparkles className="size-4" />
                    GitHub
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}
