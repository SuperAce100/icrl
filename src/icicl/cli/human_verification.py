"""Human verification utilities for file operations."""


def build_write_prompt(path: str, content: str) -> str:
    """Build a prompt asking the user to verify a write operation."""
    preview = content[:500] + "..." if len(content) > 500 else content
    return f"Allow writing to '{path}'?\n\nContent preview:\n{preview}"


def build_edit_prompt(path: str, old_text: str, new_text: str) -> str:
    """Build a prompt asking the user to verify an edit operation."""
    old_preview = old_text[:200] + "..." if len(old_text) > 200 else old_text
    new_preview = new_text[:200] + "..." if len(new_text) > 200 else new_text
    return (
        f"Allow editing '{path}'?\n\n"
        f"Replace:\n{old_preview}\n\n"
        f"With:\n{new_preview}"
    )


# NOTE: Human verification uses Rich's Confirm.ask in the CLI layer.
# Tools only receive a callback and treat its return value as a boolean.
