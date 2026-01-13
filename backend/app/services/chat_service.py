"""
ConnectRPC ChatService implementation.
Handles streaming chat responses from the LangGraph orchestrator.
"""

import asyncio
import logging
import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

# Ensure gen folder is in path
_backend_dir = Path(__file__).parent.parent.parent
_gen_dir = _backend_dir / "gen"
if str(_gen_dir) not in sys.path:
    sys.path.insert(0, str(_gen_dir))

from connectrpc.request import RequestContext

from obsidian.v1.obsidian_pb2 import ChatRequest, ChatResponse
from obsidian.v1.obsidian_connect import ChatService
from ..orchestrator import AgentOrchestrator
from ..utils.file_utils import compute_sha256
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class ObsidianChatService(ChatService):
    """
    ConnectRPC ChatService implementation.
    Streams AI responses token-by-token.
    """

    def __init__(self, orchestrator: AgentOrchestrator, session_manager=None):
        self.orchestrator = orchestrator
        self.session_manager = session_manager

    async def chat(
        self, request: ChatRequest, ctx: RequestContext
    ) -> AsyncIterator[ChatResponse]:
        """
        Send a message and receive streaming AI response.
        
        Args:
            request: ChatRequest with message, session_id, and optional file_path
            ctx: Request context
            
        Yields:
            ChatResponse with individual tokens
        """
        logger.info(f"Chat request: session={request.session_id}, message={request.message[:50]}...")
        
        queue: asyncio.Queue[str | None] = asyncio.Queue()

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
                file_path = request.file_path if request.HasField("file_path") else None
                if file_path:
                    ext = os.path.splitext(file_path)[1].lower()

                    # Compute new media_id from file hash
                    new_media_id = compute_sha256(file_path)
                    logger.info(f"New file media_id: {new_media_id[:16]}...")

                    if ext in ['.wav', '.mp3', '.m4a', '.flac']:
                        logger.info(f"Injecting audio path: {file_path}")
                        inputs["audio_path"] = file_path
                        inputs["video_path"] = ""
                        inputs["media_id"] = new_media_id
                        inputs["vlm_processed"] = False
                    elif ext in ['.mp4', '.mkv', '.mov', '.avi']:
                        logger.info(f"Injecting video path: {file_path}")
                        inputs["video_path"] = file_path
                        inputs["audio_path"] = ""
                        inputs["media_id"] = new_media_id
                        inputs["vlm_processed"] = False
                    else:
                        logger.warning(f"Unsupported file type: {ext}")

                if self.session_manager:
                    # Update session timestamp
                    await self.session_manager.update_timestamp(request.session_id)

                await self.orchestrator.graph.ainvoke(inputs, config=config)
            except Exception as e:
                logger.error(f"Error in generation: {e}")
            finally:
                await queue.put(None)  # Signal end of stream

        # Start generation in background
        task = asyncio.create_task(run_generation())

        # Yield tokens as they arrive
        while True:
            token = await queue.get()
            if token is None:
                break
            yield ChatResponse(token=token)

        await task
