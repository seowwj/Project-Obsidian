import logging
import re
import json

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from typing import Dict, Any

from .base_node import BaseNode
from ..state import AgentState
from ..tools import audio_tools, basic_tools

logger = logging.getLogger(__name__)

class ToolNode(BaseNode):
    def __init__(self):
        super().__init__(model=None, name="tool_node")
    
    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        logger.info(f"--- Node {self.name} processing ---")
        
        messages = state['messages']
        last_message = messages[-1]
        content = last_message.content
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
             logger.warning("ToolNode called but no tool_calls found in message.")
             return {}
        
        # Helper to execute a single tool call
        # In a real ReAct loop, we might loop through all calls
        results = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            result_content = f"Error: Tool {tool_name} not found."
            
            try:
                if hasattr(audio_tools, tool_name):
                    tool_func = getattr(audio_tools, tool_name)
                    logger.info(f"Invoking tool {tool_name} from audio_tools with args: {tool_args}")
                    result_content = tool_func.invoke(tool_args)
                elif hasattr(basic_tools, tool_name):
                    tool_func = getattr(basic_tools, tool_name)
                    logger.info(f"Invoking tool {tool_name} from basic_tools with args: {tool_args}")
                    result_content = tool_func.invoke(tool_args)
                else:
                    logger.error(f"Tool {tool_name} not found in audio_tools or basic_tools.")
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                result_content = f"Error executing tool: {e}"
            
            results.append(ToolMessage(content=result_content, tool_call_id=tool_id, name=tool_name))
            
        return {"messages": results}
