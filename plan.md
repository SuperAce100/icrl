# ICRL for Lean Theorem Proving - Integration Plan

## TL;DR - Simplest Path

```
miniF2F-lean4 (488 theorems) + LeanDojo (gym interface) + ICRL (trajectory DB)
```

1. **LeanDojo** = Python ↔ Lean bridge. Submit tactics, get proof states back.
2. **ICRL** = Store successful proofs in FAISS, retrieve similar ones as few-shot examples.
3. **miniF2F** = Benchmark. Start with Valid split (244), easy subset first.

**Hill-climb order:**
1. Single-tactic theorems (`ring`, `norm_num`, `simp` close ~15%)
2. `mathd_algebra_*`, `mathd_numbertheory_*` (AMC-style, cluster well)
3. `amc12_*`, `amc10_*`
4. Skip IMO for now

---

## Stack

```bash
# System
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh  # Lean version manager
export GITHUB_ACCESS_TOKEN=...  # Optional: helps avoid GitHub rate limits (LeanDojo/Lake may fetch deps)

# Python (3.9-3.11, NOT 3.12)
uv add icrl-py lean-dojo

# miniF2F setup (already at /home/simon/miniF2F-lean4)
cd /home/simon/miniF2F-lean4
lake exe cache get && lake build
```

**Models:**
- `kaiyuy/leandojo-lean4-tacgen-byt5-small` (300M, CPU-friendly)
- Or any LiteLLM model via `icrl.LiteLLMProvider`

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  ICRL Agent                                             │
│  ├── LLMProvider (tactic generation)                    │
│  ├── TrajectoryDatabase (FAISS)                         │
│  └── TrajectoryRetriever (semantic search)              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  LeanEnvironment (implements ICRL Environment protocol) │
│  └── LeanDojo Dojo (Lean RPC via Pantograph)            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  miniF2F-lean4 theorems                                 │
│  ├── Valid/ (244 theorems) ← START HERE                 │
│  └── Test/  (244 theorems)                              │
└─────────────────────────────────────────────────────────┘
```

---

## Minimal Implementation

### LeanEnvironment (wraps LeanDojo)

```python
from lean_dojo import Dojo, Theorem, ProofFinished, TacticState

class LeanEnvironment:
    """ICRL Environment protocol for Lean theorem proving."""
    
    def __init__(self, theorem: Theorem):
        self.theorem = theorem
        self.dojo = None
        self.state = None
    
    def reset(self, goal: str) -> str:
        """Enter Dojo, return initial proof state."""
        self.dojo, self.state = Dojo(self.theorem).__enter__()
        return self._format_state(self.state)
    
    def step(self, action: str) -> tuple[str, bool, bool]:
        """Run tactic, return (observation, done, success)."""
        result = self.dojo.run_tac(self.state, action)
        
        if isinstance(result, ProofFinished):
            return "Proof complete!", True, True
        
        if isinstance(result, TacticState):
            self.state = result
            return self._format_state(result), False, False
        
        # Error case
        return f"Error: {result}", False, False
    
    def _format_state(self, state: TacticState) -> str:
        """Format proof state for LLM."""
        goals = "\n".join(str(g) for g in state.goals)
        return f"Goals:\n{goals}"
    
    def close(self):
        if self.dojo:
            self.dojo.__exit__(None, None, None)
```

### Loading miniF2F theorems

```python
from lean_dojo import LeanGitRepo, trace

# Trace the repo (extracts theorem info, caches)
repo = LeanGitRepo("/home/simon/miniF2F-lean4", "main")
traced = trace(repo)

# Get all theorems from Valid split
valid_theorems = [
    thm for thm in traced.get_theorems()
    if "Valid" in thm.file_path
]

# Filter for easy ones (mathd_algebra, mathd_numbertheory)
easy_theorems = [
    thm for thm in valid_theorems
    if "mathd_algebra" in thm.full_name or "mathd_numbertheory" in thm.full_name
]
```

### ICRL Integration

```python
from icrl import Agent, LiteLLMProvider

LEAN_ACT_PROMPT = """Theorem: {goal}

Current proof state:
{observation}

{examples}

Output the next Lean 4 tactic. Examples: ring, norm_num, simp, linarith, exact h
Respond with ONLY the tactic."""

