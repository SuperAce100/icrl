"use client";

import { AlertTriangle } from "lucide-react";

interface ApiStatusBannerProps {
  message: string;
}

export function ApiStatusBanner({ message }: ApiStatusBannerProps) {
  return (
    <div className="bg-primary/5 border-b border-primary/20">
      <div className="max-w-6xl mx-auto px-6 py-2">
        <div className="flex items-center gap-2 text-sm text-primary">
          <AlertTriangle className="h-4 w-4" />
          <span>{message}</span>
        </div>
      </div>
    </div>
  );
}
