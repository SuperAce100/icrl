"use client";

import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";

interface HeaderProps {
  tabs?: ReactNode;
  databaseSelector?: ReactNode;
}

export function Header({ tabs, databaseSelector }: HeaderProps) {
  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-md sticky top-0 z-10">
      <div className="max-w-3xl mx-auto px-6">
        {/* Top row: Logo + Tabs + DB Selector */}
        <div className="flex items-center justify-between py-3">
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <Image
              src="/logo_light.png"
              alt="ICRL"
              width={32}
              height={32}
              className="dark:hidden"
            />
            <Image
              src="/logo_dark.png"
              alt="ICRL"
              width={32}
              height={32}
              className="hidden dark:block"
            />
          </Link>

          {/* Center: Tabs */}
          {tabs && <div className="hidden md:block">{tabs}</div>}

          {/* Right: Database selector */}
          {databaseSelector && <div className="hidden sm:block">{databaseSelector}</div>}
        </div>

        {/* Mobile row: Tabs + Database selector */}
        {(tabs || databaseSelector) && (
          <div className="flex items-center justify-between gap-4 pb-3 md:hidden">
            {tabs}
            {databaseSelector && <div className="sm:hidden">{databaseSelector}</div>}
          </div>
        )}
      </div>
    </header>
  );
}
