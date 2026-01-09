from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState

import logging

logger = logging.getLogger(__name__)

class ChatNode(BaseNode):
    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        logger.info(f"--- Node {self.name} processing ---")
        
        messages = state['messages']
        
        stream_callback = None
        if config and "configurable" in config:
             stream_callback = config["configurable"].get("stream_callback")
        
        # TODO: Tool detection logic goes here
        
        response_text = await self.model.generate(messages, stream_callback=stream_callback)
        
        return {"messages": [AIMessage(content=response_text)]}
