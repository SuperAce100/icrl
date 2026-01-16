"""Textual TUI for ICICL CLI."""

from pathlib import Path
from typing import Any

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.css.query import NoMatches
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
)

from icicl.cli.config import Config, get_default_db_path
from icicl.cli.prompts import SYSTEM_PROMPT
from icicl.cli.providers.tool_provider import ToolLLMProvider
from icicl.cli.tool_loop import ToolLoop
from icicl.cli.tools.base import ToolResult, create_default_registry
from icicl.database import TrajectoryDatabase

CSS = """
Screen {
    layout: grid;
    grid-size: 1;
    grid-rows: auto 1fr auto;
}

#header-container {
    height: auto;
    padding: 1;
    background: $surface;
    border-bottom: solid $primary;
}

#status {
    text-align: center;
    color: $text-muted;
}

#main-container {
    height: 100%;
}

#output-log {
    height: 100%;
    border: solid $primary;
    padding: 1;
    scrollbar-gutter: stable;
}

#input-container {
    height: auto;
    padding: 1;
    background: $surface;
    border-top: solid $primary;
}

#task-input {
    width: 100%;
}

#button-container {
    height: auto;
    margin-top: 1;
    align: center middle;
}

Button {
    margin: 0 1;
}

.tool-call {
    color: $secondary;
}

.thinking {
    color: $text-muted;
}

.success {
    color: $success;
}

.error {
    color: $error;
}

.step-header {
    color: $primary;
    text-style: bold;
}
"""


