import logging
from typing import Dict, Any, Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState
from ..vector_store import VectorStore
from ..tools import audio_tools

# Intent configuration - defines actions for each intent
INTENT_CONFIG = {
    "SUMMARIZE": {
        "context_source": "full_transcript",
        "llm_task": "summarize",
        "output_tool": None,
        "requires_media": True,
    },
    "QUESTION": {
        "context_source": "rag",
        "llm_task": "answer",
        "output_tool": None,
        "requires_media": False,
    },
    "EXPORT_SRT": {
        "context_source": None,
        "llm_task": "present_result",
        "output_tool": "export_transcript_srt",
        "requires_media": True,
    },
    "UNCLEAR": {
        "context_source": None,
        "llm_task": None,
        "output_tool": None,
        "clarification": True,
    },
    "CHAT": {
        "context_source": None,  # No media context needed
        "llm_task": "chat",
        "output_tool": None,
        "requires_media": False,
    },
}


class ActionExecutorNode(BaseNode):
    """
    Executes actions based on classified intent.

    Responsibilities:
    - Fetch appropriate context (full transcript, RAG, etc.)
    - Execute output tools if needed (SRT export, etc.)
    - Handle errors gracefully with user-friendly messages

    See architecture_intent_routing.md for design rationale.
    """

    def __init__(self):
        super().__init__(model=None, name="action_executor")
        # Priority: multimodal (audio+visual) > asr-only
        self.multimodal_store = VectorStore(collection_name="multimodal_chunks")
        self.asr_store = VectorStore(collection_name="asr_segments")
        self.logger = logging.getLogger(self.__class__.__name__)

    def _fetch_full_transcript(self, media_id: str) -> Optional[str]:
        """
        Fetch complete transcript from ChromaDB.
        """
        # Try multimodal chunks first (audio + visual descriptions)
        results = self.multimodal_store.get_by_metadata(where={"media_id": media_id})

        if results and results.get("ids"):
            self.logger.info(f"Using multimodal chunks for transcript ({len(results['ids'])} chunks)")
        else:
            # Fall back to ASR-only segments
            self.logger.info("No multimodal chunks found, falling back to ASR segments")
            results = self.asr_store.get_by_metadata(where={"media_id": media_id})

        if not results or not results.get("ids"):
            return None

        # Reconstruct and sort by time
        segments = []
        for i, meta in enumerate(results["metadatas"]):
            segments.append({
                "start": meta.get("start", 0),
                "text": results["documents"][i]
            })

        segments.sort(key=lambda x: x["start"])

        return " ".join([seg["text"] for seg in segments])

    def _fetch_rag_context(self, query: str, media_id: Optional[str] = None) -> str:
        """Fetch relevant chunks via semantic search (multimodal first)"""
        where_filter = {"media_id": media_id} if media_id else None

        # Try multimodal first
        results = self.multimodal_store.search(query, n_results=5, where=where_filter)

        if not results or not results.get("documents") or not results["documents"][0]:
            # Fall back to ASR
            results = self.asr_store.search(query, n_results=5, where=where_filter)

        if results and results.get("documents"):
            docs = results["documents"][0]
            if docs:
                return "Relevant context:\n" + "\n".join([f"- {d}" for d in docs])

        return ""

    def _execute_tool(self, tool_name: str, media_id: str) -> str:
        """Execute a tool and return result."""
        if tool_name == "export_transcript_srt":
            return audio_tools.export_transcript_srt.invoke({"media_id": media_id})
        elif tool_name == "get_whole_transcript":
            return audio_tools.get_whole_transcript.invoke({"media_id": media_id})
        else:
            return f"Error: Unknown tool '{tool_name}'"

    def _get_clarification_message(self) -> str:
        """Return clarification prompt for UNCLEAR intent."""
        return (
            "I'm not sure what you'd like me to do. Did you mean:\n"
            "1. **Summarize** the audio/video content?\n"
            "2. **Ask a question** about specific content?\n"
            "3. **Export** the transcript (SRT format)?\n\n"
            "Please let me know which option you prefer."
        )

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        self.logger.info(f"--- Node {self.name} processing ---")

        intent = state.get("intent", "UNCLEAR")
        media_id = state.get("media_id")

        self.logger.info(f"Executing actions for intent: {intent}")
        self.logger.info(f"Using media_id: {media_id[:16] if media_id else 'None'}...")

        # Get streaming callback for early returns
        stream_callback = None
        if config and "configurable" in config:
            stream_callback = config["configurable"].get("stream_callback")

        # Get config for this intent
        intent_config = INTENT_CONFIG.get(intent, INTENT_CONFIG["UNCLEAR"])

        # Handle UNCLEAR intent - short circuit with clarification
        if intent_config.get("clarification"):
            self.logger.info("Intent unclear, returning clarification message")
            message = self._get_clarification_message()
            # Stream the message so client sees it
            if stream_callback:
                await stream_callback(message)
            return {
                "prepared_context": None,
                "tool_result": None,
                "messages": [AIMessage(content=message)]
            }

        # Validate media requirement
        if intent_config.get("requires_media") and not media_id:
            self.logger.warning("Media required but not present")
            message = "Please upload a media file first."
            if stream_callback:
                await stream_callback(message)
            return {
                "prepared_context": None,
                "tool_result": None,
                "messages": [AIMessage(content=message)]
            }

        # Fetch context based on intent
        prepared_context = None
        context_source = intent_config.get("context_source")

        if context_source == "full_transcript":
            self.logger.info("Fetching full transcript...")
            prepared_context = self._fetch_full_transcript(media_id)
            if not prepared_context:
                message = "I don't have a transcript for this file. Was it processed correctly?"
                if stream_callback:
                    await stream_callback(message)
                return {
                    "prepared_context": None,
                    "tool_result": None,
                    "messages": [AIMessage(content=message)]
                }
            self.logger.info(f"Fetched transcript: {len(prepared_context)} chars")

        elif context_source == "rag":
            # Extract query from last human message
            query = ""
            for msg in reversed(state.get("messages", [])):
                if msg.type == "human":
                    query = msg.content
                    break

            self.logger.info(f"Running RAG search for: '{query[:50]}...'")
            prepared_context = self._fetch_rag_context(query, media_id)
            self.logger.info(f"RAG context: {len(prepared_context)} chars")

        # Execute output tool if needed
        tool_result = None
        output_tool = intent_config.get("output_tool")

        if output_tool:
            self.logger.info(f"Executing tool: {output_tool}")
            try:
                tool_result = self._execute_tool(output_tool, media_id)
                self.logger.info(f"Tool result: {len(tool_result)} chars")
            except Exception as e:
                self.logger.error(f"Tool execution failed: {e}")
                message = "Sorry, the operation failed. Please try again."
                if stream_callback:
                    await stream_callback(message)
                return {
                    "prepared_context": None,
                    "tool_result": None,
                    "messages": [AIMessage(content=message)]
                }

        return {
            "prepared_context": prepared_context,
            "tool_result": tool_result,
            "llm_task": intent_config.get("llm_task"),
        }
