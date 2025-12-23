"""ICICL: In-Context ICL for LLM Agents.

This package implements the Self-Generated In-Context Learning algorithm from:
"Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks"

Example usage:

    from icicl import Agent, LiteLLMProvider, Trajectory, Step

    agent = Agent(
        llm=LiteLLMProvider(model="gpt-4o-mini"),
        db_path="./trajectories",
        plan_prompt="Given goal: {goal}\\nExamples:\\n{examples}\\nCreate a plan:",
        reason_prompt="Goal: {goal}\\nPlan: {plan}\\nObservation: {observation}\\nThink:",
        act_prompt="Goal: {goal}\\nPlan: {plan}\\nReasoning: {reasoning}\\nAction:",
        k=3,
        max_steps=30,
    )

    # Training mode - accumulates successful trajectories
    trajectory = await agent.train(env, goal="Complete the task")

    # Inference mode - uses frozen database
    trajectory = await agent.run(env, goal="Complete another task")
"""

from icicl.agent import Agent
from icicl.models import Message, Step, StepContext, Trajectory
from icicl.protocols import Environment, LLMProvider
from icicl.providers import LiteLLMProvider

__all__ = [
    "Agent",
    "Environment",
    "LiteLLMProvider",
    "LLMProvider",
    "Message",
    "Step",
    "StepContext",
    "Trajectory",
]

__version__ = "0.1.0"
