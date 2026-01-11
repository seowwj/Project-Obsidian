import logging
from langgraph.graph import StateGraph, END

from .state import AgentState

from .llm import SLMWrapper
from .asr import ASRWrapper
from .vlm import VLMWrapper
from .nodes.chat_node import ChatNode
from .nodes.asr_node import ASRNode
from .nodes.intent_classifier_node import IntentClassifierNode
from .nodes.action_executor_node import ActionExecutorNode
from .nodes.chunking_node import ChunkingNode
from .nodes.vlm_node import VLMNode
from .nodes.fusion_node import FusionNode

logger = logging.getLogger(__name__)

from langgraph.checkpoint.memory import MemorySaver


class AgentOrchestrator:
    def __init__(self):
        """
        Initialize Agent Orchestrator.
        """
        logger.info("Initializing Agent Orchestrator...")

        self.graph = self.build_graph()

    def build_graph(self):
        """
        Builds the agent graph with intent-based routing and VLM support.

        Flow:
        - With video: Entry → ASR → Chunking → VLM → Fusion → IntentClassifier → ActionExecutor → [ChatNode or END]
        - With audio only: Entry → ASR → IntentClassifier → ActionExecutor → [ChatNode or END]
        - Without media: Entry → IntentClassifier → ActionExecutor → [ChatNode or END]

        VLM pipeline (Chunking → VLM → Fusion) runs once per video at ingestion time.
        """
        # Instantiate models
        chat_model = SLMWrapper()
        asr_model = ASRWrapper()
        vlm_model = VLMWrapper()

        # Instantiate nodes
        chat_node = ChatNode(model=chat_model, name="chat_node")
        asr_node = ASRNode(model=asr_model)
        intent_classifier = IntentClassifierNode(model=chat_model)
        action_executor = ActionExecutorNode()
        vlm_node = VLMNode(model=vlm_model)
        chunking_node = ChunkingNode()
        fusion_node = FusionNode()

        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("chatbot", chat_node)
        graph.add_node("asr", asr_node)
        graph.add_node("intent_classifier", intent_classifier)
        graph.add_node("action_executor", action_executor)
        graph.add_node("vlm", vlm_node)
        graph.add_node("chunking", chunking_node)
        graph.add_node("fusion", fusion_node)

        # Conditional routing after ASR
        def route_after_asr(state: AgentState):
            """
            Route based on media type after ASR completes.

            - If video_path present, VLM enabled, and not already processed: go to chunking pipeline
            - Otherwise: go directly to intent classifier
            """
            if state.get("video_path"):
                # Skip VLM if already processed for this video
                if state.get("vlm_processed"):
                    logger.info("VLM already processed, skipping to intent classifier")
                    return "intent_classifier"
                logger.info("Video detected, routing to VLM pipeline")
                return "chunking"
            return "intent_classifier"

        # ASR → [Chunking or IntentClassifier]
        graph.add_conditional_edges(
            "asr",
            route_after_asr,
            {
                "chunking": "chunking",
                "intent_classifier": "intent_classifier"
            }
        )

        # VLM pipeline: Chunking → VLM → Fusion → IntentClassifier
        graph.add_edge("chunking", "vlm")
        graph.add_edge("vlm", "fusion")
        graph.add_edge("fusion", "intent_classifier")

        # IntentClassifier → ActionExecutor
        graph.add_edge("intent_classifier", "action_executor")

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

        # Conditional Entry Point: audio/video → ASR, else → IntentClassifier
        def route_input(state: AgentState):
            # If audio or video path provided, always route to ASR
            # ASR and ChunkingNode handle caching via ChromaDB lookup
            if state.get("audio_path") or state.get("video_path"):
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
