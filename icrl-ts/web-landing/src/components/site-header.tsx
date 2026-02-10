import Image from "next/image";
import Link from "next/link";

import { ModeToggle } from "@/components/mode-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/85 backdrop-blur-xl">
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
          <div className="hidden items-center gap-5 md:flex">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Landing
            </Link>
            <Link href="/docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Docs
            </Link>
            <a href="#why" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Why ICRL
            </a>
            <a href="https://arxiv.org/abs/2505.00234" target="_blank" rel="noreferrer noopener" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Paper
            </a>
          </div>
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
