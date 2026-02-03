"use client";

import { Button } from "@/components/ui/button";
import { Zap } from "lucide-react";

interface YoloModeBannerProps {
  onStart: () => void;
}

export function YoloModeBanner({ onStart }: YoloModeBannerProps) {
  return (
    <div className="bg-linear-to-r from-primary/10 via-primary/5 to-icrl-yellow/10 rounded-xl p-6 border border-primary/20">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-primary/20">
            <Zap className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">YOLO Mode</h3>
            <p className="text-sm text-muted-foreground">
              Let AI generate prompts and answers. Just pick your preference!
            </p>
          </div>
        </div>
        <Button onClick={onStart} className="bg-primary hover:bg-primary/90 text-white">
          <Zap className="h-4 w-4 mr-2" />
          Start YOLO Mode
        </Button>
      </div>
    </div>
  );
}
