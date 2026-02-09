# TypeScript Examples

All examples are deterministic and run offline using mocked providers/embedders.

## Run everything

```bash
bun install
bun run examples:run
```

## Example index

| File | Demonstrates |
| --- | --- |
| `examples/basic.ts` | `Agent` lifecycle (`init`, `train`, `run`, `getStats`), `verifyTrajectory`, and `onStep` callbacks |
| `examples/batch.ts` | `seedTrajectories`, `trainBatch`, and `runBatch` |
| `examples/database.ts` | `TrajectoryDatabase` + `FileSystemAdapter`: `load`, `add`, `search`, `searchSteps`, `recordRetrieval`, `remove`, persistence |
| `examples/retriever.ts` | `TrajectoryRetriever`: `retrieveForPlan`, `retrieveForStep`, retrieval tracking, `recordEpisodeResult` |
| `examples/loop.ts` | Direct `ReActLoop` execution |
| `examples/curation.ts` | `CurationManager`: `getLowUtilityTrajectories`, `maybeCurate`, `getUtilityScores` |
| `examples/models.ts` | Schemas (`MessageSchema`, `StepSchema`, `StepExampleSchema`, `TrajectorySchema`, `StepContextSchema`, `CurationMetadataSchema`) and formatting/utility helpers |
| `examples/providers.ts` | `OpenAIProvider`, `OpenAIEmbedder`, `AnthropicProvider`, `AnthropicVertexProvider`, `ANTHROPIC_VERTEX_MODEL_ALIASES` |
| `examples/openai-live.ts` | Live network integration for `OpenAIProvider` + `OpenAIEmbedder` with `Agent` |
| `examples/anthropic-live.ts` | Live network integration for `AnthropicProvider` with `Agent` |

## Run a single example

```bash
bun run example:basic
bun run example:batch
bun run example:database
bun run example:retriever
bun run example:loop
bun run example:curation
bun run example:models
bun run example:providers
bun run example:live:openai
bun run example:live:anthropic
```

## Run live examples only

These hit real APIs and require credentials in the workspace root `.env`.

```bash
bun run examples:run:live
```
