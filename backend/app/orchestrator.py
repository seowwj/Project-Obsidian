import logging
from langgraph.graph import StateGraph, END

from .state import AgentState

from .llm import SLMWrapper
from .asr import ASRWrapper
from .nodes.chat_node import ChatNode
from .nodes.asr_node import ASRNode


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
        asr_model = ASRWrapper()

        # Instantiate nodes
        chat_node = ChatNode(model=chat_model, name="chat_node")
        asr_node = ASRNode(model=asr_model)

        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("chatbot", chat_node)
        graph.add_node("asr", asr_node)
        
        # Edges
        ## TEMP - FAST FAIL for ASR
        graph.add_edge("asr", END)
        # graph.add_edge("asr", "chatbot")
        graph.add_edge("chatbot", END)

        # Conditional Entry Point
        def route_input(state: AgentState):
            if state.get("audio_path"):
                return "asr"
            return "chatbot"

        graph.set_conditional_entry_point(
            route_input,
            {
                "asr": "asr",
                "chatbot": "chatbot"
            }
        )
        
        checkpointer = MemorySaver()

        return graph.compile(checkpointer=checkpointer)
