import chromadb
import logging
import uuid

from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_directory="chroma_db"):
        """
        Initialize ChromaDB Persistent Client.
        Explicitly loads the embedding model to avoid timeouts during add().
        """
        logger.info(f"Initializing ChromaDB at {persist_directory}...")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Pre-load embedding function
        logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name="video_knowledge",
            embedding_function=self.ef
        )
        logger.info(f"ChromaDB initialized. Collection count: {self.collection.count()}")
    
    def add_texts(self, texts: list[str], metadatas: list[dict]):
        """
        Add text chunks to the vector store.
        """
        if not texts:
            return
            
        ids = [str(uuid.uuid4()) for _ in texts]
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} documents to Vector Store.")

    def search(self, query_text: str, n_results: int = 5, where: dict = None):
        """
        Semantic search with optional filtering.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        return results
