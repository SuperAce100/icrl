import Image from "next/image";
import Link from "next/link";
import { Github } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden bg-background/90">
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-44 opacity-35 dark:opacity-25">
        <Image
          src="/visuals/footer-flourish.png"
          alt=""
          fill
          className="object-cover object-bottom"
          sizes="100vw"
          priority={false}
        />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-background/80" />
      <div className="relative mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-6 sm:flex-row">
        <p className="text-xs text-muted-foreground">
          In-Context Reinforcement Learning. Built with ICRL in 2026.
        </p>
        <nav className="flex items-center gap-4">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Landing
          </Link>
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
