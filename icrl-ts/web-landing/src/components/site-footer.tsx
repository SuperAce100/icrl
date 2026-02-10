import Image from "next/image";
import Link from "next/link";
import { Github } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden bg-background pt-6 md:pt-6">
      {/* Flourish — fades in from top, adapts to light/dark */}
      <div
        className="pointer-events-none absolute inset-0 opacity-20 dark:opacity-10"
        style={{
          maskImage: "linear-gradient(to bottom, transparent 0%, transparent 40%, black 130%)",
          WebkitMaskImage:
            "linear-gradient(to bottom, transparent 0%, transparent 40%, black 130%)",
        }}
      >
        <Image
          src="/visuals/footer-flourish.png"
          alt=""
          fill
          className="object-cover object-bottom dark:invert"
          aria-hidden="true"
        />
      </div>

      <div className="relative mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 pb-6 pt-6 sm:flex-row">
        <div className="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:gap-4">
          <p className="text-xs text-primary/80 font-medium">In-Context Reinforcement Learning</p>
          <div
            className="flex flex-wrap items-center justify-center gap-2"
            aria-label="Research affiliations"
          >
            <a
              href="https://graphics.stanford.edu"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded border border-border/60 bg-muted/30 px-2 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Stanford Graphics Lab
            </a>
            <span className="rounded border border-border/60 bg-muted/30 px-2 py-1 text-[11px] font-medium text-muted-foreground">
              NeurIPS
            </span>
          </div>
        </div>
        <nav className="flex flex-wrap items-center gap-4">
          <Link
            href="/docs"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Docs
          </Link>
          <a
            href="https://github.com/SuperAce100/icrl"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <Github className="size-3" />
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}
