import logging
from typing import Dict, Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState

logger = logging.getLogger(__name__)

VALID_INTENTS = ["SUMMARIZE", "QUESTION", "EXPORT_SRT", "UNCLEAR"]


class IntentClassifierNode(BaseNode):
    """
    Classifies user intent into discrete categories.

    Uses a constrained LLM call to output a single intent category.
    This enables reliable routing without complex multi-task instructions.

    See architecture_intent_routing.md for design rationale.
    """

    def __init__(self, model):
        super().__init__(model=model, name="intent_classifier")
        self.logger = logger

    def _build_classification_prompt(self, query: str, has_media: bool) -> str:
        """Build the intent classification prompt."""
        media_context = "The user has uploaded a media file." if has_media else "No media file is currently loaded."

        return f"""Classify this user query into ONE category. Output ONLY the category name.

Categories:
- SUMMARIZE: User wants a summary, overview, or general understanding of the content
- QUESTION: User asks a specific question about the content
- EXPORT_SRT: User wants to export or download the transcript (SRT, subtitles, captions)
- UNCLEAR: The intent is ambiguous or doesn't fit other categories

Context: {media_context}

Query: "{query}"

Category:"""

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        self.logger.info(f"--- Node {self.name} processing ---")

        messages = state.get("messages", [])
        media_id = state.get("media_id")

        # Extract last human message
        query = ""
        for msg in reversed(messages):
            if msg.type == "human":
                query = msg.content
                break

        if not query:
            self.logger.warning("No user query found. Defaulting to UNCLEAR.")
            return {"intent": "UNCLEAR"}

        self.logger.info(f"Classifying intent for query: '{query[:100]}...'")

        # Build classification prompt
        prompt = self._build_classification_prompt(query, has_media=bool(media_id))

        # Call LLM with no streaming (short response)
        try:
            from langchain_core.messages import HumanMessage
            response = await self.model.generate([HumanMessage(content=prompt)], stream_callback=None)

            # Extract intent from response (should be a single word)
            intent = response.strip().upper()

            # Remove any extra text (LLM might add explanation)
            # Take first word if multiple
            intent = intent.split()[0] if intent else "UNCLEAR"

            # Validate intent
            if intent not in VALID_INTENTS:
                self.logger.warning(f"Invalid intent from LLM: '{intent}'. Defaulting to UNCLEAR.")
                intent = "UNCLEAR"

            self.logger.info(f"Classified intent: {intent}")

        except Exception as e:
            self.logger.error(f"Intent classification failed: {e}")
            intent = "UNCLEAR"

        return {"intent": intent}
