"""Session manager for handling conversation history."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class Session:
    """A single conversation session."""

    def __init__(self, key: str):
        self.key = key
        self.messages: List[Dict[str, Any]] = []
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: Any) -> None:
        """Add a message to the session."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)

    def get_history(self, max_messages: int = 100) -> List[Dict[str, Any]]:
        """Get the session history."""
        if max_messages <= 0:
            return self.messages
        return self.messages[-max_messages:]


class SessionManager:
    """Manage multiple sessions."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.sessions_dir = workspace / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Session] = {}

    def get_or_create(self, key: str) -> Session:
        """Get an existing session or create a new one."""
        if key not in self._sessions:
            self._sessions[key] = self._load_session(key)
        return self._sessions[key]

    def save(self, session: Session) -> None:
        """Save a session to disk."""
        session_file = self.sessions_dir / f"{session.key}.jsonl"
        with open(session_file, "w", encoding="utf-8") as f:
            for message in session.messages:
                json.dump(message, f, ensure_ascii=False)
                f.write("\n")

    def _load_session(self, key: str) -> Session:
        """Load a session from disk."""
        session = Session(key)
        session_file = self.sessions_dir / f"{session.key}.jsonl"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            message = json.loads(line)
                            session.messages.append(message)
            except Exception as e:
                print(f"Error loading session {key}: {e}")
        return session
