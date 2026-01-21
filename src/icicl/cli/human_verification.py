"""Human verification utilities for file operations."""


def build_write_prompt(path: str, content: str) -> str:
    """Build a prompt asking the user to verify a write operation."""
    preview = content[:500] + "..." if len(content) > 500 else content
    return f"Allow writing to '{path}'?\n\nContent preview:\n{preview}"


def build_edit_prompt(path: str, old_text: str, new_text: str) -> str:
    """Build a prompt asking the user to verify an edit operation.

    Present a lightweight, line-based diff (with `-` and `+` prefixes) instead of
    two heavily-indented blocks.
    """

    def _truncate_lines(text: str, max_lines: int = 80, max_cols: int = 240) -> list[str]:
        lines = (text or "").splitlines()
        # Avoid huge prompts.
        if len(lines) > max_lines:
            head = lines[: max_lines // 2]
            tail = lines[-max_lines // 2 :]
            lines = head + ["... (truncated) ..."] + tail
        # Cap line length to keep prompts readable in terminal.
        out: list[str] = []
        for line in lines:
            if len(line) > max_cols:
                out.append(line[: max_cols - 3] + "...")
            else:
                out.append(line)
        return out

    old_lines = _truncate_lines(old_text)
    new_lines = _truncate_lines(new_text)

    # If content is single-line or empty, keep it simple.
    if len(old_lines) <= 1 and len(new_lines) <= 1:
        old_preview = (old_text[:200] + "...") if old_text and len(old_text) > 200 else (old_text or "")
        new_preview = (new_text[:200] + "...") if new_text and len(new_text) > 200 else (new_text or "")
        return (
            f"Allow editing '{path}'?\n\n"
            f"- {old_preview}\n"
            f"+ {new_preview}\n\n"
            "Approve this edit?"
        )

    # Naive, but readable, line-by-line diff:
    # - show removed lines with `- `
    # - show added lines with `+ `
    # This does not attempt a full LCS diff; it's a UX improvement for approvals.
    width = max(len(old_lines), len(new_lines))
    diff_lines: list[str] = []
    for i in range(width):
        o = old_lines[i] if i < len(old_lines) else None
        n = new_lines[i] if i < len(new_lines) else None
        if o == n:
            continue
        if o is not None:
            diff_lines.append(f"- {o}")
        if n is not None:
            diff_lines.append(f"+ {n}")

    if not diff_lines:
        diff_lines = ["(no textual changes detected)"]

    return (
        f"Allow editing '{path}'?\n\n"
        "Proposed changes:\n"
        + "\n".join(diff_lines)
        + "\n\nApprove this edit?"
    )


# NOTE: Human verification uses Rich's Confirm.ask in the CLI layer.
# Tools only receive a callback and treat its return value as a boolean.
