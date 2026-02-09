# Examples

This folder is for demos.

## Minimal Start Here

- `examples/basic_openai_demo.py`  
  Minimal OpenAI-based ICRL run (`OPENAI_API_KEY` required).

- `examples/basic_anthropic_demo.py`  
  Minimal Anthropic-based ICRL run (`ANTHROPIC_API_KEY` required).

## Core Demos

- `examples/demo_with_real_llm.py`  
  File-system navigation demo with real LLM calls.

- `examples/harbor_coding_agent.py`  
  Harbor-style coding agent demo.

## Domain Demos

- `examples/it_support_demo/`
- `examples/exception_handling_demo/`
- `examples/preference_learning_demo/`
- `examples/codebase_patterns_demo/`

## Run

```bash
uv run python examples/basic_openai_demo.py
uv run python examples/basic_anthropic_demo.py
uv run python examples/demo_with_real_llm.py
uv run python examples/harbor_coding_agent.py
```

For all mock/offline verification scripts, see `tests/README.md`.