agent = Agent(
    llm=LiteLLMProvider(model="gpt-4o-mini"),
    db_path="./lean_trajectories",
    plan_prompt="",  # Skip planning for now
    reason_prompt="",  # Skip reasoning for now
    act_prompt=LEAN_ACT_PROMPT,
    k=3,
    max_steps=10,
)

# Train on easy theorems
for thm in easy_theorems:
    env = LeanEnvironment(thm)
    trajectory = agent.train_sync(env, goal=str(thm))
    if trajectory.success:
        print(f"Proved: {thm.full_name}")
```

---

## Trajectory Structure for Lean

```python
# What gets stored in FAISS DB:
{
    "goal": "theorem mathd_algebra_109 (a b : ℝ) (h₀ : 3*a + 2*b = 12) (h₁ : a = 4) : b = 0",
    "plan": "",
    "steps": [
        {
            "observation": "Goals:\n⊢ b = 0\n\nHypotheses:\na b : ℝ\nh₀ : 3*a + 2*b = 12\nh₁ : a = 4",
            "reasoning": "",
            "action": "linarith"
        }
    ],
    "success": True
}
```

Retrieval key: embed the goal (theorem statement). Similar theorems → similar tactics.

---

## Lemmas / `have` Tactics (LATER)
Lets do the most simple stuff first

**Problem:** LeanDojo sessions are isolated. A lemma proved in episode 1 can't be called in episode 2.

**Ideas to explore:**
- Store full proof blocks including `have` steps, prompt LLM to inline helpers
- Maintain persistent `.lean` file of discovered lemmas prepended to each session
- Cross-episode lemma reuse (what InternLM Step-Prover does)

**Decision:** Defer this. Focus on single-theorem proofs first.

---

## Implementation Roadmap

### Phase 1: Minimal Loop (NOW)

```bash
# Step 1: Add lean-dojo
cd /home/simon/icrl-math
uv add lean-dojo

# Step 2: Test LeanDojo works with miniF2F
python -c "from lean_dojo import *; print('OK')"
```

**Files to create:**
1. `src/icrl/lean/__init__.py`
2. `src/icrl/lean/environment.py` - LeanEnvironment wrapper
3. `src/icrl/lean/loader.py` - Load miniF2F theorems
4. `examples/lean_minif2f_demo.py` - End-to-end demo

**Target subset:** 
- `mathd_algebra_*` (~70 theorems in Valid)
- `mathd_numbertheory_*` (~40 theorems in Valid)
- Total: ~110 "easy" theorems to start

### Phase 2: Evaluation
1. Run on mathd_* subset first
2. Measure: success rate, avg proof length
3. Then expand to full Valid split

### Phase 3: Improvements (LATER)
1. Better prompts (add reasoning phase)
2. Curriculum: easy → hard
3. Error recovery: retry on tactic failure
4. Premise retrieval
5. Lemma reuse across episodes

---

## miniF2F Structure (at /home/simon/miniF2F-lean4)

```
MiniF2F/
├── Valid/           # 244 theorems (development set)
│   ├── mathd_algebra_*.lean      # ~70 (easiest)
│   ├── mathd_numbertheory_*.lean # ~40
│   ├── aime_*.lean               # ~30
│   ├── amc12_*.lean              # ~20
│   └── algebra_*.lean            # ~20
└── Test/            # 244 theorems (held-out)
```

**Theorem format:**
```lean
import Mathlib
set_option maxHeartbeats 0
open BigOperators Real Nat Topology Rat

