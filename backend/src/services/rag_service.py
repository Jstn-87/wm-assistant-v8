"""
RAG (Retrieval-Augmented Generation) service for WM Assistant.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer
from ..models.support_entry import SupportEntry
from ..models.assistant_response import AssistantResponse
from ..config import get_settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation using ChromaDB and sentence transformers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the RAG service with embedding model and vector database."""
        try:
            logger.info("Initializing RAG service...")
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.settings.embedding_model}")
            self.embedding_model = SentenceTransformer(self.settings.embedding_model)
            
            # Initialize ChromaDB
            logger.info(f"Initializing ChromaDB at: {self.settings.vector_db_persist_dir}")
            self.chroma_client = chromadb.PersistentClient(path=self.settings.vector_db_persist_dir)
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="wm_support_entries",
                metadata={"description": "WM support database entries"}
            )
            
            self._initialized = True
            logger.info("RAG service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if the RAG service is initialized."""
        return self._initialized
    
    def add_support_entries(self, entries: List[SupportEntry]) -> bool:
        """Add support entries to the vector database."""
        if not self._initialized:
            logger.error("RAG service not initialized")
            return False
        
        try:
            logger.info(f"Adding {len(entries)} support entries to vector database")
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            embeddings = []
            
            for entry in entries:
                # Create document text for embedding
                doc_text = f"{entry.title} {entry.content} {' '.join(entry.keywords)}"
                
                # Generate embedding
                embedding = self.embedding_model.encode(doc_text).tolist()
                
                ids.append(entry.id)
                documents.append(doc_text)
                metadatas.append({
                    "title": entry.title,
                    "category": entry.category,
                    "url": entry.url or "",
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat()
                })
                embeddings.append(embedding)
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"Successfully added {len(entries)} entries to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add support entries to vector database: {e}")
            return False
    
    def search_similar_entries(self, query: str, limit: int = 5) -> List[Tuple[SupportEntry, float]]:
        """Search for similar support entries using semantic similarity."""
        if not self._initialized:
            logger.error("RAG service not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert results to SupportEntry objects
            similar_entries = []
            
            if results["ids"] and results["ids"][0]:
                for i, entry_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to similarity score (0-1, higher is better)
                    similarity_score = 1.0 - distance
                    
                    # Create SupportEntry object
                    entry = SupportEntry(
                        id=entry_id,
                        title=metadata["title"],
                        category=metadata["category"],
                        keywords=[],  # Will be populated from original data
                        content=results["documents"][0][i],
                        url=metadata["url"] if metadata["url"] else None,
                        created_at=datetime.fromisoformat(metadata["created_at"]),
                        updated_at=datetime.fromisoformat(metadata["updated_at"])
                    )
                    
                    similar_entries.append((entry, similarity_score))
            
            logger.info(f"Found {len(similar_entries)} similar entries for query: {query[:50]}...")
            return similar_entries
            
        except Exception as e:
            logger.error(f"Failed to search similar entries: {e}")
            return []
    
    def clear_database(self) -> bool:
        """Clear all entries from the vector database."""
        if not self._initialized:
            logger.error("RAG service not initialized")
            return False
        
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection("wm_support_entries")
            self.collection = self.chroma_client.create_collection(
                name="wm_support_entries",
                metadata={"description": "WM support database entries"}
            )
            
            logger.info("Vector database cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear vector database: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        if not self._initialized:
            return {"error": "RAG service not initialized"}
        
        try:
            count = self.collection.count()
            return {
                "total_entries": count,
                "embedding_model": self.settings.embedding_model,
                "collection_name": "wm_support_entries",
                "initialized": self._initialized
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def generate_context_for_query(self, query: str, max_entries: int = 3) -> str:
        """Generate context string from similar entries for use in LLM prompts."""
        similar_entries = self.search_similar_entries(query, limit=max_entries)
        
        if not similar_entries:
            return ""
        
        context_parts = []
        for entry, score in similar_entries:
            context_parts.append(f"Title: {entry.title}\nContent: {entry.content}")
            if entry.url:
                context_parts.append(f"URL: {entry.url}")
            context_parts.append(f"Relevance Score: {score:.2f}\n")
        
        return "\n".join(context_parts)
    
    def get_entry_sources(self, query: str, max_entries: int = 3) -> List[str]:
        """Get source entry IDs for a query."""
        similar_entries = self.search_similar_entries(query, limit=max_entries)
        return [entry.id for entry, _ in similar_entries]
    
    def get_entry_urls(self, query: str, max_entries: int = 3) -> List[str]:
        """Get URLs from similar entries for a query."""
        similar_entries = self.search_similar_entries(query, limit=max_entries)
        urls = []
        for entry, _ in similar_entries:
            if entry.url:
                urls.append(entry.url)
        return urls
