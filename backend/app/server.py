import asyncio
import logging
import grpc
from concurrent import futures
import sys
import os
import sqlite3
import sonora.asgi

# Add backend/app directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import service_pb2
import service_pb2_grpc
from orchestrator import AgentOrchestrator
import imageio_ffmpeg

# Force transformers to see our private ffmpeg
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ObsidianService(service_pb2_grpc.ObsidianServiceServicer):
    def __init__(self):
        self.orchestrator = AgentOrchestrator()

    async def UploadVideo(self, request, context):
        try:
            video_id = await self.orchestrator.upload_video(request.file_path)
            return service_pb2.UploadResponse(video_id=video_id, status="ready")
        except Exception as e:
            logger.error(f"Error in UploadVideo: {e}")
            return service_pb2.UploadResponse(video_id="", status=f"error: {str(e)}")

    async def Chat(self, request, context):
        try:
            async for content, type in self.orchestrator.chat(request.video_id, request.message):
                yield service_pb2.ChatResponse(content=content, type=type)
        except Exception as e:
            logger.error(f"Error in Chat: {e}")
            yield service_pb2.ChatResponse(content=f"Error: {str(e)}", type="error")

    async def GetHistory(self, request, context):
        try:
            # Fetch status to see if we should add a progress indicator
            with sqlite3.connect(self.orchestrator.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM videos WHERE id = ?", (request.video_id,))
                row = cursor.fetchone()
                status = row[0] if row else "unknown"

            messages = self.orchestrator.get_history(request.video_id)
            grpc_messages = []
            for msg in messages:
                grpc_messages.append(service_pb2.ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp", "")
                ))
            
            # Synthetic Progress Message
            if status.startswith("processing"):
                grpc_messages.append(service_pb2.ChatMessage(
                    role="assistant",
                    content=f"🔄 {status.title()}... (Please wait)",
                    timestamp=""
                ))

            return service_pb2.GetHistoryResponse(messages=grpc_messages)
        except Exception as e:
            logger.error(f"Error in GetHistory: {e}")
            return service_pb2.GetHistoryResponse(messages=[])

async def serve():
    pass # No-op for direct execution if imported

def get_application():
    from starlette.middleware.cors import CORSMiddleware
    # Create ASGI application
    # Disable internal CORS to avoid uvicorn header type issues
    app = sonora.asgi.grpcASGI(enable_cors=False)
    service_pb2_grpc.add_ObsidianServiceServicer_to_server(ObsidianService(), app)
    
    # Wrap with Starlette's robust CORS middleware
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting Sonora (gRPC-Web) Server with Uvicorn on port 8080...")
    uvicorn.run(get_application(), host="0.0.0.0", port=8080)

