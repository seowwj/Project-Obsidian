import logging
import sqlite3
import json
import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from agents.video_processor import VideoProcessor
from agents.vector_store import VectorStore
from agents.vision_agent import VisionAgent
from agents.generation_agent import GenerationAgent

# ... (imports)

class AgentOrchestrator:
    def __init__(self, db_path="obsidian.db"):
        # ...
        self.video_processor = VideoProcessor(model_size="small")
        self.vector_store = VectorStore()
        self.vision_agent = VisionAgent()
        self.generation_agent = GenerationAgent() # Phi-3
        
        # ...

    async def chat(self, video_id: str, message: str):
        # ... (Validation logic same as before) ...
        # Verify video exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, status FROM videos WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            if not row:
                yield "Error: Video ID not found.", "error"
                return
            
            status = row[1]
            if status == "processing":
                 yield "Video is still processing... please wait a moment.", "text"
                 return
            elif status.startswith("error"):
                 yield f"Video processing failed: {status}", "error"
                 return

            # Store user message
            timestamp = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chat_history (video_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (video_id, "user", message, timestamp)
            )
            conn.commit()

        # 1. Retrieve Context from Vector Store
        results = self.vector_store.search(message, n_results=5) # Increased context
        documents = results['documents'][0] if results['documents'] else []
        
        context_str = "\n".join(documents)
        logger.info(f"Retrieved context: {context_str}")
        
        if not context_str:
            context_str = "No specific context found in the video."

        # 2. Generate Response using Phi-3
        # Offload to thread to avoid blocking async loop
        loop = asyncio.get_running_loop()
        response_text = await loop.run_in_executor(
            self.executor, 
            self.generation_agent.generate_response, 
            context_str, 
            message
        )
        
        # Yield result
        yield response_text, "text"
        
        # Store assistant message
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (video_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (video_id, "assistant", response_text, datetime.now().isoformat())
            )
            conn.commit()
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, db_path="obsidian.db"):
        logger.info("Initializing Agent Orchestrator...")
        self.db_path = db_path
        self._init_db()
        
        # Initialize Agents
        self.video_processor = VideoProcessor(model_size="small")
        self.vector_store = VectorStore()
        # Initialize Vision Agent (this downloads Florence-2 ~1GB)
        self.vision_agent = VisionAgent()
        
        # Executor for background tasks
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    path TEXT,
                    video_hash TEXT,
                    status TEXT,
                    created_at TEXT
                )
            ''')

            # Migration: Ensure video_hash column exists for existing DBs
            try:
                cursor.execute("ALTER TABLE videos ADD COLUMN video_hash TEXT")
            except sqlite3.OperationalError:
                pass 

            # Sessions table [NEW]
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    video_id TEXT,
                    created_at TEXT,
                    FOREIGN KEY(video_id) REFERENCES videos(id)
                )
            ''')

            # Chat history table [UPDATED]
            # We add session_id. For backward compatibility, we keep video_id nullable but prioritize session_id.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    video_id TEXT, 
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id),
                    FOREIGN KEY(video_id) REFERENCES videos(id)
                )
            ''')
            
            # Migration: Add session_id to chat_history if not exists
            try:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT")
            except sqlite3.OperationalError:
                pass

            conn.commit()

    # ... [keep _process_video_task, _update_status, _compute_file_hash, upload_video as is] ...

    def create_session(self, video_id: str = None) -> str:
        """Creates a new chat session."""
        session_id = f"sess_{int(datetime.now().timestamp())}"
        title = "New Chat"
        if video_id:
            # Fetch video name for title
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT path FROM videos WHERE id = ?", (video_id,))
                row = cursor.fetchone()
                if row:
                    import os
                    filename = os.path.basename(row[0])
                    title = f"Chat about {filename}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (id, title, video_id, created_at) VALUES (?, ?, ?, ?)",
                (session_id, title, video_id, datetime.now().isoformat())
            )
            conn.commit()
        return session_id

    def list_sessions(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    def rename_session(self, session_id: str, new_title: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
            conn.commit()

    async def chat(self, session_id: str, message: str):
        """
        Handles a chat message within a session.
        """
        # 1. Get Session Details
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT video_id FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                yield "Error: Session not found.", "error"
                return
            video_id = row[0] # Can be None for text-only

            # Store user message
            timestamp = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "user", message, timestamp)
            )
            conn.commit()

        context_str = ""
        # 2. If Linked to Video, Check Status & Retrieve Context
        if video_id:
             with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM videos WHERE id = ?", (video_id,))
                v_row = cursor.fetchone()
                if v_row:
                    status = v_row[0]
                    if status == "processing":
                        yield "Video is still processing... I'll answer based on what I know so far.", "text"
                    elif status.startswith("error"):
                         yield f"Warning: Video processing had errors ({status}).", "error"

             # Retrieve Context
             results = self.vector_store.search(
                message, 
                n_results=5, 
                where={"video_id": video_id}
             )
             documents = results['documents'][0] if results['documents'] else []
             context_str = "\n".join(documents)
             logger.info(f"Retrieved context for video {video_id}: {context_str}")

        # 3. Generate Response
        # In a real app, we pass context_str + message to LLM
        if context_str:
            response_text = f"Based on the video content:\n{context_str}\n\n(Answer generated from {len(documents)} context chunks)"
        else:
            # Text-only or no context found
            if video_id:
                response_text = "I couldn't find specific details in the video about that."
            else:
                response_text = f"I am a text-only assistant in this session. You said: {message}"
        
        # Simulate streaming
        for word in response_text.split(" "):
            yield word + " ", "text"
            await asyncio.sleep(0.05)
        
        # Store assistant message
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "assistant", response_text, datetime.now().isoformat())
            )
            conn.commit()

    def get_history(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM chat_history WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_videos(self):
        """
        Lists all videos ordered by creation time (desc).
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, path, status, created_at FROM videos ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
