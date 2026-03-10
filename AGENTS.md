# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

ICRL (In-Context Reinforcement Learning) is a monorepo with:
- **Python library** (`src/icrl/`): core ICRL agent, uses `uv` for package management (see `pyproject.toml`)
- **TypeScript library** (`icrl-ts/`): TS port, uses `bun` for package management (has `bun.lock`)
- **Web landing** (`icrl-ts/web-landing/`): Next.js 16 marketing site, uses `bun`
- **Web example** (`icrl-ts/web-example/`): Next.js 16 demo app requiring Convex (`NEXT_PUBLIC_CONVEX_URL`), uses `bun`

### Running services

| Service | Command | Port | Notes |
|---|---|---|---|
| Web landing | `cd icrl-ts/web-landing && bun run dev` | 3000 | Works standalone |
| Web example | `cd icrl-ts/web-example && bun run dev` | 3001 | Needs `NEXT_PUBLIC_CONVEX_URL` for full functionality |
| ICRL CLI | `uv run icrl --help` | N/A | Typer CLI entry point |

### Lint / Test / Build commands

See `README.md`, `tests/README.md`, and `icrl-ts/tests/README.md` for full details. Key commands:

**Python:**
- Lint: `uv run ruff check src/icrl/` (pre-existing warnings exist)
- Tests: `uv run python tests/test_with_mock.py`, `uv run python tests/agent_api_walkthrough.py`, `uv run python tests/database_api_walkthrough.py`
- Pytest: `uv run --with pytest python -m pytest tests/test_harbor_coding.py -v`

**TypeScript library (`icrl-ts/`):**
- Typecheck: `bun run typecheck`
- Tests: `bun run tests:run` (runs 8 deterministic test suites)
- Build: `bun run build`
- Lint: ESLint config is not present; `bun run lint` will fail

### Non-obvious caveats

- The `icrl-ts/` directory has both `bun.lock` and `package-lock.json`. Use `bun` per user preference.
- The `icrl-ts/web-example/` has a `pnpm-lock.yaml` but `bun install` works fine.
- ESLint is configured as a devDependency in `icrl-ts/package.json` but there is no `.eslintrc` config file, so `bun run lint` fails. This is a pre-existing repo issue.
- Python `ruff check` has ~112 pre-existing lint warnings (unused imports, etc.).
- The web-example app requires `NEXT_PUBLIC_CONVEX_URL` to be set for full functionality; without it, the page shows a loading spinner.
- All Python and TS tests are fully offline/deterministic using mock LLMs; no API keys are needed for testing.
- `uv sync` downloads large dependencies (PyTorch, CUDA libs) on first run (~2GB). Subsequent runs are fast.
- `PATH` must include `$HOME/.bun/bin` and `$HOME/.local/bin` for `bun` and `uv` commands.
