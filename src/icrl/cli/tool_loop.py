"""Agent loop with native tool calling."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from icrl.cli.providers.tool_provider import ToolLLMProvider
from icrl.cli.tools.base import ToolRegistry, ToolResult
from icrl.models import Step, Trajectory


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

        # Conversation history for multi-turn chat
        self._messages: list[dict[str, Any]] = []

        # Ensure LLM has access to tools
        self._llm.set_registry(registry)

    def cancel(self) -> None:
        """Cancel the loop."""
        self._cancelled = True

    def clear_history(self) -> None:
        """Clear conversation history for a fresh start."""
        self._messages = []

    def get_messages(self) -> list[dict[str, Any]]:
        """Get the current conversation history."""
        return list(self._messages)

    async def run(
        self,
        goal: str,
        examples: list[str] | None = None,
        continue_conversation: bool = False,
    ) -> Trajectory:
        """Run the tool-calling loop.

        Args:
            goal: The user's goal/task
            examples: Optional retrieved examples to include in context
            continue_conversation: If True, continue from existing conversation history

        Returns:
            Trajectory with steps
        """
        self._cancelled = False

        if continue_conversation and self._messages:
            # Continue existing conversation - just add the new user message
            messages = self._messages
            messages.append({"role": "user", "content": goal})
        else:
            # Start fresh conversation
            messages = [
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
                    # Validate arguments before execution
                    is_valid, validation_error = tool.validate_arguments(
                        tool_call.arguments
                    )
                    if not is_valid:
                        result = ToolResult(
                            output=f"Error calling {tool_call.name}: {validation_error}",
                            success=False,
                        )
                    else:
                        if self._on_tool_start:
                            self._on_tool_start(tool_call.name, tool_call.arguments)

                        try:
                            result = await tool.execute(**tool_call.arguments)
                        except TypeError as e:
                            # Handle missing/invalid arguments that slipped past validation
                            result = ToolResult(
                                output=f"Error calling {tool_call.name}: {e}",
                                success=False,
                            )
                        except Exception as e:
                            # Handle any other unexpected errors gracefully
                            result = ToolResult(
                                output=f"Error executing {tool_call.name}: {type(e).__name__}: {e}",
                                success=False,
                            )

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

        # If the model finished with a text response (no tool call), add it to messages
        if success and final_response:
            messages.append({"role": "assistant", "content": final_response})

        # Save messages for multi-turn continuation
        self._messages = messages

        return Trajectory(
            goal=goal,
            plan="",  # Tool calling doesn't have separate plan phase
            steps=steps,
            success=success,
            metadata={"final_response": final_response},
        )