class ICICLTUI(App):
    """Textual TUI application for ICICL."""

    TITLE = "ICICL - Interactive Coding Assistant"
    CSS = CSS
    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
    ]

    def __init__(
        self,
        config: Config | None = None,
        working_dir: Path | None = None,
    ):
        super().__init__()
        self._config = config or Config.load()
        self._working_dir = working_dir or Path.cwd()
        self._running = False
        self._loop: ToolLoop | None = None
        self._step_count = 0

        # Initialize database
        db_path = self._config.db_path or str(get_default_db_path())
        self._database = TrajectoryDatabase(db_path)

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="header-container"):
            yield Label(
                f"Model: {self._config.model} | Working dir: {self._working_dir}",
                id="status",
            )

        with ScrollableContainer(id="main-container"):
            yield RichLog(id="output-log", highlight=True, markup=True)

        with Container(id="input-container"):
            yield Input(placeholder="Enter your task...", id="task-input")
            with Horizontal(id="button-container"):
                yield Button("Run", id="run-button", variant="primary")
                yield Button("Clear", id="clear-button", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        log = self.query_one("#output-log", RichLog)
        log.write(Text("Welcome to ICICL!", style="bold"))
        log.write(Text(f"Database contains {len(self._database)} trajectories.\n"))
        log.write(Text("Enter a task and press Enter or click Run.\n", style="dim"))

        # Focus the input
        self.query_one("#task-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        if event.input.id == "task-input" and not self._running:
            self.run_task()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "run-button" and not self._running:
            self.run_task()
        elif event.button.id == "clear-button":
            self.action_clear()

    def action_cancel(self) -> None:
        """Cancel the current task."""
        if self._running and self._loop:
            self._loop.cancel()
            self._running = False
            log = self.query_one("#output-log", RichLog)
            log.write(Text("\nCancelled by user.", style="yellow"))
            self._update_ui_state()

    def action_clear(self) -> None:
        """Clear the output log."""
        log = self.query_one("#output-log", RichLog)
        log.clear()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def _update_ui_state(self) -> None:
        """Update UI elements based on running state."""
        try:
            run_button = self.query_one("#run-button", Button)
            task_input = self.query_one("#task-input", Input)

            if self._running:
                run_button.disabled = True
                run_button.label = "Running..."
                task_input.disabled = True
            else:
                run_button.disabled = False
                run_button.label = "Run"
                task_input.disabled = False
                task_input.focus()
        except NoMatches:
            pass

    @work(exclusive=True)
    async def run_task(self) -> None:
        """Run the agent task."""
        task_input = self.query_one("#task-input", Input)
        goal = task_input.value.strip()

        if not goal:
            return

        self._running = True
        self._step_count = 0
        self._update_ui_state()

        log = self.query_one("#output-log", RichLog)
        log.write(Text(f"\n{'=' * 60}", style="dim"))
        log.write(Text(f"Task: {goal}", style="bold"))
        log.write(Text(f"{'=' * 60}\n", style="dim"))

        # Clear input
        task_input.value = ""

        # Create callbacks
        def on_thinking(text: str) -> None:
            lines = text.strip().split("\n")
            preview = lines[0][:100] + "..." if len(lines[0]) > 100 else lines[0]
            self.call_from_thread(log.write, Text(preview, style="dim italic"))

        def on_tool_start(tool: str, params: dict[str, Any]) -> None:
            self._step_count += 1
            if tool == "Bash":
                cmd = params.get("command", "")
                if len(cmd) > 60:
                    cmd = cmd[:60] + "..."
                msg = f"[Step {self._step_count}] Running: {cmd}"
            elif tool in ("Read", "Write", "Edit"):
                msg = f"[Step {self._step_count}] {tool}: {params.get('path', '')}"
            elif tool in ("Glob", "Grep"):
                msg = f"[Step {self._step_count}] {tool}: {params.get('pattern', '')}"
            else:
                msg = f"[Step {self._step_count}] {tool}"
            self.call_from_thread(log.write, Text(msg, style="cyan"))

        def on_tool_end(tool: str, result: ToolResult) -> None:
            style = "green" if result.success else "red"
            output = result.output
            if len(output) > 200:
                output = output[:200] + "..."
            self.call_from_thread(log.write, Text(f"  → {output}", style=style))

        # Create registry with user question callback
        def ask_user(question: str, options: list[str] | None) -> str:
            # For TUI, we'll need to handle this specially
            # For now, return a placeholder
            self.call_from_thread(
                log.write, Text(f"\n[Question] {question}", style="yellow bold")
            )
            if options:
                for i, opt in enumerate(options, 1):
                    opt_text = Text(f"  {i}. {opt}", style="yellow")
                    self.call_from_thread(log.write, opt_text)
            # In a real implementation, we'd pause and get user input
            return "user response placeholder"

        registry = create_default_registry(
            working_dir=self._working_dir,
            ask_user_callback=ask_user,
        )

        # Create LLM and loop
        llm = ToolLLMProvider(
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            registry=registry,
        )

        # Retrieve examples
        examples: list[str] = []
        if len(self._database) > 0:
            similar = self._database.search(goal, k=self._config.k)
            examples = [traj.to_example_string() for traj in similar]
            if examples:
                msg = f"Retrieved {len(examples)} similar examples."
                log.write(Text(msg, style="dim"))

        self._loop = ToolLoop(
            llm=llm,
            registry=registry,
            system_prompt=SYSTEM_PROMPT,
            max_steps=self._config.max_steps,
            on_tool_start=on_tool_start,
            on_tool_end=on_tool_end,
            on_thinking=on_thinking,
        )

        try:
            ex = examples if examples else None
            trajectory = await self._loop.run(goal, examples=ex)

            # Store successful trajectory
            if trajectory.success:
                self._database.add(trajectory)

            # Show result
            log.write(Text(""))
            if trajectory.success:
                log.write(Text("✓ Task completed successfully!", style="bold green"))
                if trajectory.metadata.get("final_response"):
                    log.write(Text("\nSummary:", style="bold"))
                    log.write(Text(trajectory.metadata["final_response"]))
            else:
                log.write(Text("✗ Task did not complete.", style="bold red"))

            log.write(Text(f"\nSteps: {len(trajectory.steps)}", style="dim"))

        except Exception as e:
            log.write(Text(f"\nError: {e}", style="bold red"))

        finally:
            self._running = False
            self._loop = None
            self._update_ui_state()


def run_tui(config: Config | None = None, working_dir: Path | None = None) -> None:
    """Run the TUI application."""
    app = ICICLTUI(config=config, working_dir=working_dir)
    app.run()
