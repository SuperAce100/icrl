# icrl

In-Context Reinforcement Learning for LLM agents in TypeScript.

- Learn from successful trajectories
- Retrieve similar examples during planning/reasoning
- Run with OpenAI, Anthropic, or custom providers
- Use file-system or custom storage adapters

## Installation

```bash
npm install icrl
```

Install at least one provider SDK:

```bash
npm install openai
# or
npm install @anthropic-ai/sdk
```

## Quick Start

```ts
import OpenAI from "openai";
import { Agent, FileSystemAdapter, OpenAIEmbedder, OpenAIProvider } from "icrl";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const agent = new Agent({
  llm: new OpenAIProvider(openai, { model: "gpt-4o" }),
  embedder: new OpenAIEmbedder(openai, { model: "text-embedding-3-small" }),
  storage: new FileSystemAdapter("./trajectories"),
  planPrompt: `Goal: {goal}\n\nExamples:\n{examples}\n\nCreate a plan.`,
  reasonPrompt: `Goal: {goal}\nPlan: {plan}\n\nObservation: {observation}\nHistory:\n{history}\n\nExamples:\n{examples}\n\nReason about the next step.`,
  actPrompt: `Goal: {goal}\nPlan: {plan}\nReasoning: {reasoning}\n\nReturn only the next action.`,
  k: 3,
  maxSteps: 30,
});

await agent.init();

// Train (stores successful trajectories)
const trained = await agent.train(env, "Complete the task");

// Run (retrieves examples, no new storage)
const result = await agent.run(env, "Complete another task");
```

## API Overview

Main exports:

- `Agent`
- `FileSystemAdapter`
- `OpenAIProvider`
- `OpenAIEmbedder`
- `AnthropicProvider`
- `AnthropicVertexProvider`
- `TrajectoryDatabase`
- Types: `Environment`, `StepResult`, `LLMProvider`, `Embedder`

Full docs and guides: [icrl.dev](https://icrl.dev)

## Development

From `icrl-ts/`:

```bash
npm install
npm run build
npm run typecheck
npm run tests:run
```

Run examples:

```bash
npm run examples:run
```

## Publishing (Maintainers)

```bash
npm whoami
npm install
npm run release:check
npm version patch   # or minor / major
npm publish --access public
git push origin main --follow-tags
```

## License

MIT
