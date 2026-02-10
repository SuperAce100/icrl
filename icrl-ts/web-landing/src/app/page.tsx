import Image from "next/image";
import { ArrowRight, ArrowUpRight, BookOpen, Bot, Code2, Database, Package, Sparkles, Target } from "lucide-react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const workflowStages = [
  {
    step: "Step 1",
    title: "Capture successful trajectories",
    body: "Store verified trajectories from real task completions as reusable memory.",
    image: "/visuals/icrl-memory-loop.png",
    alt: "Workflow stage for capturing successful trajectories",
  },
  {
    step: "Step 2",
    title: "Retrieve matching prior wins",
    body: "Select relevant successful traces at the exact point an agent needs guidance.",
    image: "/visuals/icrl-self-improvement-grid.png",
    alt: "Workflow stage for retrieving relevant successful trajectories",
  },
  {
    step: "Step 3",
    title: "Reinforce instantly at runtime",
    body: "Condition the next action on proven context so behavior improves on the next attempt.",
    image: "/visuals/icrl-runtime-surface.png",
    alt: "Workflow stage for instant in-context reinforcement",
  },
];

const useCases = [
  {
    title: "Support + Ops agents",
    body: "Recurring workflows become higher quality after each successful run.",
    icon: Bot,
  },
  {
    title: "Code and DevOps copilots",
    body: "Fix patterns and command sequences are reused without retraining cycles.",
    icon: Code2,
  },
  {
    title: "Data and SQL assistants",
    body: "Iterative query tasks improve in-context as outcomes are curated.",
    icon: Database,
  },
];

const comparisons = [
  {
    label: "ICRL",
    points: [
      "Reinforcement during runtime",
      "Uses successful trajectories as memory",
      "No policy training infrastructure required",
      "Adapts immediately to repeated tasks",
    ],
  },
  {
    label: "Traditional RL",
    points: [
      "Improvement after training cycles",
      "Requires optimization over model weights",
      "Higher infra and experimentation overhead",
      "Slower feedback loop from success to behavior",
    ],
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <SiteHeader />

      <section className="mx-auto max-w-6xl px-6 pb-10 pt-12 md:pt-16">
        <div className="mx-auto max-w-3xl space-y-5 text-center">
          <div className="flex items-center justify-center">
            <Image src="/logo_hero_light.svg" alt="ICRL" width={280} height={24} className="dark:hidden" priority />
            <Image src="/logo_hero_dark.svg" alt="ICRL" width={280} height={24} className="hidden dark:block" priority />
          </div>
          <h1 className="font-[family-name:var(--font-archivo)] text-balance text-3xl font-semibold leading-tight tracking-tight text-foreground sm:text-4xl md:text-5xl">
            Instant reinforcement learning for production agents.
          </h1>
          <p className="text-balance text-base leading-7 text-muted-foreground sm:text-lg">
            ICRL turns successful trajectories into reusable in-context memory, so agents improve right away instead of
            waiting for retraining.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button asChild>
              <a href="https://github.com/SuperAce100/icrl/tree/main/icrl-ts" target="_blank" rel="noreferrer noopener">
                <Sparkles className="size-4" />
                Install package
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
              <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                <BookOpen className="size-4" />
                Read paper
              </a>
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-12 md:auto-rows-[minmax(180px,auto)]">
          <Card className="border-primary/60 bg-card shadow-none md:col-span-12">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                Visual workflow: how ICRL improves agents immediately
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="hidden items-center gap-3 text-[11px] uppercase tracking-[0.08em] text-muted-foreground md:flex">
                <span>Capture</span>
                <ArrowRight className="size-3 text-primary" />
                <span>Retrieve</span>
                <ArrowRight className="size-3 text-primary" />
                <span>Reinforce</span>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                {workflowStages.map((stage) => (
                  <div key={stage.title} className="space-y-3 border border-border/60 bg-muted/20 p-3">
                    <div className="space-y-1">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-primary">{stage.step}</p>
                      <p className="text-sm font-semibold text-foreground">{stage.title}</p>
                    </div>
                    <div className="border border-border/60 bg-background p-2 text-foreground">
                      <Image src={stage.image} alt={stage.alt} width={1200} height={720} className="h-auto w-full" />
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">{stage.body}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-5">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Why teams choose ICRL
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm leading-6 text-muted-foreground">
                It delivers self-improvement at inference time. You keep your model stack and gain a fast reinforcement
                mechanism directly in product workflows.
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>Immediate feedback-to-behavior loop</li>
                <li>No delayed policy updates</li>
                <li>Works with existing model APIs</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-7">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                ICRL vs traditional RL
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              {comparisons.map((group) => (
                <div key={group.label} className="space-y-2 border border-border/60 bg-muted/20 p-4">
                  <p className="text-sm font-semibold uppercase tracking-[0.08em] text-foreground">{group.label}</p>
                  <ul className="space-y-1.5 text-sm leading-6 text-muted-foreground">
                    {group.points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-7">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Instant self-improvement use cases
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {useCases.map((item) => (
                <div key={item.title} className="border border-border/60 bg-muted/20 p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <item.icon className="size-4 text-primary" />
                    <p className="text-sm font-semibold text-foreground">{item.title}</p>
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">{item.body}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card shadow-none md:col-span-5">
            <CardHeader>
              <CardTitle className="font-[family-name:var(--font-archivo)] text-xl tracking-tight text-foreground">
                Published packages
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <a
                href="https://www.npmjs.com/package/icrl"
                target="_blank"
                rel="noreferrer noopener"
                className="flex items-center justify-between border border-border/60 bg-muted/20 px-4 py-3 text-sm text-foreground transition-colors hover:bg-muted/40"
              >
                <span>npm: `icrl`</span>
                <ArrowUpRight className="size-4 text-primary" />
              </a>
              <a
                href="https://pypi.org/project/icrl/"
                target="_blank"
                rel="noreferrer noopener"
                className="flex items-center justify-between border border-border/60 bg-muted/20 px-4 py-3 text-sm text-foreground transition-colors hover:bg-muted/40"
              >
                <span>PyPI: `icrl`</span>
                <ArrowUpRight className="size-4 text-primary" />
              </a>
            </CardContent>
          </Card>

          <Card className="border-primary/60 bg-card shadow-none md:col-span-12">
            <CardContent className="flex flex-col gap-5 py-6 md:flex-row md:items-center md:justify-between">
              <div className="space-y-2">
                <p className="font-[family-name:var(--font-archivo)] text-2xl tracking-tight text-foreground">
                  Build agents that learn while they run.
                </p>
                <p className="text-sm leading-6 text-muted-foreground">
                  Start with the TypeScript package, then connect your trajectory store and retrieval policy.
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
                    npm package
                  </a>
                </Button>
                <Button asChild variant="ghost">
                  <a href="https://pypi.org/project/icrl/" target="_blank" rel="noreferrer noopener">
                    <Package className="size-4" />
                    PyPI package
                  </a>
                </Button>
                <Button asChild variant="ghost">
                  <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                    <ArrowUpRight className="size-4" />
                    Original paper
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
