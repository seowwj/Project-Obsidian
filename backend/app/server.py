import asyncio
import logging
import grpc
from concurrent import futures
import sys
import os
from sonora.aio import SonoraWeb

# Add backend/app directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import service_pb2
import service_pb2_grpc
from orchestrator import AgentOrchestrator

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
            messages = self.orchestrator.get_history(request.video_id)
            grpc_messages = []
            for msg in messages:
                grpc_messages.append(service_pb2.ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp", "")
                ))
            return service_pb2.GetHistoryResponse(messages=grpc_messages)
        except Exception as e:
            logger.error(f"Error in GetHistory: {e}")
            return service_pb2.GetHistoryResponse(messages=[])

async def serve():
    # Use SonoraWeb to wrap the gRPC server for gRPC-Web support
    server = SonoraWeb(grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10)))
    service_pb2_grpc.add_ObsidianServiceServicer_to_server(ObsidianService(), server)
    
    # SonoraWeb needs to bind to a TCP port directly or be served behind a proxy.
    # Here we bind directly. Note: Sonora creates an HTTP/1.1 server that handles gRPC-Web.
    # We use a different port (8080) for gRPC-Web or we can just use the standard gRPC port if we purely use gRPC-Web.
    # For now, let's allow both if possible, but SonoraWeb wraps the whole thing.
    
    port = 8080
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"Sonora (gRPC-Web) Server starting on port {port}...")
    
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
