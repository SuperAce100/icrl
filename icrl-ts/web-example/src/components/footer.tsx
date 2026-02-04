"use client";

import { BookOpen, Github } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-auto">
      <div className="max-w-3xl mx-auto px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            Built with{" "}
            <a href="https://github.com/SuperAce100/icrl" className="text-primary hover:underline">
              ICRL
            </a>{" "}
            in 2026
          </p>
          <nav className="flex items-center gap-4">
            <a
              href="https://icrl.mintlify.app"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <BookOpen className="size-3" />
              <span>Docs</span>
            </a>
          </nav>
        </div>
      </div>
    </footer>
  );
}
