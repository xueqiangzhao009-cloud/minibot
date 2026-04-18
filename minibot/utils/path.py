"""Path utilities for minibot."""

from pathlib import Path
import os


def get_config_path() -> Path:
    """Get the default config path."""
    return Path.home() / ".minibot" / "config.json"


def get_workspace_path(config_workspace: str | Path | None = None) -> Path:
    """Get the workspace path."""
    if config_workspace:
        return Path(config_workspace).expanduser().resolve()
    return Path.home() / ".minibot" / "workspace"


def get_templates_path() -> Path:
    """Get the templates path."""
    return Path(__file__).parent.parent / "templates"


def get_cli_history_path() -> Path:
    """Get the CLI history path."""
    return Path.home() / ".minibot" / "cli_history.txt"


def get_cron_dir() -> Path:
    """Get the cron directory."""
    return Path.home() / ".minibot" / "cron"


def ensure_dir(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
