"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { ApiStatusBanner } from "@/components/api-status-banner";
import { DatabaseSelector } from "@/components/database-selector";
import { checkApiStatus } from "@/lib/actions";
import { toSlug } from "@/lib/slug";
import { Loader2, Database } from "lucide-react";
import type { Id } from "../../convex/_generated/dataModel";
import { GrainGradient } from "@paper-design/shaders-react";

function Background() {
  return (
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
  );
}

export default function Home() {
  const router = useRouter();
  const databases = useQuery(api.databases.list);
  const [apiStatus, setApiStatus] = useState<{
    configured: boolean;
    message: string;
  } | null>(null);

  // Check API status on mount
  useEffect(() => {
    checkApiStatus().then(setApiStatus);
  }, []);

  // Redirect to first database if available
  useEffect(() => {
    if (databases && databases.length > 0) {
      const firstDb = databases[0];
      router.replace(`/${toSlug(firstDb.name)}/train`);
    }
  }, [databases, router]);

  const handleDbSelect = (id: Id<"databases"> | null) => {
    if (!id) return;
    const db = databases?.find((d) => d._id === id);
    if (db) {
      router.push(`/${toSlug(db.name)}/train`);
    }
  };

  // Show loading while checking for databases
  if (databases === undefined) {
    return (
      <main className="min-h-screen flex flex-col relative">
        <Background />
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
        <Footer />
      </main>
    );
  }

  // No databases - show welcome screen
  return (
    <main className="min-h-screen flex flex-col relative">
      <Background />
      <Header />

      {apiStatus && !apiStatus.configured && <ApiStatusBanner message={apiStatus.message} />}

      <div className="max-w-3xl mx-auto px-6 py-16 flex-1 w-full">
        <div className="text-center space-y-8">
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
              <Database className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-3xl font-semibold tracking-tight">Welcome to ICRL</h1>
            <p className="text-muted-foreground max-w-md mx-auto">
              In-Context Reinforcement Learning. Create a database to start training your AI with
              human feedback.
            </p>
          </div>

          <div className="flex justify-center">
            <DatabaseSelector selectedId={null} onSelect={handleDbSelect} />
          </div>
        </div>
      </div>

      <Footer />
    </main>
  );
}
