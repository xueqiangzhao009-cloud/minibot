"""Tool registry for managing tools."""

from typing import Dict, Optional, Type, Any

class ToolRegistry:
    """Registry for tools."""

    def __init__(self):
        self._tools: Dict[str, Any] = {}

    def register(self, tool: Any) -> None:
        """Register a tool."""
        name = getattr(tool, "name", None)
        if not name:
            raise ValueError("Tool must have a 'name' attribute")
        self._tools[name] = tool

    def get(self, name: str) -> Optional[Any]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list(self) -> Dict[str, Any]:
        """List all registered tools."""
        return self._tools.copy()
