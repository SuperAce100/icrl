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
        <p className="text-xs text-primary/80 font-medium">In-Context Reinforcement Learning</p>
        <nav className="flex items-center gap-4">
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
