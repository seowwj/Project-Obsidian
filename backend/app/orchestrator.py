import logging
import os
import sqlite3
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .agents.video_processor import VideoProcessor
from .agents.vector_store import VectorStore
from .agents.vision_agent import VisionAgent
from .agents.generation_agent import GenerationAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, db_path="obsidian.db"):
        logger.info("Initializing Agent Orchestrator...")
        self.db_path = db_path
        self._init_db()
        
        # Initialize Agents
        self.video_processor = VideoProcessor(model_size="small")
        self.vector_store = VectorStore()
        self.vision_agent = VisionAgent()
        self.generation_agent = GenerationAgent()
        
        # Executor for background tasks
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Trigger Model Loading in Background
        self.executor.submit(self.generation_agent.load_model)

    def is_model_ready(self):
        return self.generation_agent.is_loaded()

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

    async def upload_video(self, file_path: str) -> str:
        """
        Uploads a video, checking for duplicates via hash.
        Triggers background processing.
        Returns video_id.
        """
        if not os.path.exists(file_path):
             raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Compute Hash for Deduplication (Delegate to Video Processor)
        file_hash = self.video_processor.compute_file_hash(file_path)
        
        # 2. Check DB
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, status FROM videos WHERE video_hash = ?", (file_hash,))
            row = cursor.fetchone()
            if row:
                existing_id, status = row
                if status and status.startswith("error"):
                    logger.info(f"Video duplicate found (hash={file_hash}) but status is '{status}'. Re-processing...")
                    # Update status and re-trigger
                    self._update_status(existing_id, "processing")
                    self.executor.submit(self._process_video_task, existing_id, file_path)
                    return existing_id
                
                logger.info(f"Video duplicate found (hash={file_hash}, status={status}). Returning existing ID.")
                return existing_id

        # 3. Create New Record
        video_id = f"vid_{int(datetime.now().timestamp())}"
        created_at = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO videos (id, path, video_hash, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (video_id, file_path, file_hash, "processing", created_at)
            )
            conn.commit()

        # 4. Trigger Background Processing
        # We use the executor to run the blocking processing task
        self.executor.submit(self._process_video_task, video_id, file_path)
        
        return video_id

    def _process_video_task(self, video_id: str, file_path: str):
        """
        Background task to process video:
        - Transcribe (Whisper)
        - Extract & Analyze Frames (SmolVLM)
        - Index in Vector Store
        """
        logger.info(f"Starting background processing for {video_id}...")
        try:
            # A. Video Processing (Audio -> Text, Frames extract)
            # This runs Whisper and extracts frames
            result = self.video_processor.process_video(file_path, frame_interval=2)
            transcription = result["transcription"]
            frames = result["frames"]
            
            # Prepare Knowledge Base Documents
            documents = []
            metadatas = []
            
            # B. Add Transcription chunks
            for segment in transcription.get("segments", []):
                text = f"Timestamp {segment['start']:.1f}-{segment['end']:.1f}: {segment['text']}"
                documents.append(text)
                metadatas.append({"video_id": video_id, "type": "audio", "start": segment['start']})

            # C. Vision Analysis on Frames
            for i, frame_path in enumerate(frames):
                # Analyze with Vision Agent
                description = self.vision_agent.analyze_frame(frame_path)
                
                # Estimate timestamp roughly from filename or index
                # frame_X.jpg where X is int(timestamp)
                import re
                match = re.search(r"frame_(\d+)", frame_path)
                timestamp = int(match.group(1)) if match else i * 2
                
                text = f"Visual Frame at {timestamp}s: {description}"
                documents.append(text)
                metadatas.append({"video_id": video_id, "type": "visual", "start": float(timestamp)})
            
            # D. Index in Vector Store
            if documents:
                 self.vector_store.add_texts(documents, metadatas)
                 logger.info(f"Successfully indexed {len(documents)} documents for video {video_id}.")
            else:
                 logger.warning(f"No documents were generated for video {video_id} (Transcription empty? No frames?).")
            
            # E. Update Status
            self._update_status(video_id, "ready")
            logger.info(f"Processing complete for {video_id}.")

        except Exception as e:
            logger.error(f"Processing failed for {video_id}: {e}")
            self._update_status(video_id, f"error: {str(e)}")

    def _update_status(self, video_id: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
            conn.commit()

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
             logger.info(f"Session {session_id} is linked to video {video_id}. Checking status...")
             with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM videos WHERE id = ?", (video_id,))
                v_row = cursor.fetchone()
                if v_row:
                    status = v_row[0]
                    logger.info(f"Video {video_id} status: {status}")
                    if status == "processing":
                        yield "Video is still processing... I'll answer based on what I know so far.", "text"
                    elif status.startswith("error"):
                         yield f"Warning: Video processing had errors ({status}).", "error"

             # Retrieve Context
             logger.info(f"Searching vector store for video {video_id} with query: {message}")
             results = self.vector_store.search(
                message, 
                n_results=5, 
                where={"video_id": video_id}
             )
             documents = results['documents'][0] if results['documents'] else []
             logger.info(f"Vector store returned {len(documents)} documents.")
             
             if documents:
                 context_str = "\n".join(documents)
                 logger.info(f"Context Sample: {context_str[:200]}...")
             else:
                 logger.warning(f"No context found for video {video_id}!")

        else:
             logger.info(f"Session {session_id} is NOT linked to any video.")

        # 2.5 Retrieve Chat History (Last 6 messages)
        history = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Fetch last 6 messages excluding the one we just added
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT 6 OFFSET 1",
                (session_id,)
            )
            rows = cursor.fetchall()
            # Reverse to Chronological Order
            import re
            for r in reversed(rows):
                content = r[1]
                # Remove <think>...</think> blocks
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                if content: # Only append if there is content left
                    history.append({"role": r[0], "content": content})

        # 3. Generate Response
        response_text = ""
        
        # Use GenerationAgent for streaming response
        # Using executor to run the synchronous stream generator might be tricky since specialized thread is used inside generation_agent.
        # However, generate_response_stream returns a generator.
        # We can iterate over it directly if it launches its own thread (which we did implement).
        
        try:
            stream_generator = self.generation_agent.generate_response_stream(context_str, message, history=history)
            
            for chunk in stream_generator:
                response_text += chunk
                yield chunk, "text"
                await asyncio.sleep(0.01) # Yield to event loop
        except Exception as e:
            logger.error(f"Generation error: {e}")
            yield f"Error generating response: {e}", "error"
            return
        
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
