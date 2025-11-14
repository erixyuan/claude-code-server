"""
File-based session storage for persistence across restarts.
"""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from .types import SessionData


class FileSessionStore:
    """
    File-based session storage.

    Stores sessions as JSON files in a directory.
    Survives server restarts.
    """

    def __init__(self, storage_dir: str = ".sessions"):
        """
        Initialize file session store.

        Args:
            storage_dir: Directory to store session files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def _get_file_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        # Sanitize session_id for filename
        safe_id = session_id.replace("/", "_").replace("\\", "_")
        return self.storage_dir / f"{safe_id}.json"

    def get(self, session_id: str) -> Optional[SessionData]:
        """Retrieve a session by ID."""
        file_path = self._get_file_path(session_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Parse dates
            if "created_at" in data:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            if "last_activity" in data:
                data["last_activity"] = datetime.fromisoformat(data["last_activity"])

            # Parse messages
            if "conversation_history" in data:
                for msg in data["conversation_history"]:
                    if "timestamp" in msg:
                        msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])

            return SessionData(**data)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def save(self, session: SessionData) -> None:
        """Save a session."""
        session.last_activity = datetime.now()
        file_path = self._get_file_path(session.session_id)

        try:
            # Convert to dict
            data = session.model_dump()

            # Convert dates to ISO format
            if "created_at" in data:
                data["created_at"] = data["created_at"].isoformat()
            if "last_activity" in data:
                data["last_activity"] = data["last_activity"].isoformat()

            # Convert message timestamps
            if "conversation_history" in data:
                for msg in data["conversation_history"]:
                    if "timestamp" in msg:
                        msg["timestamp"] = msg["timestamp"].isoformat()

            # Write to file
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()

    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._get_file_path(session_id).exists()

    def list_all(self) -> list[str]:
        """List all session IDs."""
        return [
            f.stem for f in self.storage_dir.glob("*.json")
        ]

    def cleanup_old_sessions(self, max_age_seconds: int = 86400):
        """
        Clean up old sessions.

        Args:
            max_age_seconds: Delete sessions older than this (default: 24 hours)
        """
        now = datetime.now()
        for file_path in self.storage_dir.glob("*.json"):
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age = (now - mtime).total_seconds()

                if age > max_age_seconds:
                    file_path.unlink()
                    print(f"Cleaned up old session: {file_path.stem}")
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")
