"""
ConnectRPC HistoryService implementation.
Retrieves chat history from LangGraph state.
"""

import logging
from typing import List

from connectrpc.request import RequestContext
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from obsidian.v1.obsidian_pb2 import (
    GetHistoryRequest, GetHistoryResponse,
    ChatMessage
)
from obsidian.v1.obsidian_connect import HistoryService
from ..orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

class ObsidianHistoryService(HistoryService):
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator

    async def get_history(self, request: GetHistoryRequest, ctx: RequestContext) -> GetHistoryResponse:
        """
        Retrieve chat history for a given session (thread_id).
        """
        thread_id = request.session_id
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Fetch state from LangGraph
            # aget_state returns a StateSnapshot object
            snapshot = await self.orchestrator.graph.aget_state(config)
            
            if not snapshot or not snapshot.values:
                # No history found
                return GetHistoryResponse(messages=[])
            
            state_messages: List[BaseMessage] = snapshot.values.get("messages", [])
            
            proto_messages = []
            for msg in state_messages:
                # Determine role
                role = "unknown"
                if isinstance(msg, HumanMessage):
                    role = "user"
                elif isinstance(msg, AIMessage):
                    role = "assistant"
                else:
                    # Skip system messages or other types for frontend display if desired,
                    # or map them to 'system'
                    continue
                
                # Generate a stable-ish ID if message id is missing, or use index?
                # LangChain messages usually have an ID if we persistent them, but maybe not always.
                msg_id = getattr(msg, "id", "") or str(id(msg))
                
                # Timestamp is not strictly tracked in BaseMessage unless added to metadata.
                # We'll default to 0 for now as 'unknown' or current time is misleading.
                # In a real app we'd check msg.additional_kwargs.get('timestamp')
                timestamp = int(msg.additional_kwargs.get("timestamp", 0))

                proto_messages.append(ChatMessage(
                    id=msg_id,
                    role=role,
                    content=str(msg.content),
                    timestamp=timestamp
                ))
            
            return GetHistoryResponse(messages=proto_messages)
            
        except Exception as e:
            logger.error(f"Error fetching history for {thread_id}: {e}")
            # return empty list on error
            return GetHistoryResponse(messages=[])
