"use client";

import { HalftoneDots } from "@paper-design/shaders-react";

import { cn } from "@/lib/utils";

interface WorkflowHalftoneProps {
  image: string;
  label: string;
  className?: string;
  fitMode?: "box" | "fill";
}

export function WorkflowHalftone({ image, label, className, fitMode = "box" }: WorkflowHalftoneProps) {
  return (
    <div
      className={cn("relative w-full overflow-hidden", fitMode === "box" && "aspect-[16/10]", className)}
      aria-label={label}
      role="img"
    >
      <HalftoneDots
        className="h-full w-full"
        width={1280}
        height={720}
        image={image}
        colorBack="#f2f1e8"
        colorFront="#2b2b2b"
        originalColors={false}
        type="gooey"
        grid="hex"
        inverted={false}
        size={0.5}
        radius={1.25}
        contrast={0.4}
        grainMixer={0.2}
        grainOverlay={0.2}
        grainSize={0.5}
        fit="cover"
      />
    </div>
  );
}
