import Image from "next/image";
import Link from "next/link";

import { ModeToggle } from "@/components/mode-toggle";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <Image src="/logo_light.svg" alt="ICRL" width={62} height={32} className="dark:hidden" />
          <Image
            src="/logo_dark.svg"
            alt="ICRL"
            width={62}
            height={32}
            className="hidden dark:block"
          />
        </Link>
        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 md:flex">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/">Landing</Link>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/docs">Docs</Link>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href="#why">Why ICRL</a>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href="#use-cases">Use Cases</a>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href="#vs-rl">ICRL vs RL</a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener">
                Paper
              </a>
            </Button>
          </div>
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
