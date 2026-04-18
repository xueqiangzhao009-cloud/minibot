"""Session manager for handling conversation history."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class Session:
    """A single conversation session."""

    def __init__(
        self,
        key: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        last_consolidated: int = 0,
    ):
        self.key = key
        self.messages = messages or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
        self.last_consolidated = last_consolidated

    def add_message(self, role: str, content: Any) -> None:
        """Add a message to the session."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_history(self, max_messages: int = 100) -> List[Dict[str, Any]]:
        """Get the session history."""
        if max_messages <= 0:
            return self.messages
        return self.messages[-max_messages:]

    def retain_recent_legal_suffix(self, count: int) -> None:
        """Retain only the last N messages that are 'legal' (not from tool calls).

        Tool messages are 'illegal' and should be removed when truncating history.
        This ensures that tool call/result pairs stay intact.
        """
        if count <= 0:
            self.messages = []
            return

        if len(self.messages) <= count:
            return

        recent = self.messages[-count:]

        illegal_indices = set()
        for i, msg in enumerate(recent):
            role = msg.get("role", "")
            if role == "tool":
                illegal_indices.add(i)

        if not illegal_indices:
            self.messages = recent
            return

        illegal_ranges: List[tuple] = []
        start = None
        for i, msg in enumerate(recent):
            role = msg.get("role", "")
            if role == "tool":
                if start is None:
                    start = i
            else:
                if start is not None:
                    illegal_ranges.append((start, i))
                    start = None
        if start is not None:
            illegal_ranges.append((start, len(recent)))

        legal_messages = []
        for i, msg in enumerate(recent):
            skip = False
            for start_idx, end_idx in illegal_ranges:
                if start_idx <= i < end_idx:
                    skip = True
                    break
            if not skip:
                legal_messages.append(msg)

        self.messages = legal_messages


class SessionManager:
    """Manage multiple sessions."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.sessions_dir = workspace / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Session] = {}
        self._index_file = workspace / "sessions_index.json"

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
        session.updated_at = datetime.now()
        self._update_index(session)

    def invalidate(self, key: str) -> None:
        """Invalidate a session from in-memory cache."""
        if key in self._sessions:
            del self._sessions[key]

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with their metadata."""
        sessions = []
        index = self._load_index()
        for key, info in index.items():
            sessions.append({
                "key": key,
                "updated_at": info.get("updated_at"),
                "created_at": info.get("created_at"),
            })
        if not sessions:
            for session_file in self.sessions_dir.glob("*.jsonl"):
                key = session_file.stem
                sessions.append({
                    "key": key,
                    "updated_at": datetime.fromtimestamp(session_file.stat().st_mtime).isoformat(),
                    "created_at": datetime.fromtimestamp(session_file.stat().st_ctime).isoformat(),
                })
        return sessions

    def _load_index(self) -> Dict[str, Any]:
        """Load session index."""
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _update_index(self, session: Session) -> None:
        """Update session index."""
        index = self._load_index()
        index[session.key] = {
            "updated_at": session.updated_at.isoformat(),
            "created_at": session.created_at.isoformat(),
        }
        try:
            self._index_file.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

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
                stat = session_file.stat()
                session.created_at = datetime.fromtimestamp(stat.st_ctime)
                session.updated_at = datetime.fromtimestamp(stat.st_mtime)
            except Exception as e:
                print(f"Error loading session {key}: {e}")
        return session
