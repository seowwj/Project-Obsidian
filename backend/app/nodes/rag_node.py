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
    Filters by media_id when available for scoped retrieval.
    """
    
    def __init__(self, collection_name: str = "asr_segments"):
        super().__init__(model=None, name="rag_node")
        self.vector_store = VectorStore(collection_name=collection_name)
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
        
        # Determine retrieval strategy
        if media_id:
            # Scoped search: only current media
            self.logger.info(f"Scoped RAG search for media_id: {media_id}")
            results = self.vector_store.search(
                query, 
                n_results=5, 
                where={"media_id": media_id}
            )
        else:
            # Global search: all indexed content
            self.logger.info("Global RAG search (no media_id filter)")
            results = self.vector_store.search(query, n_results=5)
        
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