theorem mathd_algebra_109 (a b : ℝ) (h₀ : 3 * a + 2 * b = 12) (h₁ : a = 4) : b = 0 := by sorry
```

---

## Easy Wins (Single-Tactic Proofs)

These should close with one tactic:

| Theorem | Likely Tactic |
|---------|---------------|
| `mathd_algebra_109` | `linarith` |
| `mathd_algebra_10` | `norm_num` |
| `mathd_algebra_104` | `linarith` or `field_simp` |
| `algebra_2rootsintpoly_am10tap11eqasqpam110` | `ring` |

Seed the trajectory DB with these first.

---

## References

- [LeanDojo](https://github.com/lean-dojo/LeanDojo) - Python ↔ Lean interface
- [miniF2F-lean4](https://github.com/yangky11/miniF2F-lean4) - Benchmark
- [ICRL](https://github.com/SuperAce100/icrl) - Trajectory-based in-context learning
- [LeanDojo Paper](https://arxiv.org/abs/2306.15626)

---

## Quick Start Commands

```bash
# Install lean optional deps
cd /home/simon/icrl-math
uv add --optional lean lean-dojo  # DONE

# Check theorem counts (no tracing needed)
uv run python -c "
from icrl.lean.loader import list_theorem_files, count_by_category
files = list_theorem_files()
print(f'Valid: {len(files[\"valid\"])} theorems')
print('By category:', count_by_category(files['valid']))
"
# Output: Valid: 244 theorems
# mathd: 130 (70 algebra + 60 numbertheory) ← START HERE

# Run demo (traces repo on first run, may take a few minutes)
export GITHUB_ACCESS_TOKEN=...  # Required by LeanDojo
uv run python examples/lean_minif2f_demo.py

# Or test single theorem manually
uv run python -c "
from icrl.lean import LeanEnvironment, MiniF2FLoader
loader = MiniF2FLoader()
loader.trace_repo()
thm = loader.get_mathd_algebra()[0]
env = LeanEnvironment(thm)
print(env.reset(str(thm)))
print(env.step('ring'))
"
```

---

## APPENDIX: Original Detailed Plan

<details>
<summary>Click to expand full analysis</summary>

## Current ICRL Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Agent                                                  │
│  ├── LLMProvider (generates plans/reasoning/actions)    │
│  ├── TrajectoryDatabase (FAISS-backed storage)          │
│  ├── TrajectoryRetriever (semantic search)              │
│  └── CurationManager (prunes low-utility trajectories)  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  ReActLoop: Plan → Reason → Act → Observe               │
│  - Environment.reset(goal) → initial observation        │
│  - Environment.step(action) → (obs, done, success)      │
└─────────────────────────────────────────────────────────┘
```

**Key abstractions:**
- `Environment` protocol: `reset(goal) → str`, `step(action) → (str, bool, bool)`
- `Trajectory`: goal, plan, steps (observation/reasoning/action), success
- `Step`: observation, reasoning, action

## Lean Ecosystem Options

### Option 1: LeanDojo (Recommended)

**What it is:** Python library for programmatic Lean interaction.

**Key components:**
- **Dojo**: Context manager for proof sessions
- **Tracing**: Extract theorems from Lean repos
- **TacticState/ProofFinished**: Result types

**API pattern:**
```python
from lean_dojo import Dojo, Theorem, ProofFinished

with Dojo(theorem) as (dojo, initial_state):
    result = dojo.run_tac(state, "simp")
    if isinstance(result, ProofFinished):
        print("Done!")
```

### Option 2: FineLeanCorpus (Later)

509k Lean theorems with difficulty ratings. Good for curriculum learning after miniF2F baseline.

## Lean-Specific Prompts

```python
LEAN_PLAN_PROMPT = """You are a Lean 4 theorem prover.

Theorem to prove: {goal}

{examples}

Create a proof strategy. Consider:
1. What type of theorem is this? (algebraic, logical, etc.)
2. What tactics are likely useful? (simp, ring, induction, etc.)
3. What lemmas might be needed?

Plan:"""

LEAN_REASON_PROMPT = """Theorem: {goal}
Strategy: {plan}

Current proof state:
{observation}

Previous tactics:
{history}

{examples}

Analyze the current state. What progress has been made? What remains?"""

LEAN_ACT_PROMPT = """Theorem: {goal}
Strategy: {plan}
Analysis: {reasoning}

Current proof state:
{observation}

Output the next tactic to apply. Respond with ONLY the tactic, e.g.:
simp [add_comm]
ring
exact h
apply Nat.add_assoc"""
```

## Key Design Decisions

### 1. Tactic Granularity
**Decision:** Single tactics per step (not sequences).

