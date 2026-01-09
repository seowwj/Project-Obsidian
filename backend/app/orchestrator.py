import logging
from langgraph.graph import StateGraph, END

from .state import AgentState

from .llm import SLMWrapper
from .nodes.chat_node import ChatNode


logger = logging.getLogger(__name__)

from langgraph.checkpoint.memory import MemorySaver

class AgentOrchestrator:
    def __init__(self):
        logger.info("Initializing Agent Orchestrator...")
        
        self.graph = self.build_graph()
    
    def build_graph(self):
        """
        Builds the agent graph
        """
        # Instanstiate model
        chat_model = SLMWrapper()

        # Instantiate nodes
        chat_node = ChatNode(model=chat_model, name="chat_node")

        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("chatbot", chat_node)
        graph.set_entry_point("chatbot")
        graph.add_edge("chatbot", END)
        
        checkpointer = MemorySaver()

        return graph.compile(checkpointer=checkpointer)
