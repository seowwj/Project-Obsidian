import logging
from typing import Dict, Any

from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState
from ..vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGNode(BaseNode):
    """
    Retrieval-Augmented Generation node.

    Fetches relevant context from ChromaDB based on the user's query.
    Queries multimodal_chunks (audio+visual) first, falls back to asr_segments.
    Filters by media_id when available for scoped retrieval.
    """

    def __init__(self):
        super().__init__(model=None, name="rag_node")
        # Priority: multimodal (audio+visual) > asr-only
        self.multimodal_store = VectorStore(collection_name="multimodal_chunks")
        self.asr_store = VectorStore(collection_name="asr_segments")
        self.logger = logger

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        self.logger.info(f"--- Node {self.name} processing ---")

        messages = state.get("messages", [])
        media_id = state.get("media_id")

        # Extract last human message for RAG query
        query = ""
        for msg in reversed(messages):
            if msg.type == "human":
                query = msg.content
                break

        if not query:
            self.logger.info("No query found in messages. Skipping RAG.")
            return {"rag_context": ""}

        self.logger.info(f"RAG query: '{query[:100]}...' (media_id: {media_id})")

        # Try multimodal chunks first (has audio+visual descriptions)
        results = self._search_collection(
            self.multimodal_store,
            query,
            media_id,
            collection_name="multimodal_chunks"
        )

        # Fall back to ASR segments if no multimodal results
        if not results or not results.get("documents") or not results["documents"][0]:
            self.logger.info("No multimodal chunks found, falling back to ASR segments")
            results = self._search_collection(
                self.asr_store,
                query,
                media_id,
                collection_name="asr_segments"
            )

        # Format context
        rag_context = ""
        if results and results.get("documents"):
            docs = results["documents"][0]  # ChromaDB returns list of lists
            if docs:
                rag_context = "Relevant context from indexed content:\n" + "\n".join([f"- {d}" for d in docs])
                self.logger.info(f"RAG found {len(docs)} relevant chunks")
            else:
                self.logger.info("RAG search returned no documents")
        else:
            self.logger.info("RAG search returned empty results")

        return {"rag_context": rag_context}

    def _search_collection(
        self,
        store: VectorStore,
        query: str,
        media_id: str = None,
        collection_name: str = ""
    ) -> Dict[str, Any]:
        """Search a specific collection with optional media_id filter."""
        if media_id:
            self.logger.debug(f"Scoped search in {collection_name} for media_id: {media_id[:16]}...")
            return store.search(query, n_results=5, where={"media_id": media_id})
        else:
            self.logger.debug(f"Global search in {collection_name}")
            return store.search(query, n_results=5)

