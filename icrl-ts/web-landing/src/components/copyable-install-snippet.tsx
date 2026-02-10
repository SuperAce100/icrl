"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

const NPM_CMD = "npm i icrl";
const PIP_CMD = "pip install icrl-py";

export function CopyableInstallSnippet() {
  const [copied, setCopied] = useState<"npm" | "pip" | null>(null);

  const handleCopy = async (cmd: "npm" | "pip") => {
    const text = cmd === "npm" ? NPM_CMD : PIP_CMD;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(cmd);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      // Fallback for older browsers
      setCopied(null);
    }
  };

  return (
    <div
      className="border border-border/60 bg-muted/20 font-mono text-xs text-muted-foreground"
      role="group"
    >
      <div className="flex flex-col divide-y divide-border/60 sm:flex-row sm:divide-x sm:divide-y-0">
        <button
          type="button"
          onClick={() => handleCopy("npm")}
          className="group flex items-center justify-between gap-4 px-4 py-2.5 text-left transition-colors hover:bg-muted/40 hover:text-foreground"
          aria-label="Copy npm install command"
        >
          <span>{NPM_CMD}</span>
          {copied === "npm" ? (
            <Check className="size-3.5 shrink-0 text-primary" aria-hidden />
          ) : (
            <Copy className="size-3.5 shrink-0 opacity-50 group-hover:opacity-100" aria-hidden />
          )}
        </button>
        <button
          type="button"
          onClick={() => handleCopy("pip")}
          className="group flex items-center justify-between gap-4 px-4 py-2.5 text-left transition-colors hover:bg-muted/40 hover:text-foreground"
          aria-label="Copy pip install command"
        >
          <span>{PIP_CMD}</span>
          {copied === "pip" ? (
            <Check className="size-3.5 shrink-0 text-primary" aria-hidden />
          ) : (
            <Copy className="size-3.5 shrink-0 opacity-50 group-hover:opacity-100" aria-hidden />
          )}
        </button>
      </div>
    </div>
  );
}
