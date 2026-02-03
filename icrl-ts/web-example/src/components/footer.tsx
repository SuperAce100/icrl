"use client";

export function Footer() {
  return (
    <footer className="border-t mt-auto">
      <div className="max-w-6xl mx-auto px-6 py-6">
        <p className="text-center text-xs text-muted-foreground">
          Built with{" "}
          <a href="https://github.com/SuperAce100/icrl" className="text-primary hover:underline">
            ICRL
          </a>{" "}
          &bull; In-Context Reinforcement Learning for LLM Agents
        </p>
      </div>
    </footer>
  );
}