### 2. Error Handling
**Decision:** Allow 3-5 retries on tactic failure, then terminate episode.

### 3. Retrieval Strategy
**Decision:** Embed theorem statements, retrieve similar proofs.

</details>

```python
LEAN_PLAN_PROMPT = """You are a Lean 4 theorem prover.

Theorem to prove: {goal}

{examples}

Create a proof strategy. Consider:
1. What type of theorem is this? (algebraic, logical, etc.)
2. What tactics are likely useful? (simp, ring, induction, etc.)
3. What lemmas might be needed?

Plan:"""

LEAN_REASON_PROMPT = """Theorem: {goal}
Strategy: {plan}

Current proof state:
{observation}

Previous tactics:
{history}

{examples}

Analyze the current state. What progress has been made? What remains?"""

LEAN_ACT_PROMPT = """Theorem: {goal}
Strategy: {plan}
Analysis: {reasoning}

Current proof state:
{observation}

Output the next tactic to apply. Respond with ONLY the tactic, e.g.:
simp [add_comm]
ring
exact h
apply Nat.add_assoc"""
```

### Phase 3: Trajectory Adaptation

Lean trajectories have special structure:

```python
class LeanStep(Step):
    """Extended step for Lean proofs."""
    observation: str      # Proof state (goals + hypotheses)
    reasoning: str        # Why this tactic
    action: str           # Tactic applied
    
    # Lean-specific
    goals_before: list[str]
    goals_after: list[str]
    tactic_success: bool

class LeanTrajectory(Trajectory):
    """Extended trajectory for Lean proofs."""
    goal: str             # Theorem statement
    plan: str             # Proof strategy
    steps: list[LeanStep]
    success: bool         # Proof completed (no remaining goals)
    
    # Lean-specific
    theorem_name: str
    lean_code: str        # Full Lean code
    mathlib_deps: list[str]
    difficulty: int
    domain: list[str]
```

### Phase 4: FineLeanCorpus Integration

Load and use the dataset:

```python
from datasets import load_dataset

class FineLeanCorpusLoader:
    """Load theorems from FineLeanCorpus for training."""
    
    def __init__(self, difficulty_range: tuple[int, int] = (1, 5)):
        self.dataset = load_dataset("m-a-p/FineLeanCorpus", split="train")
        self.difficulty_range = difficulty_range
    
    def get_theorems(self, n: int, domains: list[str] = None) -> list[dict]:
        """Get n theorems matching criteria."""
        filtered = self.dataset.filter(
            lambda x: self.difficulty_range[0] <= x["difficulty"] <= self.difficulty_range[1]
        )
        if domains:
            filtered = filtered.filter(
                lambda x: any(d in x["domain_list"] for d in domains)
            )
        return list(filtered.shuffle().select(range(min(n, len(filtered)))))
    
    def to_environment(self, theorem: dict) -> LeanEnvironment:
        """Convert dataset entry to ICRL environment."""
        return LeanEnvironment(
            theorem=theorem["statement"],
            lean_code=theorem["lean_code"]
        )
```

---

## Implementation Roadmap

### Milestone 1: Dataset-Only Experiments (No Live Lean)
**Goal:** Test ICRL retrieval on Lean-style data without Lean toolchain.

1. Create `MockLeanEnvironment` using FineLeanCorpus `compile_result`
2. Parse pre-extracted proof states from dataset
3. Simulate tactic execution using stored data
4. Test trajectory storage and retrieval

**Deliverables:**
- `src/icrl/lean/mock_env.py`
- `src/icrl/lean/corpus_loader.py`
- `examples/lean_mock_demo.py`

### Milestone 2: LeanDojo-v2 Integration
**Goal:** Real Lean interaction via Pantograph.

1. Add `lean-dojo-v2` dependency
2. Implement `LeanEnvironment` with real Dojo
3. Handle Lean compilation and error recovery
4. Test on simple Mathlib theorems

**Deliverables:**
- `src/icrl/lean/environment.py`
- `src/icrl/lean/dojo_adapter.py`
- `examples/lean_live_demo.py`

### Milestone 3: Lean-Optimized Retrieval
**Goal:** Better retrieval for theorem proving.

