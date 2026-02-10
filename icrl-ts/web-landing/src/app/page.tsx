import { ArrowRight, BookOpen, Database } from "lucide-react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";

const loopSteps = [
  "Run tasks in your real environment using your current prompts and tools.",
  "Store successful trajectories immediately into the local trajectory database.",
  "Retrieve the most relevant successful examples at each future decision point.",
  "Get better behavior on similar tasks without model retraining.",
];

const useCases = [
  "Support and operations agents that solve repeated workflows.",
  "Coding and DevOps copilots with recurring command and fix patterns.",
  "SQL and data assistants in iterative query-and-feedback tasks.",
  "Browser and API automation where successful flows repeat.",
];

const compareRows = [
  {
    label: "Feedback usage",
    rl: "Converted into model updates during training cycles",
    icrl: "Converted into memory for immediate in-context reuse",
  },
  {
    label: "Infrastructure",
    rl: "Policy optimization pipeline and retraining machinery",
    icrl: "Trajectory database plus retrieval on your existing model",
  },
  {
    label: "Time to impact",
    rl: "Typically delayed until next training run",
    icrl: "Can improve the next related task immediately",
  },
];

const benchmarks = [
  { name: "ALFWorld", fixed: "73%", traj: "89%", best: "93%" },
  { name: "InterCode-SQL", fixed: "75%", traj: "79%", best: "82%" },
  { name: "Wordcraft", fixed: "55%", traj: "64%", best: "72%" },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <SiteHeader />

      <section className="mx-auto max-w-4xl px-6 pb-16 pt-20 md:pt-28">
        <div className="space-y-6">
          <h1 className="text-balance text-4xl font-semibold leading-tight tracking-tight sm:text-5xl md:text-6xl">
            Instant reinforcement learning for LLM agents.
          </h1>
          <p className="max-w-3xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            ICRL lets agents improve through successful trajectories. Instead of waiting for heavyweight retraining,
            every success becomes reusable context for future decisions.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <a href="#get-started">
                Start with ICRL
                <ArrowRight className="size-4" />
              </a>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                <BookOpen className="size-4" />
                Original paper
              </a>
            </Button>
          </div>
        </div>
      </section>

      <section id="why" className="section-rule">
        <div className="mx-auto max-w-4xl px-6 py-14 md:py-16">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Why teams choose ICRL</h2>
          <ul className="mt-8 list-disc space-y-3 pl-5 text-sm text-muted-foreground sm:text-base">
            <li>Improves agents from actual successful runs, not synthetic examples.</li>
            <li>Applies reinforcement signal immediately via retrieval-ready memory.</li>
            <li>Avoids the operational cost of a traditional RL training stack.</li>
          </ul>
        </div>
      </section>

      <section className="section-rule">
        <div className="mx-auto max-w-4xl px-6 py-14 md:py-16">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">How the instant loop works</h2>
          <ol className="mt-8 list-decimal space-y-3 pl-5 text-sm text-muted-foreground sm:text-base">
            {loopSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      </section>

      <section id="use-cases" className="section-rule">
        <div className="mx-auto max-w-4xl px-6 py-14 md:py-16">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Use cases</h2>
          <ul className="mt-8 list-disc space-y-3 pl-5 text-sm text-muted-foreground sm:text-base">
            {useCases.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section id="vs-rl" className="section-rule">
        <div className="mx-auto max-w-4xl px-6 py-14 md:py-16">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">ICRL vs traditional RL</h2>
          <div className="mt-8 overflow-x-auto">
            <table className="w-full min-w-[620px] text-sm">
              <thead>
                <tr className="border-b border-border/70 text-left text-muted-foreground">
                  <th className="py-3 pr-4 font-medium">Dimension</th>
                  <th className="py-3 pr-4 font-medium">Traditional RL</th>
                  <th className="py-3 pr-4 font-medium">ICRL</th>
                </tr>
              </thead>
              <tbody>
                {compareRows.map((row) => (
                  <tr key={row.label} className="border-b border-border/50 last:border-0 align-top">
                    <td className="py-3 pr-4 font-medium">{row.label}</td>
                    <td className="py-3 pr-4 text-muted-foreground">{row.rl}</td>
                    <td className="py-3 pr-4 text-foreground">{row.icrl}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section-rule">
        <div className="mx-auto max-w-4xl px-6 py-14 md:py-16">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Evidence from the paper</h2>
          <div className="mt-8 overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border/70 text-left text-muted-foreground">
                  <th className="py-3 pr-4 font-medium">Benchmark</th>
                  <th className="py-3 pr-4 font-medium">Fixed-DB</th>
                  <th className="py-3 pr-4 font-medium">Traj-Bootstrap</th>
                  <th className="py-3 pr-4 font-medium">Best curated</th>
                </tr>
              </thead>
              <tbody>
                {benchmarks.map((row) => (
                  <tr key={row.name} className="border-b border-border/50 last:border-0">
                    <td className="py-3 pr-4 font-medium">{row.name}</td>
                    <td className="py-3 pr-4 text-muted-foreground">{row.fixed}</td>
                    <td className="py-3 pr-4 text-muted-foreground">{row.traj}</td>
                    <td className="py-3 pr-4 text-foreground">{row.best}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Results from arXiv:2505.00234.
          </p>
        </div>
      </section>

      <section id="get-started" className="section-rule">
        <div className="mx-auto max-w-4xl px-6 pb-20 pt-14 md:pb-24 md:pt-16">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Get started</h2>
          <pre className="mt-6 overflow-x-auto rounded-xl border border-border/70 bg-stone-950 p-4 text-xs leading-relaxed text-stone-100 sm:text-sm">
{`npm install icrl
npm install openai`}
          </pre>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button asChild>
              <a href="https://github.com/SuperAce100/icrl/tree/main/icrl-ts" target="_blank" rel="noreferrer noopener">
                <Database className="size-4" />
                View TypeScript package
              </a>
            </Button>
            <p className="text-xs text-muted-foreground">Use the toggle in the top-right corner for dark mode.</p>
          </div>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}
