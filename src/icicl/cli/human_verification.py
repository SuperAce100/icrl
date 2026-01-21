"""Human verification (approval) helpers for ICICL CLI.

This module is used to gate potentially dangerous side effects (e.g., writing files)
behind a human approval prompt.

Design goals:
- Minimal intrusion: integrate via callbacks already available in the CLI runner.
- Safe defaults: if we cannot get an answer, default to deny.
- Friendly UX: show a compact summary of what will happen.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class VerificationDecision:
    approved: bool
    message: str = ""


def _format_preview(text: str, max_chars: int = 800) -> str:
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars // 2] + "\n... (truncated) ...\n" + text[-max_chars // 2 :]


def build_write_prompt(path: str, content: str) -> str:
    preview = _format_preview(content)
    return (
        "Human verification required before writing a file.\n\n"
        f"Tool: Write\nPath: {path}\nBytes: {len(content.encode('utf-8', errors='ignore'))}\n\n"
        "Content preview:\n"
        "---\n"
        f"{preview}\n"
        "---\n\n"
        "Approve this write?"
    )


def build_edit_prompt(path: str, old_text: str, new_text: str) -> str:
    old_preview = _format_preview(old_text)
    new_preview = _format_preview(new_text)
    return (
        "Human verification required before editing a file.\n\n"
        f"Tool: Edit\nPath: {path}\n\n"
        "Old text (exact match required):\n"
        "---\n"
        f"{old_preview}\n"
        "---\n\n"
        "New text:\n"
        "---\n"
        f"{new_preview}\n"
        "---\n\n"
        "Approve this edit?"
    )


def parse_yes_no(answer: str) -> bool:
    """Interpret a user answer as yes/no.

    Accepts common variants. Defaults to False for unrecognized input.
    """

    if answer is None:
        return False
    a = answer.strip().lower()
    return a in {"y", "yes", "approve", "approved", "ok", "okay"}


def safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(obj)
