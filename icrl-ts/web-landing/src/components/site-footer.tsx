import Link from "next/link";
import { Github } from "lucide-react";
import { BsGithub } from "react-icons/bs";

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden pt-6 md:pt-6">
      {/* Flourish — fades in from top, adapts to light/dark */}

      <div className="relative mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 pb-6 pt-6 sm:flex-row">
        <div className="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:gap-4">
          <p className="text-xs text-muted-foreground font-medium">© ICRL 2026</p>
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
            <BsGithub className="size-3" />
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}
