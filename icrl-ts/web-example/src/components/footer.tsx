"use client";

import { BookOpen } from "lucide-react";
import Link from "next/link";
export function Footer() {
  return (
    <footer className="mt-auto">
      <div className="max-w-3xl mx-auto px-6 py-4 pt-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            Built with{" "}
            <Link href="/" className="text-primary hover:underline">
              ICRL
            </Link>{" "}
            in 2026
          </p>
          <nav className="flex items-center gap-4">
            <Link
              href="/docs"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <BookOpen className="size-3" />
              <span>Docs</span>
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
