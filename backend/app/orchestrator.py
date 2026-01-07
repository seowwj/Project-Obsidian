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
                logger.info("Migrated DB: Added 'video_hash' column.")
            except sqlite3.OperationalError:
                pass # Column likely already exists

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

    def _process_video_task(self, video_id: str, file_path: str):
        """
        Blocking task to be run in executor.
        """
        try:
            logger.info(f"Background processing started for {video_id}")
            self._update_status(video_id, "processing")
            
            # 1. Extract Audio & Frames
            # Load Whisper Model
            self.video_processor.load_model()
            # Returns { "transcription": {...}, "frames": [path1, path2, ...] }
            data = self.video_processor.process_video(file_path)
            # Unload Whisper Model immediately
            self.video_processor.unload_model()
            
            # 2. Index Audio Transcription
            transcription = data["transcription"]
            segments = transcription["segments"]
            
            chunks = [s["text"] for s in segments]
            metadatas = [{"video_id": video_id, "start": s["start"], "end": s["end"], "type": "audio"} for s in segments]
            
            self.vector_store.add_texts(chunks, metadatas)
            logger.info(f"Indexed {len(chunks)} audio segments.")

            # 3. Analyze & Index Frames (Vision)
            frames = data["frames"]
            if frames:
                logger.info(f"Analyzing {len(frames)} frames with Vision Agent...")
                # Load Vision Model
                self.vision_agent.load_model()
                
                vision_texts = []
                vision_metas = []
                
                for i, frame_path in enumerate(frames):
                    # Progress Update
                    if i % 2 == 0: # Update every 2 frames to reduce DB spam
                         self._update_status(video_id, f"processing: Analyzing frame {i+1}/{len(frames)}")

                    # Simple interval based timestamp estimation
                    timestamp = i * 2.0  # Assumes 2s interval from video_processor default
                    
                    description = self.vision_agent.analyze_frame(frame_path)
                    
                    vision_texts.append(f"Frame at {timestamp}s: {description}")
                    vision_metas.append({
                        "video_id": video_id, 
                        "start": timestamp, 
                        "end": timestamp + 1.0, 
                        "type": "visual"
                    })
                
                # Unload Vision Model
                self.vision_agent.unload()
                    
                self.vector_store.add_texts(vision_texts, vision_metas)
                logger.info(f"Indexed {len(vision_texts)} visual descriptions.")

            # 4. Update status to ready
            self._update_status(video_id, "ready")
            logger.info(f"Background processing completed for {video_id}")
            
        except Exception as e:
            logger.error(f"Processing failed for {video_id}: {e}", exc_info=True)
            self._update_status(video_id, f"error: {str(e)}")

    def _update_status(self, video_id: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
            conn.commit()

    def _compute_file_hash(self, file_path: str) -> str:
        """Computes SHA-256 hash of the file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def upload_video(self, file_path: str) -> str:
        """
        Processes a video upload.
        """
        import os
        if not os.path.exists(file_path):
             raise FileNotFoundError(f"Video not found at: {file_path}")

        # [NEW] Validation
        ALLOWED_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi'}
        MAX_SIZE_MB = 200
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file type {ext}. Supported: {', '.join(ALLOWED_EXTENSIONS)}")
            
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            raise ValueError(f"File too large ({size_mb:.2f}MB). Limit is {MAX_SIZE_MB}MB.")

        # Deduplication Check
        video_hash = self._compute_file_hash(file_path)
        logger.info(f"Computed hash for {file_path}: {video_hash}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM videos WHERE video_hash = ?", (video_hash,))
            row = cursor.fetchone()
            if row:
                existing_id = row[0]
                logger.info(f"♻️ Deduplication: Video {existing_id} already exists with hash {video_hash}. Skipping processing.")
                return existing_id

        logger.info(f"Receiving new video: {file_path} (Hash: {video_hash})")
        video_id = f"vid_{int(datetime.now().timestamp())}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO videos (id, path, video_hash, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (video_id, file_path, video_hash, "uploaded", datetime.now().isoformat())
            )
            conn.commit()
            
        # Offload processing to background thread so we don't block the gRPC response
        loop = asyncio.get_running_loop()
        loop.run_in_executor(self.executor, self._process_video_task, video_id, file_path)
            
        return video_id

    async def chat(self, video_id: str, message: str):
        """
        Handles a chat message with RAG.
        """
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
        # Filter by video_id to ensure we only get context for THIS video
        results = self.vector_store.search(
            message, 
            n_results=5, 
            where={"video_id": video_id}
        )
        documents = results['documents'][0] if results['documents'] else []
        
        context_str = "\n".join(documents)
        logger.info(f"Retrieved context: {context_str}")
        
        # 2. Construct Response (Simulated LLM for now)
        # In Phase 4, we will pass this to Phi-3
        response_text = f"Based on the video content:\n{context_str}\n\n(Answer generated from {len(documents)} context chunks)"
        
        # Simulate streaming
        for word in response_text.split(" "):
            yield word + " ", "text"
            await asyncio.sleep(0.05) # Simulate token generation delay
        
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
