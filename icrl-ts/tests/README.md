# TypeScript Tests

This folder contains mock/local deterministic verification scripts.

## Run all tests

```bash
bun install
bun run tests:run
```

## Test index

| File | Verifies |
| --- | --- |
| `tests/basic.ts` | `Agent` lifecycle + `verifyTrajectory` + `onStep` callback behavior |
| `tests/batch.ts` | `seedTrajectories`, `trainBatch`, and `runBatch` behavior |
| `tests/database.ts` | `TrajectoryDatabase` and `FileSystemAdapter` persistence/search operations |
| `tests/retriever.ts` | `TrajectoryRetriever` retrieval + result tracking behavior |
| `tests/loop.ts` | Direct `ReActLoop` execution behavior |
| `tests/curation.ts` | `CurationManager` pruning and utility score behavior |
| `tests/models.ts` | schema validation and model formatting/utility helpers |
| `tests/providers.ts` | provider adapters with mocked SDK clients |

## Run a single test

```bash
bun run test:basic
bun run test:batch
bun run test:database
bun run test:retriever
bun run test:loop
bun run test:curation
bun run test:models
bun run test:providers
```
