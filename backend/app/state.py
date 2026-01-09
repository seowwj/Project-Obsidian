from typing import Annotated, TypedDict, List
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # 'add_messages' ensures new messages are appended, not overwritten
    messages: Annotated[List[BaseMessage], add_messages]
    