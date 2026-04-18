"""Helper functions for minibot."""

import time
from datetime import datetime, timezone
from pathlib import Path


def current_time_str(timezone_str: str | None = None) -> str:
    """Get current time as a formatted string."""
    if timezone_str:
        # Simple implementation, for production use pytz
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def sync_workspace_templates(workspace: Path) -> None:
    """Sync templates to workspace."""
    from minibot.config.paths import get_templates_path
    
    templates_path = get_templates_path()
    if not templates_path.exists():
        return
    
    for template_file in templates_path.glob("*.md"):
        dest_file = workspace / template_file.name
        if not dest_file.exists():
            try:
                dest_file.write_text(template_file.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass


def format_duration(seconds: float) -> str:
    """Format duration in seconds to a human-readable string."""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
