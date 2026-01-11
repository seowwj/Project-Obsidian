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

from .orchestrator import AgentOrchestrator

# Global orchestrator instance
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("Initializing Agent Orchestrator...")
    orchestrator = AgentOrchestrator()
    yield
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
                ext = os.path.splitext(request.file_path)[1].lower()
                if ext in ['.wav', '.mp3', '.m4a', '.flac']:
                    logger.info(f"Injecting audio path: {request.file_path}")
                    inputs["audio_path"] = request.file_path
                elif ext in ['.mp4', '.mkv', '.mov', '.avi']:
                    logger.info(f"Injecting video path: {request.file_path}")
                    inputs["video_path"] = request.file_path
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
