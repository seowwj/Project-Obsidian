from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState

import logging

# Task-specific system prompts
TASK_PROMPTS = {
    "summarize": """You are a helpful AI assistant called Obsidian.
Your task is to SUMMARIZE the transcript provided below.
Provide a clear, comprehensive summary covering the main points.
Do not ask for more information - use what is provided.""",

    "answer": """You are a helpful AI assistant called Obsidian.
Your task is to ANSWER the user's question using the context provided below.
If the context doesn't contain the answer, say so honestly.
Do not make up information not present in the context.""",

    "present_result": """You are a helpful AI assistant called Obsidian.
The user requested an export. Present the result below in a readable format.
You may add a brief introduction like "Here's your SRT transcript:" but keep it minimal.""",

    "chat": """You are a helpful AI assistant called Obsidian.
Engage in friendly conversation with the user. Be helpful, concise, and personable.
You can help with general questions, greetings, and casual conversation.""",

    "general": """You are a helpful AI assistant called Obsidian.
Answer the user's question to the best of your ability.""",
}


class ChatNode(BaseNode):
    """
    ChatNode for intent-based routing.
    Receives prepared context and llm_task from ActionExecutorNode.
    """

    def __init__(self, model, name="chat_node"):
        super().__init__(model=model, name=name)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        self.logger.info(f"--- Node {self.name} processing ---")

        messages = state.get("messages", [])

        # Get intent routing data from ActionExecutor
        llm_task = state.get("llm_task", "general")
        prepared_context = state.get("prepared_context")
        tool_result = state.get("tool_result")

        self.logger.info(f"LLM task: {llm_task}")
        self.logger.info(f"Prepared context: {len(prepared_context) if prepared_context else 0} chars")
        self.logger.info(f"Tool result: {len(tool_result) if tool_result else 0} chars")

        # Build system prompt based on task
        system_prompt = TASK_PROMPTS.get(llm_task, TASK_PROMPTS["general"])

        # Add context to system prompt
        if prepared_context:
            system_prompt += f"\n\n--- CONTEXT ---\n{prepared_context}\n--- END CONTEXT ---"

        if tool_result:
            system_prompt += f"\n\n--- TOOL OUTPUT ---\n{tool_result}\n--- END TOOL OUTPUT ---"

        # Build message list
        model_messages = [SystemMessage(content=system_prompt)]

        # For summarize and present_result, only use the last message to avoid
        # context pollution from previous conversations about different files
        if llm_task in ["summarize", "present_result"]:
            # Only include the last user message
            last_human_msg = None
            for msg in reversed(messages):
                if msg.type == "human":
                    last_human_msg = msg
                    break
            if last_human_msg:
                model_messages.append(last_human_msg)
        else:
            # For answer/general tasks, include full history for context
            model_messages.extend(messages)

        self.logger.info(f"LLM input messages: {len(model_messages)}")

        # Get streaming callback if available
        stream_callback = None
        if config and "configurable" in config:
            stream_callback = config["configurable"].get("stream_callback")

        # Generate response
        response_text = await self.model.generate(model_messages, stream_callback=stream_callback)

        message = AIMessage(content=response_text)

        self.logger.info(f"LLM output: {response_text[:200]}...")
        return {"messages": [message]}
