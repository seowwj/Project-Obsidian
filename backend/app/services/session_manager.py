"""
Session Manager
Handles the `sessions` table in the same SQLite database used by LangGraph.
"""

import aiosqlite
import logging
import time
from typing import List, Optional
from dataclasses import dataclass

from ..config import CHAT_DB_PATH

logger = logging.getLogger(__name__)

@dataclass
class Session:
    id: str
    title: str
    created_at: int
    updated_at: int

class SessionManager:
    def __init__(self, db_path: str = CHAT_DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initialize the sessions table."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            """)
            await db.commit()

    async def list_sessions(self) -> List[Session]:
        """List all sessions ordered by updated_at desc."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [Session(*row) for row in rows]

    async def create_session(self, session_id: str, title: str = "New Chat") -> Session:
        """Create a new session."""
        now = int(time.time() * 1000)
        session = Session(id=session_id, title=title, created_at=now, updated_at=now)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session.id, session.title, session.created_at, session.updated_at)
            )
            await db.commit()
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Session(*row)
        return None

    async def rename_session(self, session_id: str, new_title: str) -> Optional[Session]:
        """Rename a session."""
        now = int(time.time() * 1000)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (new_title, now, session_id)
            )
            await db.commit()
            
        return await self.get_session(session_id)

    async def update_timestamp(self, session_id: str):
        """Update the updated_at timestamp (e.g. when a new message is sent)."""
        now = int(time.time() * 1000)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )
            await db.commit()

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated LangGraph state."""
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Delete from sessions table
            cursor = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            if cursor.rowcount == 0:
                return False
            
            # 2. Cleanup LangGraph state (checkpoints and writes)
            # LangGraph 3.0+ uses (thread_id, checkpoint_ns, checkpoint_id) PK
            await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
            await db.execute("DELETE FROM writes WHERE thread_id = ?", (session_id,))
            
            await db.commit()
            return True
