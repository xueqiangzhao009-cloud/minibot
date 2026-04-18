"""CLI models for minibot."""

from typing import Optional
from pydantic import BaseModel


class OnboardResult(BaseModel):
    """Result of the onboarding process."""
    config: dict
    should_save: bool = True


class CliConfig(BaseModel):
    """CLI configuration."""
    history_file: Optional[str] = None
    default_session: str = "cli:direct"
    render_markdown: bool = True
    show_progress: bool = True
    show_tool_hints: bool = True
