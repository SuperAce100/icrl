# TypeScript Demos

This folder contains demo-ready, real API examples.

## Run all demos

```bash
bun install
bun run examples:run
```

## Demo index

| File | Demonstrates |
| --- | --- |
| `examples/openai-demo.ts` | End-to-end `Agent` training run using `OpenAIProvider` + `OpenAIEmbedder` |
| `examples/anthropic-demo.ts` | End-to-end `Agent` training run using `AnthropicProvider` + local demo embedder |

## Run a single demo

```bash
bun run example:openai
bun run example:anthropic
```

These demos require credentials in the workspace root `.env`.

Mock-based verification scripts were moved to `tests/`.
