"""ReAct-style agent loop implementation."""

import inspect
import os
from collections.abc import Callable
from typing import Any

from icrl.models import Message, Step, StepContext, StepExample, Trajectory
from icrl.protocols import Environment, LLMProvider
from icrl.retriever import TrajectoryRetriever


async def _maybe_await(result: Any) -> Any:
    """Await the result if it's awaitable, otherwise return as-is."""
    if inspect.isawaitable(result):
        return await result
    return result


class ReActLoop:
    """ReAct-style agent loop with planning, reasoning, and acting phases.

    Follows the algorithm from the ICRL paper:
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
        import re

        self._retriever.clear_retrieved()

        observation = env.reset(goal)

        plan_uses_examples = "{examples}" in self._plan_prompt
        reason_uses_examples = "{examples}" in self._reason_prompt
        act_uses_examples = "{examples}" in self._act_prompt

        # Check if using unified XML format (system prompt contains XML markers)
        unified_xml_mode = (
            "<keystrokes" in self._plan_prompt or "<response>" in self._plan_prompt
        )

        examples = self._retriever.retrieve_for_plan(goal) if plan_uses_examples else []

        steps: list[Step] = []
        done = False
        success = False
        plan = ""

        if unified_xml_mode:
            # In XML mode, generate initial response with plan + commands
            # Use the plan prompt for the first turn
            context = StepContext(
                goal=goal,
                plan="",
                observation=observation,
                history=[],
                examples=examples,
            )
            initial_response = await self._generate_plan(goal, examples, observation)

            # Extract plan text for trajectory
            plan_match = re.search(r"<plan>(.*?)</plan>", initial_response, re.DOTALL)
            plan = plan_match.group(1).strip() if plan_match else ""

            # Extract analysis as reasoning
            analysis_match = re.search(
                r"<analysis>(.*?)</analysis>", initial_response, re.DOTALL
            )
            reasoning = analysis_match.group(1).strip() if analysis_match else ""

            # The full XML response is the action (adapter will extract commands)
            action = initial_response

            step = Step(
                observation=observation,
                reasoning=reasoning,
                action=action,
            )
            steps.append(step)

            if self._on_step:
                self._on_step(step, context)

            # Execute initial commands
            step_result = env.step(action)
            observation, done, success = await _maybe_await(step_result)
        else:
            # Traditional mode: generate plan separately
            plan = await self._generate_plan(goal, examples)

        # Continue with step loop
        for _ in range(self._max_steps):
            if done:
                break

            context = StepContext(
                goal=goal,
                plan=plan,
                observation=observation,
                history=steps.copy(),
                examples=[],
            )

            if reason_uses_examples or act_uses_examples:
                examples = self._retriever.retrieve_for_step(goal, plan, observation)
                context.examples = examples

            # In unified XML mode, generate one response with analysis+commands
            if unified_xml_mode:
                # Use act_prompt as unified prompt, reasoning comes from analysis
                action = await self._generate_action(context)

                # Extract analysis/reasoning from XML response
                analysis_match = re.search(
                    r"<analysis>(.*?)</analysis>", action, re.DOTALL
                )
                reasoning = analysis_match.group(1).strip() if analysis_match else ""

                # Update plan if provided in response
                plan_match = re.search(r"<plan>(.*?)</plan>", action, re.DOTALL)
                if plan_match:
                    plan = plan_match.group(1).strip()
            else:
                reasoning = await self._generate_reasoning(context)
                context.reasoning = reasoning
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

        self._retriever.record_episode_result(success)

        return Trajectory(
            goal=goal,
            plan=plan,
            steps=steps,
            success=success,
        )

    async def _generate_plan(
        self, goal: str, examples: list[StepExample], observation: str = ""
    ) -> str:
        """Generate the initial plan.

        Args:
            goal: The goal description.
            examples: Retrieved step examples.
            observation: Initial observation (for XML mode).

        Returns:
            The generated plan.
        """
        context = StepContext(
            goal=goal, plan="", observation=observation, examples=examples
        )
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
        max_goal = int(os.environ.get("ICRL_MAX_GOAL_CHARS", "4000"))
        max_plan = int(os.environ.get("ICRL_MAX_PLAN_CHARS", "2000"))
        max_obs = int(os.environ.get("ICRL_MAX_OBS_CHARS", "5000"))
        max_reason = int(os.environ.get("ICRL_MAX_REASONING_CHARS", "2000"))

        def _cap(text: str, limit: int) -> str:
            if limit <= 0:
                return ""
            if len(text) <= limit:
                return text
            return text[:limit] + "\n...[truncated]..."

        return template.format(
            goal=_cap(context.goal, max_goal),
            plan=_cap(context.plan, max_plan),
            observation=_cap(context.observation, max_obs),
            reasoning=_cap(context.reasoning, max_reason),
            history=context.format_history(),
            examples=context.format_examples(),
        )
