"""Configuration management for ICICL CLI."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    if os.name == "nt":  # Windows
        config_dir = Path(os.environ.get("APPDATA", "~")) / "icicl"
    else:  # macOS/Linux
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")) / "icicl"
    return config_dir.expanduser()


def get_default_db_path() -> Path:
    """Get the default database path."""
    data_dir = get_config_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "trajectories"


@dataclass
class Config:
    """Configuration for ICICL CLI."""

    # LLM settings
    model: str = "gpt-5.2"
    temperature: float = 0.3
    max_tokens: int = 4096

    # Agent settings
    max_steps: int = 50
    k: int = 3  # Number of examples to retrieve

    # Database settings
    db_path: str | None = None

    # API keys (loaded from environment)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

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
            "db_path": self.db_path,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_steps": self.max_steps,
            "k": self.k,
            "db_path": self.db_path or str(get_default_db_path()),
        }
