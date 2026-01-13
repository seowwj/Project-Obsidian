"""
Project Obsidian Server

Hybrid FastAPI + ConnectRPC server.
- ConnectRPC: Chat, Health services (for TypeScript frontend)
- REST: /health, /chat (for backward compatibility with client.py)
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Add gen folder to Python path for proto imports
_backend_dir = Path(__file__).parent.parent
_gen_dir = _backend_dir / "gen"
if str(_gen_dir) not in sys.path:
    sys.path.insert(0, str(_gen_dir))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Monkeypatch for aiosqlite 0.22.0+ compatibility with langgraph-checkpoint-sqlite 3.0.1
# See: https://github.com/langchain-ai/langgraph/issues/6583
import aiosqlite
if not hasattr(aiosqlite.Connection, 'is_alive'):
    aiosqlite.Connection.is_alive = lambda self: True
    logger.info("Applied aiosqlite Connection.is_alive monkeypatch")

from .orchestrator import AgentOrchestrator
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from .config import CHAT_DB_PATH

# ConnectRPC imports - now using the gen folder in PYTHONPATH
from obsidian.v1.obsidian_connect import (
    ChatServiceASGIApplication,
    HealthServiceASGIApplication,
    SessionServiceASGIApplication,
    HistoryServiceASGIApplication,
)
from .services import ObsidianChatService, ObsidianHealthService
from .services.session_service import ObsidianSessionService
from .services.history_service import ObsidianHistoryService
from .services.session_manager import SessionManager

# Global orchestrator and manager instances
orchestrator: AgentOrchestrator | None = None
session_manager: SessionManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, session_manager
    logger.info("Initializing Agent Orchestrator...")
    logger.info(f"Setting up AsyncSqliteSaver with database: {CHAT_DB_PATH}")

    # Initialize Session Manager (creates tables if needed)
    session_manager = SessionManager(CHAT_DB_PATH)
    await session_manager.init_db()

    async with AsyncSqliteSaver.from_conn_string(CHAT_DB_PATH) as checkpointer:
        orchestrator = AgentOrchestrator(checkpointer=checkpointer)
        logger.info("Agent Orchestrator initialized with persistent SQLite checkpointer")
        yield

    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

# CORS middleware will be added at the top level to cover both FastAPI and ConnectRPC


# =============================================================================
# REST Endpoints (backward compatibility with client.py)
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_path: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
async def health_check():
    """REST health check endpoint."""
    return {"status": "ok"}


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    REST chat endpoint with streaming response.
    For backward compatibility with client.py.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def token_callback(token: str):
        await queue.put(token)

    async def run_generation():
        try:
            config = {"configurable": {"stream_callback": token_callback}}
            if request.session_id:
                config["configurable"]["thread_id"] = request.session_id

            inputs = {"messages": [HumanMessage(content=request.message)]}

            if request.file_path:
                from .utils.file_utils import compute_sha256
                ext = os.path.splitext(request.file_path)[1].lower()

                new_media_id = compute_sha256(request.file_path)
                logger.info(f"New file media_id: {new_media_id[:16]}...")

                if ext in ['.wav', '.mp3', '.m4a', '.flac']:
                    logger.info(f"Injecting audio path: {request.file_path}")
                    inputs["audio_path"] = request.file_path
                    inputs["video_path"] = ""
                    inputs["media_id"] = new_media_id
                    inputs["vlm_processed"] = False
                elif ext in ['.mp4', '.mkv', '.mov', '.avi']:
                    logger.info(f"Injecting video path: {request.file_path}")
                    inputs["video_path"] = request.file_path
                    inputs["audio_path"] = ""
                    inputs["media_id"] = new_media_id
                    inputs["vlm_processed"] = False
                else:
                    logger.warning(f"Unsupported file type: {ext}")

            await orchestrator.graph.ainvoke(inputs, config=config)
        except Exception as e:
            logger.error(f"Error in generation: {e}")
        finally:
            await queue.put(None)

    async def stream_generator():
        task = asyncio.create_task(run_generation())
        while True:
            token = await queue.get()
            if token is None:
                break
            yield token
        await task

    return StreamingResponse(stream_generator(), media_type="text/plain")


# =============================================================================
# ConnectRPC Applications
# =============================================================================

def create_connect_apps():
    """
    Create ConnectRPC ASGI applications.
    Must be called after orchestrator is initialized.
    """
    if not orchestrator:
        raise RuntimeError("Orchestrator not initialized")

    chat_service = ObsidianChatService(orchestrator, session_manager)
    health_service = ObsidianHealthService()
    session_service = ObsidianSessionService(session_manager)
    history_service = ObsidianHistoryService(orchestrator)

    chat_app = ChatServiceASGIApplication(chat_service)
    health_app = HealthServiceASGIApplication(health_service)
    session_app = SessionServiceASGIApplication(session_service)
    history_app = HistoryServiceASGIApplication(history_service)

    return {
        chat_app.path: chat_app,
        health_app.path: health_app,
        session_app.path: session_app,
        history_app.path: history_app,
    }


class ConnectRPCMiddleware:
    """
    Middleware to route ConnectRPC requests to the appropriate service.
    """

    def __init__(self, app):
        self.app = app
        self._connect_apps: dict | None = None

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")

            # Initialize ConnectRPC apps lazily (after orchestrator is ready)
            if self._connect_apps is None and orchestrator is not None:
                try:
                    self._connect_apps = create_connect_apps()
                    logger.info(f"ConnectRPC apps mounted: {list(self._connect_apps.keys())}")
                except Exception as e:
                    logger.error(f"Failed to create ConnectRPC apps: {e}")
                    self._connect_apps = {}

            # Route to ConnectRPC if path matches, EXCEPT for OPTIONS requests (let CORS middleware handle those)
            if self._connect_apps and scope["method"] != "OPTIONS":
                for connect_path, connect_app in self._connect_apps.items():
                    if path.startswith(connect_path):
                        await connect_app(scope, receive, send)
                        return

        # Fall through to FastAPI
        await self.app(scope, receive, send)


# Wrap FastAPI with ConnectRPC middleware first
app = ConnectRPCMiddleware(app)

# Then wrap EVERYTHING with CORS middleware so it applies to ConnectRPC too
app = CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run():
    """Run the server."""
    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == '__main__':
    run()
