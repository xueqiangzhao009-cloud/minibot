"""Tool hints for minibot."""

from typing import List, Dict, Any


class ToolHintGenerator:
    """Generate tool hints for minibot."""

    @staticmethod
    def get_filesystem_hints() -> List[Dict[str, Any]]:
        """Get filesystem tool hints."""
        return [
            {
                "tool": "read_file",
                "description": "Read the content of a file",
                "example": "read_file(path=\"example.txt\")"
            },
            {
                "tool": "write_file",
                "description": "Write content to a file",
                "example": "write_file(path=\"example.txt\", content=\"Hello world\")"
            },
            {
                "tool": "edit_file",
                "description": "Edit an existing file",
                "example": "edit_file(path=\"example.txt\", content=\"Updated content\")"
            },
            {
                "tool": "list_directory",
                "description": "List files in a directory",
                "example": "list_directory(path=\".\")"
            }
        ]

    @staticmethod
    def get_shell_hints() -> List[Dict[str, Any]]:
        """Get shell tool hints."""
        return [
            {
                "tool": "execute_command",
                "description": "Execute a shell command",
                "example": "execute_command(command=\"ls -la\")"
            }
        ]

    @staticmethod
    def get_web_hints() -> List[Dict[str, Any]]:
        """Get web tool hints."""
        return [
            {
                "tool": "search_web",
                "description": "Search the web for information",
                "example": "search_web(query=\"Python asyncio tutorial\")"
            },
            {
                "tool": "fetch_web",
                "description": "Fetch content from a URL",
                "example": "fetch_web(url=\"https://example.com\")"
            }
        ]

    @staticmethod
    def get_all_hints() -> List[Dict[str, Any]]:
        """Get all tool hints."""
        hints = []
        hints.extend(ToolHintGenerator.get_filesystem_hints())
        hints.extend(ToolHintGenerator.get_shell_hints())
        hints.extend(ToolHintGenerator.get_web_hints())
        return hints
