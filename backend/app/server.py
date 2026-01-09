import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from fastapi.responses import StreamingResponse
import asyncio

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
            
            await orchestrator.graph.ainvoke(
                {"messages": [HumanMessage(content=request.message)]},
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
