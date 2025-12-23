"""SGICL: Self-Generated In-Context Learning for LLM Agents.

This package implements the SGICL algorithm from the paper:
"Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks"

Example usage:

    from sgicl import Agent, LiteLLMProvider, Trajectory, Step

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

from sgicl.agent import Agent
from sgicl.models import Message, Step, StepContext, Trajectory
from sgicl.protocols import Environment, LLMProvider
from sgicl.providers import LiteLLMProvider

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
