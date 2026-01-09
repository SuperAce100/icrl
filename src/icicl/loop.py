"""ReAct-style agent loop implementation."""

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from icicl.models import Message, Step, StepContext, StepExample, Trajectory
from icicl.protocols import Environment, LLMProvider
from icicl.retriever import TrajectoryRetriever


async def _maybe_await(result: Any) -> Any:
    """Await the result if it's awaitable, otherwise return as-is."""
    if inspect.isawaitable(result):
        return await result
    return result


class ReActLoop:
    """ReAct-style agent loop with planning, reasoning, and acting phases.

    Follows the algorithm from the SGICL paper:
    1. Retrieve examples and generate initial plan
    2. For each step: observe, retrieve examples, reason, retrieve again, act
    3. Continue until done or max_steps reached
    """

    def __init__(
        self,
        llm: LLMProvider,
        retriever: TrajectoryRetriever,
        plan_prompt: str,
        reason_prompt: str,
        act_prompt: str,
        max_steps: int = 30,
        on_step: Callable[[Step, StepContext], None] | None = None,
    ) -> None:
        """Initialize the ReAct loop.

        Args:
            llm: The LLM provider for generating completions.
            retriever: The trajectory retriever for finding examples.
            plan_prompt: Template for planning prompts.
            reason_prompt: Template for reasoning prompts.
            act_prompt: Template for action prompts.
            max_steps: Maximum number of steps per episode.
            on_step: Optional callback called after each step.
        """
        self._llm = llm
        self._retriever = retriever
        self._plan_prompt = plan_prompt
        self._reason_prompt = reason_prompt
        self._act_prompt = act_prompt
        self._max_steps = max_steps
        self._on_step = on_step

    async def run(self, env: Environment, goal: str) -> Trajectory:
        """Run a complete episode.

        Args:
            env: The environment to interact with.
            goal: The goal description.

        Returns:
            The resulting trajectory.
        """
        self._retriever.clear_retrieved()

        observation = env.reset(goal)

        examples = self._retriever.retrieve_for_plan(goal)
        plan = await self._generate_plan(goal, examples)

        steps: list[Step] = []
        done = False
        success = False

        for _ in range(self._max_steps):
            context = StepContext(
                goal=goal,
                plan=plan,
                observation=observation,
                history=steps.copy(),
                examples=examples,
            )

            examples = self._retriever.retrieve_for_step(goal, plan, observation)
            context.examples = examples

            reasoning = await self._generate_reasoning(context)
            context.reasoning = reasoning

            examples = self._retriever.retrieve_for_step(goal, plan, reasoning)
            context.examples = examples

            action = await self._generate_action(context)

            step = Step(
                observation=observation,
                reasoning=reasoning,
                action=action,
            )
            steps.append(step)

            if self._on_step:
                self._on_step(step, context)

            step_result = env.step(action)
            observation, done, success = await _maybe_await(step_result)

            if done:
                break

        self._retriever.record_episode_result(success)

        return Trajectory(
            goal=goal,
            plan=plan,
            steps=steps,
            success=success,
        )

    async def _generate_plan(self, goal: str, examples: list[StepExample]) -> str:
        """Generate the initial plan.

        Args:
            goal: The goal description.
            examples: Retrieved step examples.

        Returns:
            The generated plan.
        """
        context = StepContext(goal=goal, plan="", observation="", examples=examples)
        prompt = self._format_prompt(self._plan_prompt, context)
        messages = [Message(role="user", content=prompt)]
        return await self._llm.complete(messages)

    async def _generate_reasoning(self, context: StepContext) -> str:
        """Generate reasoning for the current step.

        Args:
            context: The current step context.

        Returns:
            The generated reasoning.
        """
        prompt = self._format_prompt(self._reason_prompt, context)
        messages = [Message(role="user", content=prompt)]
        return await self._llm.complete(messages)

    async def _generate_action(self, context: StepContext) -> str:
        """Generate an action for the current step.

        Args:
            context: The current step context.

        Returns:
            The generated action.
        """
        prompt = self._format_prompt(self._act_prompt, context)
        messages = [Message(role="user", content=prompt)]
        return await self._llm.complete(messages)

    def _format_prompt(self, template: str, context: StepContext) -> str:
        """Format a prompt template with context.

        Args:
            template: The prompt template string.
            context: The context to fill in.

        Returns:
            The formatted prompt.
        """
        return template.format(
            goal=context.goal,
            plan=context.plan,
            observation=context.observation,
            reasoning=context.reasoning,
            history=context.format_history(),
            examples=context.format_examples(),
        )
