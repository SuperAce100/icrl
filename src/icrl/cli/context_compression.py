"""Automatic context compression for long conversations.

When the context window exceeds a threshold, this module compresses the
conversation history using an LLM call to maintain key information while
reducing token count.
"""

import json
from typing import Any

import litellm


# Compression prompt that instructs the LLM to compress conversation history
COMPRESSION_SYSTEM_PROMPT = """You are a context compression assistant. Your task is to compress a conversation history into a concise summary that preserves ALL information needed for an AI assistant to continue the task effectively.

CRITICAL REQUIREMENTS:
1. Preserve ALL file paths, code snippets, and technical details mentioned
2. Preserve the current state of any ongoing work (what's been done, what's pending)
3. Preserve any user preferences, constraints, or requirements stated
4. Preserve the exact content of any recent tool calls and their results
5. Preserve any errors encountered and how they were resolved
6. Keep the most recent 2-3 exchanges in full detail (these are most relevant)

OUTPUT FORMAT:
Return a JSON object with this structure:
{
    "summary": "A detailed summary of the conversation so far, including all key technical details",
    "key_files": ["list of file paths that have been read, written, or edited"],
    "key_decisions": ["list of important decisions or findings"],
    "current_state": "description of where we are in the task",
    "pending_actions": ["any actions that were discussed but not yet completed"]
}

Be thorough - it's better to include too much detail than to lose critical context."""


async def estimate_token_count(messages: list[dict[str, Any]], model: str = "gpt-4") -> int:
    """Estimate the token count for a list of messages.
    
    Uses litellm's token counting which handles different model tokenizers.
    Falls back to a rough character-based estimate if that fails.
    
    Args:
        messages: List of messages in LiteLLM format
        model: Model name for tokenizer selection
        
    Returns:
        Estimated token count
    """
    try:
        # Try to use litellm's token counter
        return litellm.token_counter(model=model, messages=messages)
    except Exception:
        # Fallback: rough estimate based on characters (avg ~4 chars per token)
        total_chars = sum(
            len(str(msg.get("content", ""))) + len(str(msg.get("tool_calls", "")))
            for msg in messages
        )
        return total_chars // 4


async def compress_context(
    messages: list[dict[str, Any]],
    model: str,
    project_id: str | None = None,
    location: str | None = None,
    preserve_recent: int = 4,
) -> list[dict[str, Any]]:
    """Compress conversation history while preserving key information.
    
    Args:
        messages: Full conversation history
        model: Model to use for compression
        project_id: Vertex AI project ID (if using Vertex)
        location: Vertex AI location (if using Vertex)
        preserve_recent: Number of recent messages to keep uncompressed
        
    Returns:
        Compressed message list with summary + recent messages
    """
    if len(messages) <= preserve_recent + 2:  # system + few messages
        return messages  # Nothing to compress
    
    # Separate system prompt, messages to compress, and recent messages
    system_messages = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    
    if len(non_system) <= preserve_recent:
        return messages  # Not enough to compress
    
    # Messages to compress (older ones) and preserve (recent ones)
    to_compress = non_system[:-preserve_recent]
    to_preserve = non_system[-preserve_recent:]
    
    # Format messages for compression
    formatted_history = _format_messages_for_compression(to_compress)
    
    # Build compression request
    compression_messages = [
        {"role": "system", "content": COMPRESSION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Please compress the following conversation history:\n\n{formatted_history}"},
    ]
    
    # Call LLM for compression
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": compression_messages,
        "temperature": 0.1,  # Low temperature for consistent compression
        "max_tokens": 4096,
    }
    
    # Add Vertex AI params if needed
    if project_id:
        kwargs["vertex_ai_project"] = project_id
    if location:
        kwargs["vertex_ai_location"] = location
    
    try:
        response = await litellm.acompletion(**kwargs)
        compressed_content = response.choices[0].message.content or ""
        
        # Try to parse as JSON for structured summary
        try:
            summary_data = json.loads(compressed_content)
            summary_text = _format_structured_summary(summary_data)
        except json.JSONDecodeError:
            # Use raw text if not valid JSON
            summary_text = compressed_content
        
        # Build compressed message list
        compressed_messages = list(system_messages)  # Keep system prompts
        
        # Add compression summary as a system message
        compressed_messages.append({
            "role": "system",
            "content": f"[COMPRESSED CONTEXT - Previous conversation summary]\n\n{summary_text}\n\n[END COMPRESSED CONTEXT - Recent messages follow]"
        })
        
        # Add preserved recent messages
        compressed_messages.extend(to_preserve)
        
        return compressed_messages
        
    except Exception as e:
        # If compression fails, return original messages
        # (better to be slow than to lose context)
        import sys
        print(f"[Warning] Context compression failed: {e}", file=sys.stderr)
        return messages


