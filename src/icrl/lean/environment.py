"""LeanDojo-based environment for ICRL."""

from lean_dojo import Dojo, ProofFinished, TacticState, Theorem


class LeanEnvironment:
    """ICRL Environment protocol implementation for Lean theorem proving.
    
    Wraps LeanDojo's Dojo to provide the standard ICRL interface:
    - reset(goal) -> initial observation
    - step(action) -> (observation, done, success)
    """

    def __init__(self, theorem: Theorem):
        self.theorem = theorem
        self._dojo: Dojo | None = None
        self._state: TacticState | None = None

    def reset(self, goal: str) -> str:
        """Enter the Dojo and return initial proof state."""
        if self._dojo is not None:
            self.close()
        self._dojo = Dojo(self.theorem)
        dojo_context, self._state = self._dojo.__enter__()
        self._dojo_context = dojo_context
        return self._format_state(self._state)

    def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute a tactic and return (observation, done, success)."""
        if self._dojo_context is None or self._state is None:
            return "Error: Environment not initialized. Call reset() first.", True, False

        action = action.strip()
        if not action:
            return "Error: Empty tactic", False, False

        try:
            result = self._dojo_context.run_tac(self._state, action)
        except Exception as e:
            return f"Error: {e}", False, False

        if isinstance(result, ProofFinished):
            return "Proof complete! No goals remaining.", True, True

        if isinstance(result, TacticState):
            self._state = result
            return self._format_state(result), False, False

        return f"Tactic failed: {result}", False, False

    def _format_state(self, state: TacticState) -> str:
        """Format proof state for LLM consumption."""
        if not state.goals:
            return "No goals."
        goals_str = "\n".join(f"  {i+1}. {g}" for i, g in enumerate(state.goals))
        return f"Goals:\n{goals_str}"

    def close(self):
        """Clean up Dojo resources."""
        if self._dojo is not None:
            try:
                self._dojo.__exit__(None, None, None)
            except Exception:
                pass
            self._dojo = None
            self._dojo_context = None
            self._state = None

    def __del__(self):
        self.close()
