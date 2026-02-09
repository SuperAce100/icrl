# AGENTS.md

## Scope
- Applies to the entire repository unless a deeper `AGENTS.md` overrides it.
- `icrl-ts/AGENTS.md` is authoritative for files under `icrl-ts/`.

## Repository Map
- Python package: `src/icrl/`
- TypeScript package: `icrl-ts/src/`
- Python examples/tests: `examples/`
- Docs/content: `docs/`

## Cross-Package Rules (Python + TypeScript)
- Treat `src/icrl/*` and `icrl-ts/src/*` as sibling implementations of the same core ICRL concepts (`Agent`, loop, retriever, database, curation, providers).
- When changing core algorithm behavior in one package, either:
  - implement the equivalent change in the other package, or
  - leave a clear TODO + docs note explaining intentional divergence.
- Keep public API docs aligned with real source behavior (README and docs should not drift from code).
- Never commit runtime artifacts or local data:
  - `.icrl/`, `data/`, `runs/`, `harbor_jobs/`, `*_db`, local credential files.

## Python Package Instructions (`src/icrl/`)

### Architecture Contracts
- `Agent` composes `TrajectoryDatabase`, `TrajectoryRetriever`, `ReActLoop`, and `CurationManager`.
- `ReActLoop` is the control loop for plan/reason/act and prompt formatting.
- `TrajectoryDatabase` persists trajectories and retrieval indexes (FAISS + JSON metadata).
- CLI code in `src/icrl/cli/` is separate from core library logic; keep imports and responsibilities clean.

### Behavior Requirements
- Maintain placeholder compatibility for prompt templates:
  - `{goal}`, `{examples}`, `{plan}`, `{observation}`, `{reasoning}`, `{history}`.
- Preserve sync+async environment support in loop execution (`env.step(...)` may be awaitable or immediate).
- Keep LiteLLM worker disabling behavior intact:
  - `litellm.disable_logging_worker = True` must happen before broader runtime usage in package/CLI entrypoints.
- Preserve DB on-disk compatibility unless intentionally versioning:
  - trajectories JSON files
  - `index.faiss`, `index_ids.json`, `embedder.json`, `curation.json`.

### Code Style
- Target runtime is Python 3.12+ (`pyproject.toml`).
- Prefer typed function signatures and explicit return types.
- Follow Ruff rules configured in `pyproject.toml` (`E`, `F`, `I`, `UP`).
- Keep library code deterministic and side-effect aware (avoid debug prints in core paths).

### Validation (Python)
- Install deps: `uv sync` (or `uv sync --group dev`).
- Lint: `uv run ruff check src examples`.
- Run focused tests when behavior changes:
  - `uv run pytest -q examples/test_harbor_coding.py`
- Run smoke demo when loop/retrieval/db behavior changes:
  - `uv run python examples/test_with_mock.py`

## TypeScript Package Instructions (`icrl-ts/`)
- Follow `icrl-ts/AGENTS.md` for implementation details and validation in that subtree.
- At minimum for TS edits, run:
  - `cd icrl-ts && bun run typecheck`
  - `cd icrl-ts && bun run build`

## Change Hygiene
- Keep diffs focused; avoid unrelated refactors.
- If public APIs change, update both:
  - Python docs (`README.md`, `docs/`)
  - TypeScript docs (`icrl-ts/README.md`)
- Prefer backward-compatible evolution; call out breaking changes explicitly.
