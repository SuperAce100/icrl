"use client";

import { useParams, useRouter, usePathname } from "next/navigation";
import { useQuery } from "convex/react";
import { api } from "../../../convex/_generated/api";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { DatabaseSelector } from "@/components/database-selector";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Database, Loader2, BicepsFlexed, Milestone, MessageCircle } from "lucide-react";
import { toSlug, type TabSlug } from "@/lib/slug";
import type { Id } from "../../../convex/_generated/dataModel";
import { GrainGradient } from "@paper-design/shaders-react";

export default function DatabaseLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const dbSlug = params.dbSlug as string;

  // Get the current tab from pathname
  const pathParts = pathname.split("/");
  const currentTab = (pathParts[2] || "train") as TabSlug;

  // Query the database by slug
  const database = useQuery(api.databases.getBySlug, { slug: dbSlug });
  const databases = useQuery(api.databases.list);

  const handleDbSelect = (id: Id<"databases"> | null) => {
    if (!id) return;
    const db = databases?.find((d) => d._id === id);
    if (db) {
      router.push(`/${toSlug(db.name)}/${currentTab}`);
    }
  };

  const handleTabChange = (tab: string) => {
    router.push(`/${dbSlug}/${tab}`);
  };

  // Loading state
  if (database === undefined) {
    return (
      <main className="min-h-screen flex flex-col relative">
        <div className="fixed inset-0 -z-10">
          <GrainGradient
            style={{ width: "100%", height: "100%" }}
            colors={["#ffedd6"]}
            colorBack="#fafaf9"
            softness={0.7}
            intensity={0.15}
            noise={0.5}
            shape="wave"
            speed={1}
            scale={1.24}
          />
        </div>
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
        <Footer />
      </main>
    );
  }

  // Database not found
  if (database === null) {
    return (
      <main className="min-h-screen flex flex-col relative">
        <div className="fixed inset-0 -z-10">
          <GrainGradient
            style={{ width: "100%", height: "100%" }}
            colors={["#ffedd6"]}
            colorBack="#fafaf9"
            softness={0.7}
            intensity={0.15}
            noise={0.5}
            shape="wave"
            speed={1}
            scale={1.24}
          />
        </div>
        <Header
          databaseSelector={<DatabaseSelector selectedId={null} onSelect={handleDbSelect} />}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-semibold">Database not found</h1>
            <p className="text-muted-foreground">
              The database &quot;{dbSlug}&quot; doesn&apos;t exist.
            </p>
          </div>
        </div>
        <Footer />
      </main>
    );
  }

  const headerTabs = (
    <Tabs value={currentTab} onValueChange={handleTabChange}>
      <TabsList className="h-9 bg-transparent">
        <TabsTrigger
          value="ask"
          className="flex items-center gap-1.5 text-sm data-[state=active]:text-primary data-[state=active]:bg-transparent"
        >
          <MessageCircle className="h-3.5 w-3.5" />
          Ask
        </TabsTrigger>
        <TabsTrigger
          value="train"
          className="flex items-center gap-1.5 text-sm data-[state=active]:text-primary data-[state=active]:bg-transparent"
        >
          <BicepsFlexed className="h-3.5 w-3.5" />
          Learn
        </TabsTrigger>
        <TabsTrigger
          value="memory"
          className="flex items-center gap-1.5 text-sm data-[state=active]:text-primary data-[state=active]:bg-transparent"
        >
          <Database className="h-3.5 w-3.5" />
          Examples
        </TabsTrigger>
        <TabsTrigger
          value="settings"
          className="flex items-center gap-1.5 text-sm data-[state=active]:text-primary data-[state=active]:bg-transparent"
        >
          <Milestone className="h-3.5 w-3.5" />
          Instructions
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );

  return (
    <main className="min-h-screen flex flex-col relative">
      {/* Grain Gradient Background */}
      <div className="fixed inset-0 -z-10">
        <GrainGradient
          style={{ width: "100%", height: "100%" }}
          colors={["#ffedd6"]}
          colorBack="#fafaf9"
          softness={0.7}
          intensity={0.15}
          noise={0.5}
          shape="wave"
          speed={1}
          scale={1.24}
        />
      </div>

      <Header
        tabs={headerTabs}
        databaseSelector={<DatabaseSelector selectedId={database._id} onSelect={handleDbSelect} />}
      />

      {/* Main Content - Narrower */}
      <div className="max-w-3xl mx-auto py-8 flex-1 w-full flex flex-col">{children}</div>

      <Footer />
    </main>
  );
}
