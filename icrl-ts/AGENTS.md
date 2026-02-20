# AGENTS.md

## Scope
- Applies to everything under `icrl-ts/`.
- Overrides parent guidance for this subtree when there is conflict.

## Runtime + Tooling Baseline
- Use Bun for install/run/test tasks in this package.
- Do not introduce npm/pnpm-only workflows unless explicitly requested.
- Required versions:
  - Bun: `>=1.x`
  - Node runtime target: `>=18` (package `engines.node`)

## Package Structure
- Public entrypoint: `src/index.ts`
- Core loop and agent:
  - `src/agent.ts`
  - `src/loop.ts`
  - `src/retriever.ts`
  - `src/curation.ts`
- Persistence and storage abstractions:
  - `src/database.ts`
  - `src/storage.ts`
  - `src/adapters/filesystem.ts`
- Provider adapters:
  - `src/providers/openai.ts`
  - `src/providers/anthropic.ts`
  - `src/providers/anthropic-vertex.ts`

## Architecture Contracts
- `Agent` composes database + retriever + loop + curation manager.
- `Agent.init()` loads storage; `train()` and `run()` must preserve this lazy-init behavior.
- Prompt templates must preserve placeholder semantics:
  - `{goal}`, `{examples}`, `{plan}`, `{observation}`, `{reasoning}`, `{history}`.
- `Environment` compatibility:
  - `reset(goal)` may return immediately.
  - `step(action)` may be sync or async; both must remain supported.
- `StorageAdapter` abstraction is authoritative:
  - keep new persistence features behind adapter interfaces first.
  - avoid hardcoding filesystem assumptions into core classes.

## API Stability Expectations
- Treat exports from `src/index.ts` as public API.
- If adding/removing/changing exported names or option types:
  - update `icrl-ts/README.md`.
  - ensure `dist/*.d.ts` output remains correct via build.
- Keep parity with Python package behavior for core ICRL semantics unless intentionally diverging and documented.

## TypeScript Quality Bar
- Maintain strict TS compatibility (`tsconfig.json` strict settings).
- Avoid `any`; prefer exact interfaces, discriminated unions, and narrow types.
- Preserve ESM+CJS output compatibility (`tsup` build in `package.json`).
- Keep dependencies lightweight; avoid adding runtime deps without clear need.

## Bun-First Commands
- Install dependencies:
  - `cd icrl-ts && bun install`
- Typecheck:
  - `cd icrl-ts && bun run typecheck`
- Build (must pass before publishing or merging core changes):
  - `cd icrl-ts && bun run build`
- Tests:
  - `cd icrl-ts && bun run test:run`
  - if no tests exist yet, still run once to verify harness behavior.

## Validation Matrix by Change Type
- If editing `src/agent.ts`, `src/loop.ts`, `src/retriever.ts`, or `src/database.ts`:
  - run `typecheck` + `build` + `test:run`.
- If editing providers in `src/providers/*`:
  - run `typecheck` + `build`.
  - verify constructor option defaults remain documented.
- If editing only docs/comments:
  - run at least `typecheck` to catch accidental type regressions.

## Known Repo-Specific Notes
- `lint` script exists but currently fails without an ESLint config in this package.
- Do not block completion on lint until ESLint config is added.
- `examples/basic.ts` is useful for manual smoke checks but may require live API keys.

## Change Hygiene
- Keep edits scoped; avoid unrelated formatting-only churn.
- Do not commit generated build output in `dist/` unless explicitly requested.
- Update docs when behavior or public options change.
