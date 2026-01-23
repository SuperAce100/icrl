"""Configuration management for ICRL CLI."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    if os.name == "nt":  # Windows
        config_dir = Path(os.environ.get("APPDATA", "~")) / "icrl"
    else:  # macOS/Linux
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")) / "icrl"
    return config_dir.expanduser()


def get_default_db_path() -> Path:
    """Get the default database path."""
    data_dir = get_config_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "trajectories"


@dataclass
class Config:
    """Configuration for ICRL CLI."""

    # LLM settings
    # Default to Anthropic Claude Opus 4.5 on Vertex AI
    model: str = "claude-opus-4-5"
    temperature: float = 0.3
    max_tokens: int = 4096

    # Agent settings
    max_steps: int = 50
    k: int = 3  # Number of examples to retrieve

    # Display settings
    show_stats: bool = True  # Show latency and throughput statistics

    # Approval settings
    auto_approve: bool = True  # Auto-approve file writes and edits (no confirmation prompts)

    # Database settings
    db_path: str | None = None

    # API keys (loaded from environment)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Vertex AI settings (for Anthropic Claude on Google Cloud)
    vertex_credentials_path: str | None = None
    vertex_project_id: str | None = None
    vertex_location: str | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        """Load configuration from file.

        Args:
            path: Path to config file. If None, uses default location.

        Returns:
            Loaded configuration.
        """
        if path is None:
            path = get_config_dir() / "config.json"

        config = cls()

        if path.exists():
            with open(path) as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

        # Load API keys from environment
        config.openai_api_key = os.environ.get("OPENAI_API_KEY")
        config.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Load Vertex AI settings from environment (fallbacks)
        if config.vertex_credentials_path is None:
            config.vertex_credentials_path = os.environ.get(
                "GOOGLE_APPLICATION_CREDENTIALS"
            )
        if config.vertex_project_id is None:
            config.vertex_project_id = os.environ.get("VERTEXAI_PROJECT")
        if config.vertex_location is None:
            config.vertex_location = os.environ.get("VERTEXAI_LOCATION")

        return config

    def save(self, path: Path | None = None) -> None:
        """Save configuration to file.

        Args:
            path: Path to config file. If None, uses default location.
        """
        if path is None:
            path = get_config_dir() / "config.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        # Don't save API keys to file
        data = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_steps": self.max_steps,
            "k": self.k,
            "show_stats": self.show_stats,
            "auto_approve": self.auto_approve,
            "db_path": self.db_path,
            "vertex_credentials_path": self.vertex_credentials_path,
            "vertex_project_id": self.vertex_project_id,
            "vertex_location": self.vertex_location,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_steps": self.max_steps,
            "k": self.k,
            "show_stats": self.show_stats,
            "auto_approve": self.auto_approve,
            "db_path": self.db_path or str(get_default_db_path()),
        }
        # Only include Vertex settings if configured
        if self.vertex_credentials_path:
            result["vertex_credentials_path"] = self.vertex_credentials_path
        if self.vertex_project_id:
            result["vertex_project_id"] = self.vertex_project_id
        if self.vertex_location:
            result["vertex_location"] = self.vertex_location
        return result
