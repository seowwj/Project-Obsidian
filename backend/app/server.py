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

    async def CreateSession(self, request, context):
        try:
            session_id = self.orchestrator.create_session(request.video_id)
            # Retrieve the created session metadata to return
            # (In a real app, create_session might return the object, here we query it back or construct it)
            # Quick hack: construct it since we know the ID and title default
            title = "New Chat"
            if request.video_id:
                 # We'd need to fetch the title again or have orchestrator return it. 
                 # For now let's trust list_sessions will fix it on refresh.
                 pass
            
            # Better: make orchestrator.create_session return the full dict
            # or just return the ID and client re-fetches list.
            # Let's return a basic metadata object.
            return service_pb2.CreateSessionResponse(
                session=service_pb2.SessionMetadata(
                    id=session_id,
                    title="New Session", # Placeholder, frontend will typically list_sessions anyway
                    video_id=request.video_id,
                    created_at="" # Timestamp not critical for immediate response
                )
            )
        except Exception as e:
            logger.error(f"Error in CreateSession: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.CreateSessionResponse()

    async def ListSessions(self, request, context):
        try:
            sessions = self.orchestrator.list_sessions()
            grpc_sessions = []
            for s in sessions:
                grpc_sessions.append(service_pb2.SessionMetadata(
                    id=s["id"],
                    title=s["title"],
                    video_id=s["video_id"] or "",
                    created_at=s["created_at"]
                ))
            return service_pb2.ListSessionsResponse(sessions=grpc_sessions)
        except Exception as e:
            logger.error(f"Error in ListSessions: {e}")
            return service_pb2.ListSessionsResponse(sessions=[])

    async def DeleteSession(self, request, context):
        try:
            self.orchestrator.delete_session(request.session_id)
            return service_pb2.DeleteSessionResponse(success=True)
        except Exception as e:
            logger.error(f"Error in DeleteSession: {e}")
            return service_pb2.DeleteSessionResponse(success=False)

    async def RenameSession(self, request, context):
        try:
            self.orchestrator.rename_session(request.session_id, request.new_title)
            return service_pb2.RenameSessionResponse(success=True)
        except Exception as e:
            logger.error(f"Error in RenameSession: {e}")
            return service_pb2.RenameSessionResponse(success=False)

    async def Chat(self, request, context):
        try:
            async for content, type in self.orchestrator.chat(request.session_id, request.message):
                yield service_pb2.ChatResponse(content=content, type=type)
        except Exception as e:
            logger.error(f"Error in Chat: {e}")
            yield service_pb2.ChatResponse(content=f"Error: {str(e)}", type="error")

    async def GetHistory(self, request, context):
        try:
            # Check session status logic if needed (e.g. if video is processing)
            # For now, simplistic retrieval
            messages = self.orchestrator.get_history(request.session_id)
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
    pass # No-op for direct execution if imported

def get_application():
    from starlette.middleware.cors import CORSMiddleware
    # Create ASGI application
    # Disable internal CORS to avoid uvicorn header type issues
    app = sonora.asgi.grpcASGI(enable_cors=False)
    servicer = ObsidianService()
    
    # Manual Registration to ensure compatibility
    rpc_method_handlers = {
            'UploadVideo': grpc.unary_unary_rpc_method_handler(
                    servicer.UploadVideo,
                    request_deserializer=service_pb2.UploadRequest.FromString,
                    response_serializer=service_pb2.UploadResponse.SerializeToString,
            ),
            'CreateSession': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateSession,
                    request_deserializer=service_pb2.CreateSessionRequest.FromString,
                    response_serializer=service_pb2.CreateSessionResponse.SerializeToString,
            ),
            'Chat': grpc.unary_stream_rpc_method_handler(
                    servicer.Chat,
                    request_deserializer=service_pb2.ChatRequest.FromString,
                    response_serializer=service_pb2.ChatResponse.SerializeToString,
            ),
            'GetHistory': grpc.unary_unary_rpc_method_handler(
                    servicer.GetHistory,
                    request_deserializer=service_pb2.GetHistoryRequest.FromString,
                    response_serializer=service_pb2.GetHistoryResponse.SerializeToString,
            ),
            'ListSessions': grpc.unary_unary_rpc_method_handler(
                    servicer.ListSessions,
                    request_deserializer=service_pb2.ListSessionsRequest.FromString,
                    response_serializer=service_pb2.ListSessionsResponse.SerializeToString,
            ),
            'ListVideos': grpc.unary_unary_rpc_method_handler(
                    servicer.ListVideos,
                    request_deserializer=service_pb2.ListVideosRequest.FromString,
                    response_serializer=service_pb2.ListVideosResponse.SerializeToString,
            ),
            'DeleteSession': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteSession,
                    request_deserializer=service_pb2.DeleteSessionRequest.FromString,
                    response_serializer=service_pb2.DeleteSessionResponse.SerializeToString,
            ),
            'RenameSession': grpc.unary_unary_rpc_method_handler(
                    servicer.RenameSession,
                    request_deserializer=service_pb2.RenameSessionRequest.FromString,
                    response_serializer=service_pb2.RenameSessionResponse.SerializeToString,
            ),
    }
    
    # Try generic registration (Sonora explicitly supports this)
    generic_handler = grpc.method_handlers_generic_handler(
            'obsidian.ObsidianService', rpc_method_handlers)
    app.add_generic_rpc_handlers((generic_handler,))
    
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

