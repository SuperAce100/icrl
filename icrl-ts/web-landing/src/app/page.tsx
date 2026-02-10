import Image from "next/image";
import { ArrowUpRight, BookOpen, BrainCircuit, Code2, Package, Sparkles, Target, Terminal } from "lucide-react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { WorkflowHalftone } from "@/components/workflow-halftone";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const flourishes = {
  capture: "/visuals/workflow-capture-natural.png",
  retrieve: "/visuals/workflow-retrieve-natural.png",
  reinforce: "/visuals/workflow-reinforce-natural.png",
};

const useCases = [
  "Support and operations agents for repeated workflows",
  "Coding and DevOps copilots with recurring fix patterns",
  "Data and SQL assistants in iterative query loops",
  "Browser and API automation with repeatable flow steps",
];

const rlDiff = [
  "ICRL reinforces behavior at runtime, not after training cycles",
  "ICRL reuses successful trajectories instead of policy optimization",
  "ICRL avoids heavyweight RL infra and delayed retraining loops",
  "ICRL adapts immediately to repeated tasks in production",
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <SiteHeader />

      <section className="mx-auto max-w-6xl px-6 pb-10 pt-10 md:pt-14">
        <div className="mx-auto max-w-3xl space-y-4 text-center">
          <div className="flex items-center justify-center">
            <Image src="/logo_hero_light.svg" alt="ICRL" width={280} height={24} className="dark:hidden" priority />
            <Image src="/logo_hero_dark.svg" alt="ICRL" width={280} height={24} className="hidden dark:block" priority />
          </div>
          <p className="text-sm leading-6 text-muted-foreground">In-Context Reinforcement Learning for production agents</p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-12 md:auto-rows-[minmax(180px,auto)]">
          <Card className="relative overflow-hidden border-primary/60 bg-card shadow-none md:col-span-6">
            <div className="pointer-events-none absolute inset-y-0 right-0 w-24" style={{ maskImage: "linear-gradient(to left, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.capture} label="What is ICRL flourish" fitMode="fill" className="h-full opacity-45" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardHeader>
              <CardTitle className="relative font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                What is ICRL
              </CardTitle>
            </CardHeader>
            <CardContent className="relative space-y-3">
              <p className="text-sm leading-6 text-muted-foreground">
                ICRL stores successful trajectories and retrieves them at decision time so agents can reinforce behavior instantly.
                It turns each production success into usable context for the very next related task.
              </p>
              <p className="text-sm leading-6 text-muted-foreground">The result is immediate self-improvement without waiting for retraining.</p>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-border/70 bg-card shadow-none md:col-span-6">
            <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24" style={{ maskImage: "linear-gradient(to top, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.retrieve} label="ICRL vs traditional RL flourish" fitMode="fill" className="h-full opacity-40" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardHeader>
              <CardTitle className="relative font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                ICRL vs traditional RL
              </CardTitle>
            </CardHeader>
            <CardContent className="relative">
              <ul className="space-y-2 text-sm leading-6 text-muted-foreground">
                {rlDiff.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-border/70 bg-card shadow-none md:col-span-7">
            <div className="pointer-events-none absolute left-0 top-0 h-24 w-28" style={{ maskImage: "linear-gradient(to bottom right, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.reinforce} label="Use case flourish" fitMode="fill" className="h-full opacity-40" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardHeader>
              <CardTitle className="relative font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Common use cases
              </CardTitle>
            </CardHeader>
            <CardContent className="relative">
              <ul className="space-y-2 text-sm leading-6 text-muted-foreground">
                {useCases.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-border/70 bg-card shadow-none md:col-span-5">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-20" style={{ maskImage: "linear-gradient(to bottom, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.capture} label="CLI flourish" fitMode="fill" className="h-full opacity-35" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardHeader>
              <CardTitle className="relative font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                CLI
              </CardTitle>
            </CardHeader>
            <CardContent className="relative space-y-2">
              <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                <Terminal className="size-4 text-primary" /> Python + TypeScript workflow support
              </p>
              <pre className="border border-border/60 bg-muted/20 p-3 font-mono text-xs leading-6 text-foreground">{`pip install icrl\nbun add icrl\nicrl --help`}</pre>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-border/70 bg-card shadow-none md:col-span-5">
            <div className="pointer-events-none absolute inset-y-0 right-0 w-20" style={{ maskImage: "linear-gradient(to left, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.retrieve} label="ICRLHF flourish" fitMode="fill" className="h-full opacity-40" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardHeader>
              <CardTitle className="relative font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                ICRLHF
              </CardTitle>
            </CardHeader>
            <CardContent className="relative space-y-3">
              <p className="inline-flex items-center gap-2 text-sm text-foreground">
                <BrainCircuit className="size-4 text-primary" />
                In-Context RL from Human Feedback
              </p>
              <p className="text-sm leading-6 text-muted-foreground">
                Curate preferred trajectories and retrieval priorities from human feedback, then reinforce better behavior in
                context without retraining your base model.
              </p>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-border/70 bg-card shadow-none md:col-span-7">
            <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24" style={{ maskImage: "linear-gradient(to top, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.reinforce} label="Stanford research flourish" fitMode="fill" className="h-full opacity-40" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardHeader>
              <CardTitle className="relative font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Proven through Stanford research
              </CardTitle>
            </CardHeader>
            <CardContent className="relative space-y-3">
              <p className="text-sm leading-6 text-muted-foreground">
                The Stanford paper demonstrates strong gains across ALFWorld, InterCode-SQL, and Wordcraft by converting
                successful runs into immediate in-context reinforcement.
              </p>
              <a
                href="https://arxiv.org/abs/2505.00234"
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-2 text-sm text-foreground hover:text-primary"
              >
                <BookOpen className="size-4" />
                Read the original research
                <ArrowUpRight className="size-4" />
              </a>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-primary/60 bg-card shadow-none md:col-span-12">
            <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24" style={{ maskImage: "linear-gradient(to top, black, transparent)" }}>
              <WorkflowHalftone image={flourishes.capture} label="CTA flourish" fitMode="fill" className="h-full opacity-35" />
            </div>
            <div className="pointer-events-none absolute inset-0 bg-background/80" />
            <CardContent className="relative flex flex-col gap-5 py-6 md:flex-row md:items-center md:justify-between">
              <div className="space-y-2">
                <p className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">Start building with ICRL</p>
                <p className="text-sm leading-6 text-muted-foreground">Ship self-improving agents with instant reinforcement in production.</p>
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
                  <a href="https://github.com/SuperAce100/icrl/tree/main/icrl-ts" target="_blank" rel="noreferrer noopener">
                    <Code2 className="size-4" />
                    TS package
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
