# ICRL (TypeScript)

**In-Context Reinforcement Learning for LLM Agents**

TypeScript implementation of the ICRL algorithm, enabling LLM agents to bootstrap their own performance by learning from successful trajectories.

## Installation

```bash
npm install icrl
# or
yarn add icrl
# or
pnpm add icrl
```

You'll also need an LLM provider:

```bash
npm install openai
# or
npm install @anthropic-ai/sdk
```

## Quick Start

```typescript
import OpenAI from "openai";
import { Agent, OpenAIProvider, OpenAIEmbedder } from "icrl";

const openai = new OpenAI();

const agent = new Agent({
  llm: new OpenAIProvider(openai, { model: "gpt-4o" }),
  embedder: new OpenAIEmbedder(openai),
  dbPath: "./trajectories",
  planPrompt: `Goal: {goal}

Here are examples of similar tasks:
{examples}

Create a step-by-step plan to accomplish the goal.`,
  reasonPrompt: `Goal: {goal}
Plan: {plan}

Previous steps:
{history}

Current observation:
{observation}

Examples of similar situations:
{examples}

Think step by step about what to do next.`,
  actPrompt: `Goal: {goal}
Plan: {plan}
Your reasoning: {reasoning}

What is the next action? Respond with only the action.`,
  k: 3, // Number of examples to retrieve
  maxSteps: 30,
});

// Initialize (loads database from disk)
await agent.init();

// Training: successful trajectories are stored for future use
const trajectory = await agent.train(env, "Complete the task");

// Inference: uses stored examples but doesn't add new ones
const result = await agent.run(env, "Another task");
```

## Core Concepts

### The ICRL Algorithm

1. **Bootstrap Phase**: The agent attempts tasks, storing successful trajectories
2. **Retrieval**: At each decision point, semantically similar examples are retrieved
3. **Generation**: The LLM generates plans/reasoning/actions informed by examples
4. **Curation**: Low-utility trajectories are automatically pruned over time

### ReAct Loop

Each episode follows a **Plan → Reason → Act** loop:

```
┌─────────────────────────────────────────────────────────┐
│  1. PLAN: Generate high-level strategy using examples   │
├─────────────────────────────────────────────────────────┤
│  2. REASON: Analyze observation with retrieved context  │
├─────────────────────────────────────────────────────────┤
│  3. ACT: Execute action based on reasoning              │
├─────────────────────────────────────────────────────────┤
│  4. OBSERVE: Get environment feedback                   │
│     └─→ Loop back to REASON until done                  │
└─────────────────────────────────────────────────────────┘
```

## Implementing an Environment

```typescript
import type { Environment, StepResult } from "icrl";

class MyEnvironment implements Environment {
  private goal: string = "";

  reset(goal: string): string {
    this.goal = goal;
    return "Initial state description";
  }

  async step(action: string): Promise<StepResult> {
    // Execute the action
    const observation = await executeAction(action);

    // Check if goal is achieved
    const success = checkGoalAchieved(this.goal, observation);
    const done = success || isTerminal(observation);

    return { observation, done, success };
  }
}
```

## Custom LLM Provider

```typescript
import type { LLMProvider, Message } from "icrl";

class MyLLMProvider implements LLMProvider {
  async complete(messages: Message[]): Promise<string> {
    const response = await myLLMCall(messages);
    return response.text;
  }
}
```

## Custom Embedder

```typescript
import type { Embedder } from "icrl";

class MyEmbedder implements Embedder {
  readonly dimension = 768;

  async embed(texts: string[]): Promise<number[][]> {
    return await myEmbeddingService.embed(texts);
  }

  async embedSingle(text: string): Promise<number[]> {
    const [embedding] = await this.embed([text]);
    return embedding!;
  }
}
```

## Human Verification

Add a verification step before storing trajectories:

```typescript
const agent = new Agent({
  // ... other options
  verifyTrajectory: async (trajectory) => {
    console.log("Trajectory completed:");
    console.log(`Goal: ${trajectory.goal}`);
    console.log(`Steps: ${trajectory.steps.length}`);
    console.log(`Success: ${trajectory.success}`);

    const answer = await prompt("Store this trajectory? (y/n): ");
    return answer.toLowerCase() === "y";
  },
});
```

## API Reference

### `Agent`

Main class for training and running the ICRL agent.

#### Constructor Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `llm` | `LLMProvider` | required | LLM for generating completions |
| `embedder` | `Embedder` | required | Embedder for semantic search |
| `dbPath` | `string` | required | Path to trajectory database |
| `planPrompt` | `string` | required | Template with `{goal}`, `{examples}` |
| `reasonPrompt` | `string` | required | Template with `{goal}`, `{plan}`, `{observation}`, `{history}`, `{examples}` |
| `actPrompt` | `string` | required | Template with `{goal}`, `{plan}`, `{reasoning}`, `{history}`, `{examples}` |
| `k` | `number` | `3` | Number of examples to retrieve |
| `maxSteps` | `number` | `30` | Maximum steps per episode |
| `seedTrajectories` | `Trajectory[]` | `[]` | Initial examples |
| `onStep` | `function` | `undefined` | Step callback |
| `curationThreshold` | `number` | `0.3` | Utility threshold for pruning |
| `curationMinRetrievals` | `number` | `5` | Min retrievals before pruning |
| `verifyTrajectory` | `function` | `undefined` | Verification callback |

#### Methods

| Method | Description |
|--------|-------------|
| `init()` | Initialize agent (load database) |
| `train(env, goal)` | Run training episode, store successful trajectories |
| `run(env, goal)` | Run inference episode (database frozen) |
| `trainBatch(envFactory, goals)` | Train on multiple goals |
| `runBatch(envFactory, goals)` | Run inference on multiple goals |
| `getStats()` | Get database statistics |
| `getDatabase()` | Access the underlying `TrajectoryDatabase` |

### Providers

#### `OpenAIProvider`

```typescript
import OpenAI from "openai";
import { OpenAIProvider } from "icrl";

const provider = new OpenAIProvider(new OpenAI(), {
  model: "gpt-4o",
  temperature: 0.7,
  maxTokens: 4096,
});
```

#### `OpenAIEmbedder`

```typescript
import OpenAI from "openai";
import { OpenAIEmbedder } from "icrl";

const embedder = new OpenAIEmbedder(new OpenAI(), {
  model: "text-embedding-3-small",
});
```

#### `AnthropicProvider`

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { AnthropicProvider } from "icrl";

const provider = new AnthropicProvider(new Anthropic(), {
  model: "claude-sonnet-4-20250514",
  temperature: 0.7,
  maxTokens: 4096,
});
```

## Database Structure

```
./trajectories/
├── trajectories/
│   ├── <uuid-1>.json
│   ├── <uuid-2>.json
│   └── ...
└── curation.json
```

## License

MIT
