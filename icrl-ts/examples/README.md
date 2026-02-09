# TypeScript Demos

This folder contains demo-ready, real API examples.

## Run core demos

```bash
bun install
bun run examples:run
```

## Demo index

| File | Use case |
| --- | --- |
| `examples/openai-demo.ts` | Basic end-to-end `Agent` training run with `OpenAIProvider` + `OpenAIEmbedder` |
| `examples/anthropic-demo.ts` | Basic end-to-end `Agent` training run with `AnthropicProvider` |
| `examples/support-triage-demo.ts` | Customer support triage automation (routing + structured customer reply) |
| `examples/incident-response-demo.ts` | On-call incident first-response playbook generation |
| `examples/web-convex-demo.ts` | `web-example` integration: uses `web-example`'s `ConvexAdapter` for persistent storage |

## Run a single demo

```bash
bun run example:openai
bun run example:anthropic
bun run example:support
bun run example:incident
bun run example:web
```

## Web-example integration demo

`examples/web-convex-demo.ts` requires additional env vars:

- `NEXT_PUBLIC_CONVEX_URL`

Optional:
- `ICRL_CONVEX_DATABASE_ID` (auto-created if omitted)

Run all demos including web storage integration:

```bash
bun run examples:run:all
```
