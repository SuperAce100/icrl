"""Datasets for Lean theorem proving experiments.

Provides toy examples and interfaces to external datasets like miniF2F.
"""

from dataclasses import dataclass


@dataclass
class ToyTheorem:
    """A simple theorem for testing without LeanDojo tracing."""
    name: str
    statement: str
    expected_tactic: str
    description: str


TOY_THEOREMS = [
    ToyTheorem(
        name="one_plus_one",
        statement="theorem one_plus_one : 1 + 1 = 2 := by sorry",
        expected_tactic="rfl",
        description="Trivial: 1 + 1 = 2 by reflexivity",
    ),
    ToyTheorem(
        name="two_times_three", 
        statement="theorem two_times_three : 2 * 3 = 6 := by sorry",
        expected_tactic="rfl",
        description="Simple multiplication",
    ),
    ToyTheorem(
        name="nat_refl",
        statement="theorem nat_refl (n : Nat) : n = n := by sorry",
        expected_tactic="rfl",
        description="Reflexivity with variable",
    ),
    ToyTheorem(
        name="from_hyp",
        statement="theorem from_hyp (P : Prop) (h : P) : P := by sorry",
        expected_tactic="exact h",
        description="Use hypothesis directly",
    ),
    ToyTheorem(
        name="add_zero",
        statement="theorem add_zero_right (n : Nat) : n + 0 = n := by sorry",
        expected_tactic="rfl",
        description="Adding zero (definitional equality)",
    ),
    ToyTheorem(
        name="simple_linarith",
        statement="theorem simple_linarith (a b : ℤ) (h : a + b = 10) (h2 : a = 3) : b = 7 := by sorry",
        expected_tactic="linarith",
        description="Simple linear arithmetic",
    ),
    ToyTheorem(
        name="norm_num_example",
        statement="theorem norm_num_example : (2 : ℕ) + 3 = 5 := by sorry",
        expected_tactic="norm_num",
        description="Numeric computation",
    ),
]


def get_toy_theorems(n: int | None = None) -> list[ToyTheorem]:
    """Get toy theorems for testing.
    
    Args:
        n: Number of theorems to return. None returns all.
    """
    if n is None:
        return TOY_THEOREMS.copy()
    return TOY_THEOREMS[:n]


def get_toy_theorem_by_name(name: str) -> ToyTheorem | None:
    """Get a specific toy theorem by name."""
    for thm in TOY_THEOREMS:
        if thm.name == name:
            return thm
    return None
