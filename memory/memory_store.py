"""
🧠 Memory Store

Manages session and long-term memory for AI interactions.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import logger


class MemoryStore:
    """
    Memory management system for AI agents.

    Features:
    - Session memory (short-term)
    - Long-term memory storage
    - Context window management
    - Memory retrieval and summarization
    """

    def __init__(self):
        self.session_memory: Dict[str, List[Dict]] = {}
        self.long_term_memory: Dict[str, List[Dict]] = {}
        self.context_window = 10
        self.session_ttl = timedelta(hours=24)

        logger.info("🧠 Memory Store initialized")

    async def add_to_session(self, session_id: str, entry: Dict[str, Any]):
        """
        Add entry to session memory.

        Args:
            session_id: Session identifier
            entry: Memory entry
        """
        if session_id not in self.session_memory:
            self.session_memory[session_id] = []

        entry["timestamp"] = datetime.now().isoformat()
        self.session_memory[session_id].append(entry)

        # Keep only recent entries
        if len(self.session_memory[session_id]) > self.context_window * 2:
            self.session_memory[session_id] = self.session_memory[session_id][
                -self.context_window * 2 :
            ]

    async def get_session_context(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get session memory context.

        Args:
            session_id: Session identifier
            limit: Maximum entries to return

        Returns:
            List of memory entries
        """
        if session_id not in self.session_memory:
            return []

        entries = self.session_memory[session_id]

        if limit:
            entries = entries[-limit:]

        return entries

    async def add_to_long_term(
        self, user_id: str, entry: Dict[str, Any], category: Optional[str] = None
    ):
        """
        Add entry to long-term memory.

        Args:
            user_id: User identifier
            entry: Memory entry
            category: Optional category
        """
        if user_id not in self.long_term_memory:
            self.long_term_memory[user_id] = []

        entry["timestamp"] = datetime.now().isoformat()
        entry["category"] = category or "general"

        self.long_term_memory[user_id].append(entry)

    async def query_long_term(
        self, user_id: str, category: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query long-term memory.

        Args:
            user_id: User identifier
            category: Optional category filter
            limit: Maximum entries to return

        Returns:
            List of memory entries
        """
        if user_id not in self.long_term_memory:
            return []

        entries = self.long_term_memory[user_id]

        if category:
            entries = [e for e in entries if e.get("category") == category]

        return entries[-limit:]

    async def clear_session(self, session_id: str):
        """Clear session memory"""
        if session_id in self.session_memory:
            del self.session_memory[session_id]

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        cutoff = datetime.now() - self.session_ttl
        expired = []

        for session_id, entries in self.session_memory.items():
            if entries:
                try:
                    # Safely get timestamp with fallback
                    last_entry = entries[-1]
                    if "timestamp" in last_entry:
                        last_timestamp = datetime.fromisoformat(last_entry["timestamp"])
                        if last_timestamp < cutoff:
                            expired.append(session_id)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid timestamp in session {session_id}: {e}")
                    expired.append(session_id)  # Remove sessions with invalid timestamps

        for session_id in expired:
            del self.session_memory[session_id]

        return len(expired)

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        return {
            "active_sessions": len(self.session_memory),
            "users_with_memory": len(self.long_term_memory),
            "total_session_entries": sum(len(e) for e in self.session_memory.values()),
            "total_long_term_entries": sum(len(e) for e in self.long_term_memory.values()),
            "context_window": self.context_window,
        }


# Singleton instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get or create memory store singleton"""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
