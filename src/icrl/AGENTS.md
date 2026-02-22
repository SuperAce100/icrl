# AGENTS.md

## Scope
- Applies to `src/icrl/` and all subdirectories.
- Supplements repository-level guidance with Python package specifics.

## Package Purpose
- Python implementation of ICRL core algorithms and CLI tooling.
- Primary public API surface:
  - `icrl.Agent`
  - `icrl.LiteLLMProvider`
  - `icrl.AnthropicVertexProvider`
  - models/protocols exported in `src/icrl/__init__.py`

## Architecture Contracts
- `Agent` is the orchestrator; it should compose rather than duplicate logic from:
  - `TrajectoryDatabase`
  - `TrajectoryRetriever`
  - `ReActLoop`
  - `CurationManager`
- `ReActLoop` owns plan/reason/act execution behavior and prompt formatting.
- `TrajectoryDatabase` owns persistence and retrieval index management.
- `src/icrl/cli/` code should remain CLI-oriented and must not leak CLI-only assumptions into core library modules.

## Behavioral Guarantees
- Keep prompt-template placeholder support intact:
  - `{goal}`, `{examples}`, `{plan}`, `{observation}`, `{reasoning}`, `{history}`.
- Preserve mixed sync/async environment semantics:
  - `env.reset(...)` sync behavior must continue to work.
  - `env.step(...)` may be sync or awaitable.
- Do not break trajectory persistence compatibility without an explicit migration plan:
  - `trajectories/*.json`
  - `index.faiss`
  - `index_ids.json`
  - `embedder.json`
  - `curation.json`
- Preserve LiteLLM async worker workaround in package/CLI entrypoints:
  - set `litellm.disable_logging_worker = True` before normal runtime use.

## Implementation Guidance
- Python target: 3.12+.
- Favor explicit typing and small, composable functions.
- Keep non-deterministic behavior and side effects out of core algorithm code paths where possible.
- Add comments only where logic is non-obvious; avoid commentary noise.

## Validation Commands
- Install/update dependencies:
  - `uv sync`
  - for development tools: `uv sync --group dev`
- Lint:
  - `uv run ruff check src examples`
- Focused tests:
  - `uv run pytest -q examples/test_harbor_coding.py`
- End-to-end mock smoke test for loop/db/retrieval changes:
  - `uv run python examples/test_with_mock.py`

## Docs + API Hygiene
- If changing public behavior or constructor options:
  - update the repository `README.md`
  - update relevant docs under `docs/`
- If changing semantics shared with TypeScript core, keep parity or document intentional divergence.
