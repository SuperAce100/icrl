# Lean Experiment Commands

Quick reference for running Lean theorem proving experiments with ICRL.

## Quick Start

```bash
# Run 1 toy theorem (no Lean/LeanDojo required)
uv run python experiments/lean/run.py --dataset toy --n 1

# Run 3 toy theorems
uv run python experiments/lean/run.py --dataset toy --n 3

# Run all 7 toy theorems
uv run python experiments/lean/run.py --dataset toy --n 7
```

## Datasets

| Dataset | Description | Requirements |
|---------|-------------|--------------|
| `toy` | 7 trivial theorems (mock env) | None |
| `minif2f` | miniF2F benchmark (real Lean) | GITHUB_ACCESS_TOKEN, Lean toolchain |

## Toy Dataset (No Setup Required)

```bash
# List available toy theorems
uv run python experiments/lean/run.py --list

# Run specific theorem by name
uv run python experiments/lean/run.py --dataset toy --theorem one_plus_one
uv run python experiments/lean/run.py --dataset toy --theorem simple_linarith

# Use different model
uv run python experiments/lean/run.py --dataset toy --n 1 --model gpt-4o-mini
uv run python experiments/lean/run.py --dataset toy --n 1 --model claude-3-5-sonnet-20241022
```

### Available Toy Theorems

| Name | Statement | Expected Tactic |
|------|-----------|-----------------|
| `one_plus_one` | `1 + 1 = 2` | `rfl` |
| `two_times_three` | `2 * 3 = 6` | `rfl` |
| `nat_refl` | `n = n` | `rfl` |
| `from_hyp` | `(h : P) : P` | `exact h` |
| `add_zero` | `n + 0 = n` | `rfl` |
| `simple_linarith` | `a + b = 10, a = 3 → b = 7` | `linarith` |
| `norm_num_example` | `2 + 3 = 5` | `norm_num` |

## miniF2F Dataset (Real Lean)

### Setup

```bash
# 1. Set GitHub token (required by LeanDojo)
export GITHUB_ACCESS_TOKEN=ghp_...

# 2. Ensure Lean toolchain is installed
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh

# 3. Build miniF2F (if not already done)
cd /home/simon/miniF2F-lean4
lake exe cache get && lake build
```

### Run

```bash
# Run 1 miniF2F theorem
uv run python experiments/lean/run.py --dataset minif2f --n 1

# Run 3 miniF2F theorems
uv run python experiments/lean/run.py --dataset minif2f --n 3

# Run specific theorem
uv run python experiments/lean/run.py --dataset minif2f --theorem mathd_algebra_109
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--dataset` | `toy` or `minif2f` | `toy` |
| `--n` | Number of theorems | `1` |
| `--theorem` | Specific theorem name | - |
| `--model` | LLM model | `gemini/gemini-2.0-flash` |
| `--max-steps` | Max proof steps | `5` |
| `--list` | List available theorems | - |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ICRL_MODEL` | Default model (overridden by `--model`) |
| `GITHUB_ACCESS_TOKEN` | Required for miniF2F/LeanDojo |
| `OPENAI_API_KEY` | For OpenAI models |
| `ANTHROPIC_API_KEY` | For Claude models |
| `GEMINI_API_KEY` | For Gemini models |

## Example Output

```
============================================================
  TOY DATASET (Mock Environment)
============================================================
Running 1 theorem(s)
Model: gemini/gemini-2.0-flash

[1/1] one_plus_one
  Statement: theorem one_plus_one : 1 + 1 = 2 := by sorry
  Expected: rfl
  ✓ Proved in 1 step(s)
  Step 1: rfl
         → Proof complete! No goals remaining.

============================================================
  RESULTS
============================================================
  Proved: 1/1 (100.0%)
```
