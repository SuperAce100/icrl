# Tests

This folder is for verification and mock-driven checks.

## Scripted Checks

- `tests/test_with_mock.py`  
  Offline integration-style test using `examples/mock_llm.py` and the file-system environment.

- `tests/agent_api_walkthrough.py`  
  Offline assertions for Agent API coverage (`train`, `run`, sync/batch, seeding, verification).

- `tests/database_api_walkthrough.py`  
  Offline assertions for database/retrieval/curation/validation APIs.

## Pytest Suite

- `tests/test_harbor_coding.py`  
  Unit/integration tests for the Harbor coding environment and prompts.

## Run

```bash
uv run python tests/test_with_mock.py
uv run python tests/agent_api_walkthrough.py
uv run python tests/database_api_walkthrough.py
uv run --with pytest python -m pytest tests/test_harbor_coding.py -v
```
