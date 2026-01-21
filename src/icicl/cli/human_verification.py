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


def parse_yes_no(answer: str) -> bool:
    """Parse a yes/no answer from the user."""
    answer = answer.strip().lower()
    if answer in ("1", "yes", "y", "true"):
        return True
    return False
