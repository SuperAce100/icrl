import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ICRL — In-Context Reinforcement Learning",
    short_name: "ICRL",
    description:
      "A trajectory-learning framework that lets LLM agents improve continuously at runtime without retraining.",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0a",
    theme_color: "#F88D39",
    icons: [
      {
        src: "/favicon.png",
        sizes: "any",
        type: "image/png",
      },
    ],
  };
}
