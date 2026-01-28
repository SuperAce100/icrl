"use client";

import { ConvexProvider, ConvexReactClient } from "convex/react";
import { ReactNode, useState } from "react";

// Create client outside component to avoid re-creating on every render
// The URL comes from environment variable
const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  const [client] = useState(() => {
    if (!convexUrl) {
      console.warn(
        "NEXT_PUBLIC_CONVEX_URL is not set. Convex features will not work."
      );
      // Return a dummy client that won't connect
      return new ConvexReactClient("https://placeholder.convex.cloud");
    }
    return new ConvexReactClient(convexUrl);
  });

  return <ConvexProvider client={client}>{children}</ConvexProvider>;
}
