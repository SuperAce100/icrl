import { BookOpen, Github } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/40 bg-background/70 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-6 sm:flex-row">
        <p className="text-xs text-muted-foreground">
          In-Context Reinforcement Learning. Built with ICRL in 2026.
        </p>
        <nav className="flex items-center gap-4">
          <a
            href="https://icrl.mintlify.app"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <BookOpen className="size-3" />
            Docs
          </a>
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
