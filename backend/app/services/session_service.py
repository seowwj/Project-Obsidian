"""
ConnectRPC SessionService implementation.
Delegates to SessionManager.
"""

from typing import cast
import logging

from connectrpc.request import RequestContext

from obsidian.v1.obsidian_pb2 import (
    ListSessionsRequest, ListSessionsResponse,
    CreateSessionRequest, CreateSessionResponse,
    DeleteSessionRequest, DeleteSessionResponse,
    RenameSessionRequest, RenameSessionResponse,
    Session as ProtoSession
)
from obsidian.v1.obsidian_connect import SessionService
from .session_manager import SessionManager

logger = logging.getLogger(__name__)

class ObsidianSessionService(SessionService):
    def __init__(self, session_manager: SessionManager):
        self.manager = session_manager

    async def list_sessions(self, request: ListSessionsRequest, ctx: RequestContext) -> ListSessionsResponse:
        sessions = await self.manager.list_sessions()
        proto_sessions = [
            ProtoSession(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at
            ) for s in sessions
        ]
        return ListSessionsResponse(sessions=proto_sessions)

    async def create_session(self, request: CreateSessionRequest, ctx: RequestContext) -> CreateSessionResponse:
        import uuid
        session_id = str(uuid.uuid4())
        title = request.title if request.title else "New Chat"
        
        session = await self.manager.create_session(session_id, title)
        
        return CreateSessionResponse(
            session=ProtoSession(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
        )

    async def delete_session(self, request: DeleteSessionRequest, ctx: RequestContext) -> DeleteSessionResponse:
        await self.manager.delete_session(request.session_id)
        return DeleteSessionResponse()

    async def rename_session(self, request: RenameSessionRequest, ctx: RequestContext) -> RenameSessionResponse:
        session = await self.manager.rename_session(request.session_id, request.new_title)
        if not session:
            # ConnectRPC will translate typical exceptions, but here we just return empty if not found
            # Ideally should raise Code.NOT_FOUND
            raise ValueError("Session not found")
            
        return RenameSessionResponse(
            session=ProtoSession(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
        )
