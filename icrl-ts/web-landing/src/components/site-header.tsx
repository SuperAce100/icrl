import Image from "next/image";
import Link from "next/link";

import { ModeToggle } from "@/components/mode-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center transition-opacity hover:opacity-80" aria-label="ICRL Home">
          <Image src="/logo_light.svg" alt="ICRL" width={62} height={32} className="dark:hidden" priority />
          <Image src="/logo_dark.svg" alt="ICRL" width={62} height={32} className="hidden dark:block" priority />
        </Link>
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
