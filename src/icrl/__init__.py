"""ICRL: In-Context Reinforcement Learning for LLM Agents.

This package implements the In-Context Reinforcement Learning algorithm from:
"In-Context Reinforcement Learning Examples Improve LLM Agents for "
"Sequential Decision-Making Tasks"

Example usage:

    from icrl import Agent, LiteLLMProvider, Trajectory, Step

    agent = Agent(
        llm=LiteLLMProvider(model="gpt-4o-mini"),
        db_path="./trajectories",
        plan_prompt="Given goal: {goal}\\nExamples:\\n{examples}\\nCreate a plan:",
        reason_prompt=(
            "Goal: {goal}\\nPlan: {plan}\\nObservation: {observation}\\nThink:"
        ),
        act_prompt="Goal: {goal}\\nPlan: {plan}\\nReasoning: {reasoning}\\nAction:",
        k=3,
        max_steps=30,
    )

    # Training mode - accumulates successful trajectories
    trajectory = await agent.train(env, goal="Complete the task")

    # Inference mode - uses frozen database
    trajectory = await agent.run(env, goal="Complete another task")
"""

# Disable LiteLLM's async logging worker BEFORE any litellm import.
# This avoids event loop mismatch errors when asyncio.run() is called
# multiple times (e.g., in interactive chat mode).
import litellm as _litellm

_litellm.disable_logging_worker = True
del _litellm

from icrl.agent import Agent  # noqa: E402
from icrl.models import Message, Step, StepContext, Trajectory  # noqa: E402
from icrl.protocols import Environment, LLMProvider  # noqa: E402
from icrl.providers import (  # noqa: E402
    AnthropicVertexProvider,
    GeminiVertexProvider,
    LiteLLMProvider,
)

__all__ = [
    "Agent",
    "AnthropicVertexProvider",
    "Environment",
    "GeminiVertexProvider",
    "LiteLLMProvider",
    "LLMProvider",
    "Message",
    "Step",
    "StepContext",
    "Trajectory",
]

# Optional Harbor integration exports
try:
    from icrl.harbor import (  # noqa: F401
        HarborEnvironmentAdapter,
        ICRLTestAgent,
        ICRLTrainAgent,
    )

    __all__.extend(
        [
            "HarborEnvironmentAdapter",
            "ICRLTrainAgent",
            "ICRLTestAgent",
        ]
    )
except ImportError:
    # Harbor not installed, skip harbor-specific exports
    pass

__version__ = "0.1.0"
