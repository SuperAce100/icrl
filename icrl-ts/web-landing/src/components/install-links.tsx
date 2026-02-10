"use client";

import { useState } from "react";
import { ArrowUpRight, BookOpen, Check } from "lucide-react";
import { SiPython, SiTypescript } from "react-icons/si";

const installs = [
  {
    command: "npm i icrl",
    label: "TypeScript / JavaScript",
    icon: SiTypescript,
    packageUrl: "https://www.npmjs.com/package/icrl",
    packageLabel: "npm",
  },
  {
    command: "pip install icrl-py",
    label: "Python",
    icon: SiPython,
    packageUrl: "https://pypi.org/project/icrl-py/",
    packageLabel: "PyPI",
  },
] as const;

export function InstallLinks() {
  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = async (command: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(command);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      setCopied(null);
    }
  };

  return (
    <div className="flex w-[min(100%,280px)] min-w-[240px] flex-col gap-2">
      {installs.map(({ command, label, icon: Icon, packageUrl, packageLabel }) => (
        <button
          key={command}
          type="button"
          onClick={() => handleCopy(command)}
          className="group flex w-full h-10 cursor-pointer items-center gap-2 rounded-md border border-border/60 bg-muted/20 px-3 py-2 text-left transition-colors hover:border-primary/40 hover:bg-muted/30"
          aria-label={`Copy ${command}`}
        >
          <Icon className="size-4 shrink-0 text-foreground" aria-hidden />
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-foreground group-hover:text-primary transition-colors">
                {copied === command ? (
                  <span className="inline-flex items-center gap-1 text-primary">
                    <Check className="size-3" />
                    Copied
                  </span>
                ) : (
                  command
                )}
              </span>
            </div>
          </div>
        </button>
      ))}
      <a
        href="/docs"
        className="group flex w-full items-center gap-2 rounded-md border border-border/60 bg-muted/20 px-3 py-2 transition-colors hover:border-primary/40 hover:bg-muted/30"
      >
        <BookOpen className="size-4 shrink-0 text-foreground" aria-hidden />
        <div className="flex flex-col gap-0.5">
          <span className="inline-flex items-center gap-1 font-medium text-xs text-foreground group-hover:text-primary transition-colors">
            Open docs
            <ArrowUpRight className="size-3" />
          </span>
        </div>
      </a>
    </div>
  );
}
