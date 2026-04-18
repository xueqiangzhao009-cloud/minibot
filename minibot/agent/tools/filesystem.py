"""Filesystem tools."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class ReadFileTool:
    """Tool for reading files."""

    name = "read"
    description = "Read the content of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["path"]
    }

    def __init__(self, workspace: Path, allowed_dir: Optional[Path] = None):
        self.workspace = workspace
        self.allowed_dir = allowed_dir or workspace

    async def run(self, path: str) -> str:
        """Run the tool."""
        file_path = self._resolve_path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _resolve_path(self, path: str) -> Path:
        """Resolve the path relative to the workspace."""
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        p = p.resolve()
        # Check if the path is within the allowed directory
        if not p.is_relative_to(self.allowed_dir):
            raise ValueError(f"Access denied: {path}")
        return p


class WriteFileTool:
    """Tool for writing files."""

    name = "write"
    description = "Write content to a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            },
            "append": {
                "type": "boolean",
                "description": "Whether to append to the file"
            }
        },
        "required": ["path", "content"]
    }

    def __init__(self, workspace: Path, allowed_dir: Optional[Path] = None):
        self.workspace = workspace
        self.allowed_dir = allowed_dir or workspace

    async def run(self, path: str, content: str, append: bool = False) -> str:
        """Run the tool."""
        file_path = self._resolve_path(path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if append:
                file_path.write_text(content, encoding="utf-8")
            else:
                file_path.write_text(content, encoding="utf-8")
            return f"File written successfully: {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def _resolve_path(self, path: str) -> Path:
        """Resolve the path relative to the workspace."""
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        p = p.resolve()
        # Check if the path is within the allowed directory
        if not p.is_relative_to(self.allowed_dir):
            raise ValueError(f"Access denied: {path}")
        return p


class EditFileTool:
    """Tool for editing files."""

    name = "edit"
    description = "Edit a file by replacing content"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit"
            },
            "old": {
                "type": "string",
                "description": "Text to replace"
            },
            "new": {
                "type": "string",
                "description": "New text"
            }
        },
        "required": ["path", "old", "new"]
    }

    def __init__(self, workspace: Path, allowed_dir: Optional[Path] = None):
        self.workspace = workspace
        self.allowed_dir = allowed_dir or workspace

    async def run(self, path: str, old: str, new: str) -> str:
        """Run the tool."""
        file_path = self._resolve_path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"
        try:
            content = file_path.read_text(encoding="utf-8")
            new_content = content.replace(old, new)
            file_path.write_text(new_content, encoding="utf-8")
            return f"File edited successfully: {path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def _resolve_path(self, path: str) -> Path:
        """Resolve the path relative to the workspace."""
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        p = p.resolve()
        # Check if the path is within the allowed directory
        if not p.is_relative_to(self.allowed_dir):
            raise ValueError(f"Access denied: {path}")
        return p


class ListDirTool:
    """Tool for listing directory contents."""

    name = "list"
    description = "List the contents of a directory"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the directory to list"
            },
            "recursive": {
                "type": "boolean",
                "description": "Whether to list recursively"
            }
        },
        "required": ["path"]
    }

    def __init__(self, workspace: Path, allowed_dir: Optional[Path] = None):
        self.workspace = workspace
        self.allowed_dir = allowed_dir or workspace

    async def run(self, path: str, recursive: bool = False) -> str:
        """Run the tool."""
        dir_path = self._resolve_path(path)
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        if not dir_path.is_dir():
            return f"Error: Not a directory: {path}"
        try:
            if recursive:
                result = []
                for root, dirs, files in os.walk(dir_path):
                    rel_path = Path(root).relative_to(dir_path)
                    if rel_path != Path("."):
                        result.append(f"📁 {rel_path}")
                    for file in files:
                        result.append(f"📄 {rel_path / file}")
                return "\n".join(result)
            else:
                result = []
                for item in dir_path.iterdir():
                    if item.is_dir():
                        result.append(f"📁 {item.name}")
                    else:
                        result.append(f"📄 {item.name}")
                return "\n".join(result)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def _resolve_path(self, path: str) -> Path:
        """Resolve the path relative to the workspace."""
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        p = p.resolve()
        # Check if the path is within the allowed directory
        if not p.is_relative_to(self.allowed_dir):
            raise ValueError(f"Access denied: {path}")
        return p
