"use client";

import { BookOpen, Github } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t mt-auto">
      <div className="max-w-3xl mx-auto px-6 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            Built with{" "}
            <a href="https://github.com/SuperAce100/icrl" className="text-primary hover:underline">
              ICRL
            </a>{" "}
            &bull; In-Context Reinforcement Learning
          </p>
          <nav className="flex items-center gap-4">
            <a
              href="https://icrl.mintlify.app"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <BookOpen className="h-4 w-4" />
              <span>Docs</span>
            </a>
            <a
              href="https://github.com/SuperAce100/icrl"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Github className="h-4 w-4" />
              <span>GitHub</span>
            </a>
          </nav>
        </div>
      </div>
    </footer>
  );
}
