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
    <header className="">
      <div className="max-w-3xl mx-auto">
        {/* Top row: Logo + Tabs + DB Selector */}
        <div className="flex items-center justify-between py-3">
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <Image
              src="/logo_light.svg"
              alt="ICRL"
              width={62}
              height={32}
              className="dark:hidden"
            />
            <Image
              src="/logo_dark.svg"
              alt="ICRL"
              width={62}
              height={32}
              className="hidden dark:block"
            />
          </Link>

          {/* Center: Tabs */}
          <div className="flex items-center gap-2">
            {tabs && <div className="hidden md:block">{tabs}</div>}
            {databaseSelector && <div className="hidden sm:block">{databaseSelector}</div>}
          </div>
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
