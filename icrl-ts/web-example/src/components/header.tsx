"use client";

import Image from "next/image";
import { BookOpen, Github } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-md sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/logo_light.png"
              alt="ICRL"
              width={40}
              height={40}
              className="dark:hidden"
            />
            <Image
              src="/logo_dark.png"
              alt="ICRL"
              width={40}
              height={40}
              className="hidden dark:block"
            />
            <div>
              <h1 className="text-xl font-semibold tracking-tight">
                <span className="text-primary">ICRL</span>
                <span className="text-muted-foreground font-normal ml-2">Playground</span>
              </h1>
              <p className="text-xs text-muted-foreground">In-Context Reinforcement Learning</p>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <a
              href="https://icrl.mintlify.app"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted"
            >
              <BookOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Docs</span>
            </a>
            <a
              href="https://github.com/SuperAce100/icrl"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted"
            >
              <Github className="h-4 w-4" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
