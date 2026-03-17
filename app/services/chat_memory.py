"""
Chat memory service — conversation history management.
"""

from collections import defaultdict
from datetime import datetime, timezone


class ChatMemoryService:
    """Manages conversation history per session."""

    def __init__(self):
        # session_id → list of messages
        self.sessions: dict[str, list[dict]] = defaultdict(list)

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history."""
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_history(self, session_id: str, limit: int = 20) -> list[dict]:
        """Get the last N messages from a session."""
        messages = self.sessions.get(session_id, [])
        return messages[-limit:]

    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        self.sessions.pop(session_id, None)
