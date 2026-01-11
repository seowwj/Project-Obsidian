import logging
from langgraph.graph import StateGraph, END

from .state import AgentState

from .llm import SLMWrapper
from .asr import ASRWrapper
from .nodes.chat_node import ChatNode
from .nodes.asr_node import ASRNode
from .nodes.intent_classifier_node import IntentClassifierNode
from .nodes.action_executor_node import ActionExecutorNode

logger = logging.getLogger(__name__)

from langgraph.checkpoint.memory import MemorySaver


class AgentOrchestrator:
    def __init__(self):
        logger.info("Initializing Agent Orchestrator...")
        
        self.graph = self.build_graph()
    
    def build_graph(self):
        """
        Builds the agent graph with intent-based routing.
        
        Flow:
        - With audio: Entry → ASR → IntentClassifier → ActionExecutor → [ChatNode or END]
        - Without audio: Entry → IntentClassifier → ActionExecutor → [ChatNode or END]
        
        ActionExecutor handles:
        - Fetching context (full transcript, RAG)
        - Executing tools (SRT export)
        - Returning clarification for UNCLEAR intent
        """
        # Instantiate models
        chat_model = SLMWrapper()
        asr_model = ASRWrapper()

        # Instantiate nodes
        chat_node = ChatNode(model=chat_model, name="chat_node")
        asr_node = ASRNode(model=asr_model)
        intent_classifier = IntentClassifierNode(model=chat_model)
        action_executor = ActionExecutorNode()

        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("chatbot", chat_node)
        graph.add_node("asr", asr_node)
        graph.add_node("intent_classifier", intent_classifier)
        graph.add_node("action_executor", action_executor)
        
        # Edges
        graph.add_edge("asr", "intent_classifier")              # ASR → IntentClassifier
        graph.add_edge("intent_classifier", "action_executor")  # IntentClassifier → ActionExecutor
        
        # Conditional Edge: ActionExecutor → ChatNode or END
        def route_after_action(state: AgentState):
            """
            Route based on ActionExecutor output.
            
            - If ActionExecutor returned a message (clarification, error), go to END
            - If ActionExecutor prepared context/tool_result, go to ChatNode
            """
            messages = state.get("messages", [])
            
            # Check if ActionExecutor already added a response message
            # (happens for UNCLEAR intent or errors)
            if messages and messages[-1].type == "ai":
                # Already have a response, skip ChatNode
                logger.info("ActionExecutor provided response, skipping ChatNode")
                return END
            
            # Otherwise, proceed to ChatNode for generation
            return "chatbot"
        
        graph.add_conditional_edges(
            "action_executor",
            route_after_action,
            {
                "chatbot": "chatbot",
                END: END
            }
        )

        graph.add_edge("chatbot", END)

        # Conditional Entry Point: audio → ASR, else → IntentClassifier
        def route_input(state: AgentState):
            if state.get("audio_path"):
                return "asr"
            return "intent_classifier"

        graph.set_conditional_entry_point(
            route_input,
            {
                "asr": "asr",
                "intent_classifier": "intent_classifier"
            }
        )
        
        checkpointer = MemorySaver()

        return graph.compile(checkpointer=checkpointer)
