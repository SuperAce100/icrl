import Link from "next/link";

import { ModeToggle } from "@/components/mode-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-end px-6 py-4">
        <div className="flex items-center gap-2">
          <Link href="/docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Docs
          </Link>
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
