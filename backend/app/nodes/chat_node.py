from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
import re
import uuid

from .base_node import BaseNode
from ..state import AgentState
from ..vector_store import VectorStore

import logging

logger = logging.getLogger(__name__)

class ChatNode(BaseNode):
    def __init__(self, model, name="chat_node"):
        super().__init__(model=model, name=name)
        # Initialize Vector Store for RAG
        self.vector_store = VectorStore(collection_name="asr_segments")

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        logger.info(f"--- Node {self.name} processing ---")
        logger.debug(f"Input messages: {state['messages']}")
        
        messages = state['messages']
        last_human_message = ""
        
        # Simple extraction of last user query for RAG
        # Walk backwards to find last human message
        for msg in reversed(messages):
            if msg.type == "human":
                last_human_message = msg.content
                break
        
        model_messages = []
        
        # 1. RAG Retrieval
        rag_context = ""
        if last_human_message:
            results = self.vector_store.search(last_human_message, n_results=3)
            if results and results['documents']:
                docs = results['documents'][0] # List of lists
                if docs:
                    rag_context = "Context from analyzed files (RAG):\n" + "\n".join([f"- {d}" for d in docs])
        
        # 2. System Prompt Construction
        # Check if the last message was a ToolMessage (meaning we just executed a tool)
        last_message_was_tool = len(messages) > 0 and messages[-1].type == 'tool'
        
        if last_message_was_tool:
            # Mode: Reporting / Summarizing Code
            system_instructions = (
                "You are a helpful AI assistant called Obsidian.\n"
                "You have just received the output of a requested tool.\n"
                "Use the content of the ToolMessage to answer the user's question.\n"
                "IMPORTANT: DO NOT call the tool again. Just present the result to the user."
            )
        else:
            # Mode: General Chat / Planning
            system_instructions = (
                "You are a helpful AI assistant called Obsidian.\n"
                "You have access to tools to read file contents.\n"
                "You may also have some 'Context from analyzed files (RAG)' above. Use it if sufficient.\n"
                "If RAG is insufficient (e.g. for full summarization) and you need the WHOLE file, output exactly: [[TOOL: get_whole_transcript]]\n"
                "If the user asks to export the transcript, output exactly: [[TOOL: export_transcript_srt]]\n"
                "CRITICAL: Output ONLY ONE tool tag. Do NOT output any other text with it.\n"
                "Do NOT support multiple tool calls in one response.\n"
            )
        
        if rag_context:
            system_instructions += f"\n{rag_context}\n"
            
        model_messages.append(SystemMessage(content=system_instructions))
        
        # 3. Add History
        model_messages.extend(messages)
        
        stream_callback = None
        if config and "configurable" in config:
             stream_callback = config["configurable"].get("stream_callback")
        
        response_text = await self.model.generate(model_messages, stream_callback=stream_callback)
        
        # Post-process response for tool calls
        # Regex to capture tool name without arguments for now
        tool_regex = r"\[\[TOOL:\s*(\w+)\]\]"
        
        # Use search to find the first tool call
        match = re.search(tool_regex, response_text)

        if match:
            tool_name = match.group(1)
            
            # Create structured tool call
            # We assume the tool only needs media_id from state
            media_id = state.get("media_id")
            tool_args = {"media_id": media_id} if media_id else {}
            
            # Create AIMessage with the original text (visible tag) AND tool_calls
            message = AIMessage(
                content=response_text,
                tool_calls=[{
                    "name": tool_name,
                    "args": tool_args,
                    "id": str(uuid.uuid4())
                }]
            )
        else:
            message = AIMessage(content=response_text)
        
        logger.debug(f"LLM output: {message}")
        return {"messages": [message]}
