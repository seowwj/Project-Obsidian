import logging
import sqlite3
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, db_path="obsidian.db"):
        logger.info("Initializing Agent Orchestrator...")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    path TEXT,
                    status TEXT,
                    created_at TEXT
                )
            ''')
            # Chat history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(video_id) REFERENCES videos(id)
                )
            ''')
            conn.commit()

    async def upload_video(self, file_path: str) -> str:
        """
        Processes a video upload.
        """
        logger.info(f"Processing video: {file_path}")
        video_id = f"vid_{int(datetime.now().timestamp())}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO videos (id, path, status, created_at) VALUES (?, ?, ?, ?)",
                (video_id, file_path, "ready", datetime.now().isoformat())
            )
            conn.commit()
            
        return video_id

    async def chat(self, video_id: str, message: str):
        """
        Handles a chat message.
        """
        # Verify video exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM videos WHERE id = ?", (video_id,))
            if not cursor.fetchone():
                yield "Error: Video ID not found.", "error"
                return

            # Store user message
            timestamp = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chat_history (video_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (video_id, "user", message, timestamp)
            )
            conn.commit()

        # Mock response for now (Logic to route to agents goes here)
        response_text = f"Echo: {message}. (Persistence Enabled)"
        
        # Simulate streaming
        for word in response_text.split():
            yield word + " ", "text"
        
        # Store assistant message
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (video_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (video_id, "assistant", response_text, datetime.now().isoformat())
            )
            conn.commit()

    def get_history(self, video_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM chat_history WHERE video_id = ? ORDER BY id ASC",
                (video_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