1. Embed proof states (not just goals)
2. Retrieve by theorem structure similarity
3. Retrieve by tactic patterns
4. Consider premise retrieval (what lemmas to use)

**Deliverables:**
- `src/icrl/lean/retriever.py`
- `src/icrl/lean/embedder.py` (math-aware embeddings)

### Milestone 4: Curriculum Learning
**Goal:** Progressive difficulty training.

1. Start with easy theorems (difficulty 1-3)
2. Graduate to harder theorems as success rate improves
3. Track per-domain performance
4. Implement difficulty-aware curation

**Deliverables:**
- `src/icrl/lean/curriculum.py`
- `src/icrl/lean/difficulty_tracker.py`

### Milestone 5: Evaluation & Benchmarks
**Goal:** Measure performance on standard benchmarks.

1. Evaluate on miniF2F or similar
2. Compare with/without ICRL retrieval
3. Measure proof length, success rate, time

**Deliverables:**
- `benchmarks/minif2f_eval.py`
- `benchmarks/results/`

---

## Key Design Decisions to Discuss

### 1. Tactic Granularity
**Question:** Should each step be a single tactic or a tactic sequence?

- **Single tactic:** More fine-grained learning, but longer trajectories
- **Tactic sequence:** Faster proving, but harder to learn patterns

**Recommendation:** Start with single tactics, add sequence support later.

### 2. Proof State Representation
**Question:** How to represent proof state for embedding/retrieval?

Options:
- Raw Lean syntax
- Structured (goals + hypotheses as separate fields)
- Natural language description
- Hybrid

**Recommendation:** Structured representation with optional NL summary.

### 3. Error Handling
**Question:** How to handle tactic failures?

Options:
- Immediate episode termination
- Retry with different tactic (limited retries)
- Backtrack to previous state

**Recommendation:** Allow limited retries (3-5), then terminate.

### 4. Retrieval Strategy
**Question:** What to retrieve for in-context examples?

Options:
- Full proof trajectories (current ICRL approach)
- Similar proof states + successful tactics
- Relevant lemmas/premises
- Hybrid

**Recommendation:** Start with proof states + tactics, add premise retrieval.

### 5. LeanDojo-v2 vs Custom Integration
**Question:** Use LeanDojo-v2's agent/trainer or just the Dojo?

- **Full LeanDojo-v2:** Get their training pipeline, but less control
- **Dojo only:** More work, but ICRL's trajectory system stays central

**Recommendation:** Use Dojo for Lean interaction, keep ICRL for trajectory management.

---

## Dependencies to Add

```toml
# pyproject.toml additions
[project.optional-dependencies]
lean = [
    "lean-dojo-v2>=0.1.0",  # Lean interaction
    "datasets>=2.0.0",      # HuggingFace datasets
    "transformers>=4.30.0", # For math-aware embeddings
]
```

**System requirements:**
- Lean 4 toolchain (via elan)
- Git >= 2.25
- ~10GB disk for Mathlib cache

---

## Open Questions

1. **Mathlib version pinning:** Which Mathlib version to target? (affects theorem availability)

2. **Proof search strategy:** Pure LLM generation vs. hybrid with traditional search?

3. **Multi-step reasoning:** Should the "reason" phase do explicit proof planning?

4. **Verification:** How to verify generated proofs beyond "no goals remaining"?

5. **Scaling:** How many trajectories needed for meaningful improvement?

---

## Next Steps

1. **Discuss this plan** - Any concerns or alternative approaches?
2. **Set up LeanDojo-v2** - Install and test basic interaction
3. **Load FineLeanCorpus** - Explore the dataset structure
4. **Implement MockLeanEnvironment** - Start with offline experiments
5. **Design prompts** - Iterate on Lean-specific prompts

---

## References

- [LeanDojo-v2](https://github.com/lean-dojo/LeanDojo-v2)
- [FineLeanCorpus](https://huggingface.co/datasets/m-a-p/FineLeanCorpus)
- [Pantograph](https://github.com/lean-dojo/Pantograph)
- [LeanAgent Paper](https://arxiv.org/abs/2410.06209)
- [Original ICRL Paper](https://arxiv.org/abs/2312.10997)
