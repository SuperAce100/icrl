"""Agent loop with native tool calling."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from icrl.cli.context_compression import ContextCompressor
from icrl.cli.providers.tool_provider import LLMStats, ToolLLMProvider
from icrl.cli.tools.base import ToolRegistry, ToolResult
from icrl.models import Step, Trajectory


@dataclass
class SessionStats:
    """Accumulated statistics for a session/turn."""

    total_latency_ms: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cached_tokens: int = 0
    total_cache_creation_tokens: int = 0
    llm_calls: int = 0

    def add(self, stats: LLMStats) -> None:
        """Add stats from a single LLM call."""
        self.total_latency_ms += stats.latency_ms
        self.total_prompt_tokens += stats.prompt_tokens
        self.total_completion_tokens += stats.completion_tokens
        self.total_tokens += stats.total_tokens
        self.total_cached_tokens += stats.cached_tokens
        self.total_cache_creation_tokens += stats.cache_creation_tokens
        self.llm_calls += 1

    @property
    def avg_latency_ms(self) -> float:
        """Average latency per LLM call."""
        if self.llm_calls == 0:
            return 0.0
        return self.total_latency_ms / self.llm_calls

    @property
    def tokens_per_second(self) -> float:
        """Overall throughput in tokens per second."""
        if self.total_latency_ms <= 0:
            return 0.0
        return (self.total_completion_tokens / self.total_latency_ms) * 1000

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as percentage of prompt tokens."""
        if self.total_prompt_tokens <= 0:
            return 0.0
        return (self.total_cached_tokens / self.total_prompt_tokens) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for metadata storage."""
        result = {
            "total_latency_ms": round(self.total_latency_ms, 1),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "tokens_per_second": round(self.tokens_per_second, 1),
        }
        # Only include cache stats if there was any caching activity
        if self.total_cached_tokens > 0 or self.total_cache_creation_tokens > 0:
            result["cached_tokens"] = self.total_cached_tokens
            result["cache_creation_tokens"] = self.total_cache_creation_tokens
            result["cache_hit_rate"] = round(self.cache_hit_rate, 1)
        return result


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
        context_compression_threshold: int = 150_000,
        on_context_compressed: Callable[[int, int], None] | None = None,
        enable_prompt_caching: bool = True,
    ):
        self._llm = llm
        self._registry = registry
        self._system_prompt = system_prompt
        self._max_steps = max_steps
        self._on_tool_start = on_tool_start
        self._on_tool_end = on_tool_end
        self._on_thinking = on_thinking
        self._on_context_compressed = on_context_compressed
        self._enable_prompt_caching = enable_prompt_caching
        self._cancelled = False

        # Conversation history for multi-turn chat
        self._messages: list[dict[str, Any]] = []

        # Context compression
        # Get Vertex AI params if available (for compression LLM calls)
        project_id = getattr(llm, "_project_id", None)
        location = getattr(llm, "_location", None)
        model = getattr(llm, "_model", "gpt-4")
        
        self._context_compressor = ContextCompressor(
            threshold_tokens=context_compression_threshold,
            model=model,
            project_id=project_id,
            location=location,
        )

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
            # Continue existing conversation
            messages = self._messages
            
            # For prompt caching: add a cache breakpoint at the end of the
            # existing conversation history. This allows the entire prefix
            # (system + examples + previous turns) to be cached.
            # Anthropic supports up to 4 breakpoints.
            if self._enable_prompt_caching and len(messages) > 0:
                # Find the last assistant message and add cache_control to it
                # This marks the end of the "stable" conversation prefix
                for i in range(len(messages) - 1, -1, -1):
                    msg = messages[i]
                    if msg.get("role") == "assistant" and msg.get("content"):
                        content = msg["content"]
                        # If content is a string, convert to block format with cache_control
                        if isinstance(content, str):
                            messages[i]["content"] = [
                                {
                                    "type": "text",
                                    "text": content,
                                    "cache_control": {"type": "ephemeral"},
                                }
                            ]
                        # If content is already a list, add cache_control to last text block
                        elif isinstance(content, list):
                            for j in range(len(content) - 1, -1, -1):
                                if isinstance(content[j], dict) and content[j].get("type") == "text":
                                    content[j]["cache_control"] = {"type": "ephemeral"}
                                    break
                        break  # Only mark the last assistant message
            
            messages.append({"role": "user", "content": goal})
        else:
            # Start fresh conversation
            # Use cache_control for static content (system prompt, examples)
            # to enable prompt caching on supported providers (Anthropic, etc.)
            if self._enable_prompt_caching:
                # Format with cache_control blocks for Anthropic-style caching
                # The system prompt and examples are static across turns,
                # so they benefit from caching
                system_content: list[dict[str, Any]] = [
                    {
                        "type": "text",
                        "text": self._system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
                messages = [{"role": "system", "content": system_content}]

                # Add examples if provided (also cached)
                if examples:
                    examples_text = "\n\n---\n\n".join(examples)
                    ex_content = (
                        f"Here are some relevant examples from similar tasks:\n\n"
                        f"{examples_text}"
                    )
                    examples_content: list[dict[str, Any]] = [
                        {
                            "type": "text",
                            "text": ex_content,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ]
                    messages.append({"role": "system", "content": examples_content})
            else:
                # Standard format without caching
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
        session_stats = SessionStats()

        for step_num in range(self._max_steps):
            if self._cancelled:
                break

            # Check if context compression is needed before LLM call
            old_token_count = self._context_compressor.last_token_count
            messages, was_compressed = await self._context_compressor.maybe_compress(
                messages
            )
            if was_compressed and self._on_context_compressed:
                new_token_count = self._context_compressor.last_token_count
                self._on_context_compressed(old_token_count, new_token_count)

            # Get LLM response
            response = await self._llm.complete_with_tools(messages)

            # Accumulate stats
            session_stats.add(response.stats)

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
            metadata={
                "final_response": final_response,
                "stats": session_stats.to_dict(),
            },
        )
