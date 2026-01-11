from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    LangGraph agent state

    Design Principle: Store references, not data.
    Transcription segments are stored in ChromaDB and accessed via media_id.
    """
    # 'add_messages' ensures new messages are appended, not overwritten
    messages: Annotated[List[BaseMessage], add_messages]

    # Media identifiers (temporary, for current processing)
    audio_path: Optional[str]
    video_path: Optional[str]

    # Media reference - used to query ChromaDB for segments
    media_id: Optional[str]

    # ASR metadata only - segments stored in ChromaDB
    audio_usability: Optional[Dict[str, Any]]

    # VLM Metadata
    processing_chunks: Optional[List[Dict[str, Any]]]  # Chunks pending VLM processing
    vlm_results: Optional[List[Dict[str, Any]]]        # VLM output per chunk
    vlm_processed: Optional[bool]                      # Flag indicating VLM stage complete

    # Intent routing
    intent: Optional[str]            # "SUMMARIZE", "QUESTION", "EXPORT_SRT", "UNCLEAR"
    prepared_context: Optional[str]  # Full transcript or RAG results
    tool_result: Optional[str]       # Output from tool execution
    llm_task: Optional[str]          # Task for ChatNode: "summarize", "answer", "present_result"

    # TODO: Legacy - to be removed
    rag_context: Optional[str]

