from typing import Annotated, TypedDict, List, Dict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # 'add_messages' ensures new messages are appended, not overwritten
    messages: Annotated[List[BaseMessage], add_messages]
    audio_path: str
    media_id: str
    transcription_segments: List[Dict]
    