def _format_messages_for_compression(messages: list[dict[str, Any]]) -> str:
    """Format messages into a readable string for compression.
    
    Args:
        messages: Messages to format
        
    Returns:
        Formatted string representation
    """
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        
        # Handle tool calls
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            tool_info = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    name = func.get("name", "unknown")
                    args = func.get("arguments", "{}")
                    tool_info.append(f"  - {name}({args})")
            if tool_info:
                content = f"{content}\n[Tool calls:\n" + "\n".join(tool_info) + "]"
        
        # Handle tool results
        if role == "TOOL":
            tool_call_id = msg.get("tool_call_id", "unknown")
            parts.append(f"[TOOL RESULT ({tool_call_id})]:\n{content}")
        else:
            parts.append(f"[{role}]:\n{content}")
    
    return "\n\n---\n\n".join(parts)


def _format_structured_summary(data: dict[str, Any]) -> str:
    """Format structured summary data into readable text.
    
    Args:
        data: Parsed JSON summary data
        
    Returns:
        Formatted summary string
    """
    parts = []
    
    if summary := data.get("summary"):
        parts.append(f"**Summary:**\n{summary}")
    
    if key_files := data.get("key_files"):
        parts.append(f"**Key Files:**\n" + "\n".join(f"  - {f}" for f in key_files))
    
    if key_decisions := data.get("key_decisions"):
        parts.append(f"**Key Decisions:**\n" + "\n".join(f"  - {d}" for d in key_decisions))
    
    if current_state := data.get("current_state"):
        parts.append(f"**Current State:**\n{current_state}")
    
    if pending := data.get("pending_actions"):
        parts.append(f"**Pending Actions:**\n" + "\n".join(f"  - {a}" for a in pending))
    
    return "\n\n".join(parts)


class ContextCompressor:
    """Manages automatic context compression for a conversation.
    
    Tracks token usage and automatically compresses when threshold is exceeded.
    """
    
    def __init__(
        self,
        threshold_tokens: int = 150_000,
        model: str = "gpt-4",
        project_id: str | None = None,
        location: str | None = None,
    ):
        """Initialize the context compressor.
        
        Args:
            threshold_tokens: Token count threshold to trigger compression
            model: Model to use for compression
            project_id: Vertex AI project ID (if using Vertex)
            location: Vertex AI location (if using Vertex)
        """
        self.threshold_tokens = threshold_tokens
        self.model = model
        self.project_id = project_id
        self.location = location
        self._compression_count = 0
        self._last_token_count = 0
    
    @property
    def compression_count(self) -> int:
        """Number of times compression has been triggered."""
        return self._compression_count
    
    @property
    def last_token_count(self) -> int:
        """Token count from last check."""
        return self._last_token_count
    
    async def maybe_compress(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], bool]:
        """Check if compression is needed and compress if so.
        
        Args:
            messages: Current conversation messages
            
        Returns:
            Tuple of (possibly compressed messages, whether compression occurred)
        """
        # Estimate current token count
        self._last_token_count = await estimate_token_count(messages, self.model)
        
        if self._last_token_count < self.threshold_tokens:
            return messages, False
        
        # Compression needed
        compressed = await compress_context(
            messages=messages,
            model=self.model,
            project_id=self.project_id,
            location=self.location,
        )
        
        self._compression_count += 1
        
        # Verify compression actually reduced size
        new_count = await estimate_token_count(compressed, self.model)
        if new_count >= self._last_token_count:
            # Compression didn't help, return original
            return messages, False
        
        self._last_token_count = new_count
        return compressed, True
