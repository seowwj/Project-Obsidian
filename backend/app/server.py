import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import uvicorn

# Monkeypatch for aiosqlite 0.22.0+ compatibility with langgraph-checkpoint-sqlite 3.0.1
# See: https://github.com/langchain-ai/langgraph/issues/6583
# aiosqlite 0.22.0 removed is_alive() since Connection no longer inherits from Thread
import aiosqlite
if not hasattr(aiosqlite.Connection, 'is_alive'):
    aiosqlite.Connection.is_alive = lambda self: True
    logger.info("Applied aiosqlite Connection.is_alive monkeypatch")

from .orchestrator import AgentOrchestrator
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from .config import CHAT_DB_PATH

# Global orchestrator instance
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("Initializing Agent Orchestrator...")
    logger.info(f"Setting up AsyncSqliteSaver with database: {CHAT_DB_PATH}")
    
    # Use AsyncSqliteSaver context manager - keeps connection open for app lifetime
    # Following the exact pattern from LangGraph docs
    async with AsyncSqliteSaver.from_conn_string(CHAT_DB_PATH) as checkpointer:
        orchestrator = AgentOrchestrator(checkpointer=checkpointer)
        logger.info("Agent Orchestrator initialized with persistent SQLite checkpointer")
        yield
        # Context manager handles cleanup when app shuts down
    
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_path: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from fastapi.responses import StreamingResponse
import asyncio
import os

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    queue = asyncio.Queue()

    async def token_callback(token: str):
        await queue.put(token)

    async def run_generation():
        try:
            config = {"configurable": {"stream_callback": token_callback}}
            if request.session_id:
                config["configurable"]["thread_id"] = request.session_id
            
            # Prepare input
            inputs = {"messages": [HumanMessage(content=request.message)]}
            
            # Check for file attachments
            if request.file_path:
                from .utils.file_utils import compute_sha256
                ext = os.path.splitext(request.file_path)[1].lower()
                
                # Compute new media_id from file hash
                new_media_id = compute_sha256(request.file_path)
                logger.info(f"New file media_id: {new_media_id[:16]}...")
                
                if ext in ['.wav', '.mp3', '.m4a', '.flac']:
                    logger.info(f"Injecting audio path: {request.file_path}")
                    inputs["audio_path"] = request.file_path
                    inputs["video_path"] = ""  # Clear video path
                    # Force new media_id to override stale state
                    inputs["media_id"] = new_media_id
                    inputs["vlm_processed"] = False
                elif ext in ['.mp4', '.mkv', '.mov', '.avi']:
                    logger.info(f"Injecting video path: {request.file_path}")
                    inputs["video_path"] = request.file_path
                    inputs["audio_path"] = ""  # Clear audio path
                    # Force new media_id to override stale state
                    inputs["media_id"] = new_media_id
                    inputs["vlm_processed"] = False
                else:
                    logger.warning(f"Unsupported file type: {ext}")
            
            await orchestrator.graph.ainvoke(
                inputs,
                config=config
            )
        except Exception as e:
            logger.error(f"Error in generation: {e}")
        finally:
            await queue.put(None) # Signal end of stream

    async def stream_generator():
        # Start generation in background
        task = asyncio.create_task(run_generation())

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

        await task

    return StreamingResponse(stream_generator(), media_type="text/plain")

def run():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    run()
