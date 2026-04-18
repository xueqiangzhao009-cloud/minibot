"""Auto compact: proactive compression of idle sessions to reduce token cost and latency."""

from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional

from loguru import logger


class Consolidator:
    """Consolidator interface for archiving messages."""

    def __init__(self, summarize_skill_path: Optional[str] = None):
        self.summarize_skill_path = summarize_skill_path

    async def archive(self, messages: list[dict[str, Any]]) -> str:
        """Archive messages and return a summary.

        Default implementation creates a simple summary.
        Override to use external summarization service.
        """
        if not messages:
            return "(nothing)"

        user_messages = [
            m.get("content", "")
            for m in messages
            if m.get("role") == "user" and m.get("content")
        ]
        if not user_messages:
            return "(no user messages)"

        preview = user_messages[:3]
        preview_text = "; ".join(preview[:100] + ["..."] if sum(len(p) for p in preview) > 100 else preview)
        return f"User discussed: {preview_text}"


class AutoCompact:
    """Auto compaction for idle sessions."""

    _RECENT_SUFFIX_MESSAGES = 8

    def __init__(
        self,
        sessions: Any,
        consolidator: Optional[Consolidator] = None,
        session_ttl_minutes: int = 0,
    ):
        self.sessions = sessions
        self.consolidator = consolidator or Consolidator()
        self._ttl = session_ttl_minutes
        self._archiving: set[str] = set()
        self._summaries: dict[str, tuple[str, datetime]] = {}

    def _is_expired(
        self, ts: datetime | str | None, now: datetime | None = None
    ) -> bool:
        if self._ttl <= 0 or not ts:
            return False
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return ((now or datetime.now()) - ts).total_seconds() >= self._ttl * 60

    @staticmethod
    def _format_summary(text: str, last_active: datetime) -> str:
        idle_min = int((datetime.now() - last_active).total_seconds() / 60)
        return f"Inactive for {idle_min} minutes.\nPrevious conversation summary: {text}"

    def _split_unconsolidated(
        self, session: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split live session tail into archiveable prefix and retained recent suffix."""
        tail = list(session.messages[session.last_consolidated:])
        if not tail:
            return [], []

        from minibot.session.manager import Session

        probe = Session(
            key=session.key,
            messages=tail.copy(),
            created_at=session.created_at,
            updated_at=session.updated_at,
            metadata={},
            last_consolidated=0,
        )
        probe.retain_recent_legal_suffix(self._RECENT_SUFFIX_MESSAGES)
        kept = probe.messages
        cut = len(tail) - len(kept)
        return tail[:cut], kept

    def check_expired(
        self,
        schedule_background: Callable[[Coroutine[Any, Any, None]], None],
        active_session_keys: Collection[str] = (),
    ) -> None:
        """Schedule archival for idle sessions."""
        now = datetime.now()
        for info in self.sessions.list_sessions():
            key = info.get("key", "")
            if not key or key in self._archiving:
                continue
            if key in active_session_keys:
                continue
            if self._is_expired(info.get("updated_at"), now):
                self._archiving.add(key)
                schedule_background(self._archive(key))

    async def _archive(self, key: str) -> None:
        try:
            self.sessions.invalidate(key)
            session = self.sessions.get_or_create(key)
            archive_msgs, kept_msgs = self._split_unconsolidated(session)

            if not archive_msgs and not kept_msgs:
                session.updated_at = datetime.now()
                self.sessions.save(session)
                return

            last_active = session.updated_at
            summary = ""
            if archive_msgs:
                summary = await self.consolidator.archive(archive_msgs) or ""

            if summary and summary != "(nothing)":
                self._summaries[key] = (summary, last_active)
                session.metadata["_last_summary"] = {
                    "text": summary,
                    "last_active": last_active.isoformat()
                }

            session.messages = kept_msgs
            session.last_consolidated = 0
            session.updated_at = datetime.now()
            self.sessions.save(session)

            if archive_msgs:
                logger.info(
                    "Auto-compact: archived {} (archived={}, kept={}, summary={})",
                    key,
                    len(archive_msgs),
                    len(kept_msgs),
                    bool(summary),
                )
        except Exception:
            logger.exception("Auto-compact: failed for {}", key)
        finally:
            self._archiving.discard(key)

    def prepare_session(self, session: Any, key: str) -> tuple[Any, str | None]:
        """Prepare session for use, returning summary if available."""
        if key in self._archiving or self._is_expired(session.updated_at):
            logger.info(
                "Auto-compact: reloading session {} (archiving={})",
                key,
                key in self._archiving,
            )
            session = self.sessions.get_or_create(key)

        entry = self._summaries.pop(key, None)
        if entry:
            session.metadata.pop("_last_summary", None)
            return session, self._format_summary(entry[0], entry[1])

        if "_last_summary" in session.metadata:
            meta = session.metadata.pop("_last_summary")
            self.sessions.save(session)
            return session, self._format_summary(
                meta["text"], datetime.fromisoformat(meta["last_active"])
            )

        return session, None
