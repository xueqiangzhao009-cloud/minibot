import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from minibot.bus.message import InboundMessage

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Build context for LLM calls."""

    def __init__(self, workspace: Path, timezone: Optional[str] = None, disabled_skills: Optional[List[str]] = None):
        self.workspace = workspace
        self.agents_dir = workspace / "AGENTS"
        self.soul_dir = workspace / "SOUL"
        self.tools_dir = workspace / "TOOLS"
        self.identity_dir = workspace / "IDENTITY"
        self.memory_dir = workspace / "memory"
        self.timezone = timezone
        self.disabled_skills = disabled_skills or []

    def build_messages(self, history: List[Dict[str, Any]], current_message: str, channel: str, chat_id: str) -> List[Dict[str, Any]]:
        """Build messages for LLM calls."""
        context = []

        # Add system prompt
        system_prompt = self._load_system_prompt()
        if system_prompt:
            context.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            # Default system prompt
            context.append({
                "role": "system",
                "content": "You are a helpful AI assistant. You can use tools to help users with their tasks."
            })

        # Add identity
        identity = self._load_identity()
        if identity:
            context.append({
                "role": "system",
                "content": f"Identity: {identity}"
            })

        # Add tools description
        tools_description = self._load_tools_description()
        if tools_description:
            context.append({
                "role": "system",
                "content": f"Tools: {tools_description}"
            })

        # Add history messages
        for msg in history:
            if msg["role"] in ["user", "assistant", "tool", "system"]:
                context.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current message if it's not empty
        if current_message:
            context.append({
                "role": "user",
                "content": current_message
            })

        return context

    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_file = self.soul_dir / "system.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return ""

    def _load_identity(self) -> str:
        """Load identity from file."""
        identity_file = self.identity_dir / "identity.md"
        if identity_file.exists():
            return identity_file.read_text(encoding="utf-8")
        return ""

    def _load_tools_description(self) -> str:
        """Load tools descriptions from files."""
        tools = []
        for tool_file in self.tools_dir.glob("*.md"):
            tools.append(tool_file.read_text(encoding="utf-8"))
        return "\n".join(tools)

