"""Agent loop with native tool calling."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from icicl.cli.providers.tool_provider import ToolLLMProvider
from icicl.cli.tools.base import ToolRegistry, ToolResult
from icicl.models import Step, Trajectory


@dataclass
class ToolStep:
    """A single step in the tool-calling loop."""

    tool_name: str
    tool_args: dict[str, Any]
    tool_result: ToolResult
    reasoning: str = ""  # LLM's thinking before the tool call


class ToolLoop:
    """Agent loop using native tool calling."""

    def __init__(
        self,
        llm: ToolLLMProvider,
        registry: ToolRegistry,
        system_prompt: str,
        max_steps: int = 50,
        on_tool_start: Callable[[str, dict[str, Any]], None] | None = None,
        on_tool_end: Callable[[str, ToolResult], None] | None = None,
        on_thinking: Callable[[str], None] | None = None,
    ):
        self._llm = llm
        self._registry = registry
        self._system_prompt = system_prompt
        self._max_steps = max_steps
        self._on_tool_start = on_tool_start
        self._on_tool_end = on_tool_end
        self._on_thinking = on_thinking
        self._cancelled = False

        # Ensure LLM has access to tools
        self._llm.set_registry(registry)

    def cancel(self) -> None:
        """Cancel the loop."""
        self._cancelled = True

    async def run(self, goal: str, examples: list[str] | None = None) -> Trajectory:
        """Run the tool-calling loop.

        Args:
            goal: The user's goal/task
            examples: Optional retrieved examples to include in context

        Returns:
            Trajectory with steps
        """
        self._cancelled = False

        # Build initial messages
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
        ]

        # Add examples if provided
        if examples:
            examples_text = "\n\n---\n\n".join(examples)
            ex_content = (
                f"Here are some relevant examples from similar tasks:\n\n"
                f"{examples_text}"
            )
            messages.append({"role": "system", "content": ex_content})

        # Add user goal
        messages.append({"role": "user", "content": goal})

        steps: list[Step] = []
        success = False
        final_response = ""

        for step_num in range(self._max_steps):
            if self._cancelled:
                break

            # Get LLM response
            response = await self._llm.complete_with_tools(messages)

            # Handle text content (thinking)
            if response.content:
                if self._on_thinking:
                    self._on_thinking(response.content)
                final_response = response.content

            # Check if done
            if response.finish_reason == "stop" or not response.tool_calls:
                # Model finished without tool call
                success = True
                break

            # Execute tool calls
            for tool_call in response.tool_calls:
                if self._cancelled:
                    break

                tool = self._registry.get(tool_call.name)

                if not tool:
                    result = ToolResult(
                        output=f"Unknown tool: {tool_call.name}", success=False
                    )
                else:
                    if self._on_tool_start:
                        self._on_tool_start(tool_call.name, tool_call.arguments)

                    result = await tool.execute(**tool_call.arguments)

                    if self._on_tool_end:
                        self._on_tool_end(tool_call.name, result)

                # Record step
                steps.append(
                    Step(
                        observation=result.output,
                        reasoning=response.content or "",
                        action=f"{tool_call.name}({json.dumps(tool_call.arguments)})",
                    )
                )

                # Add assistant message with tool call
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.content,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.name,
                                    "arguments": json.dumps(tool_call.arguments),
                                },
                            }
                        ],
                    }
                )

                # Add tool result
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.output,
                    }
                )

        return Trajectory(
            goal=goal,
            plan="",  # Tool calling doesn't have separate plan phase
            steps=steps,
            success=success,
            metadata={"final_response": final_response},
        )
