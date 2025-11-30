# services/rag/chroma_rag.py
"""
ChromaDB RAG Provider
Local vector database support for development and small deployments
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .base_rag import BaseRAGProvider, Document, SearchResult, DocumentType

# Optional import - ChromaDB support
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None


class ChromaRAGProvider(BaseRAGProvider):
    """ChromaDB RAG provider for local vector storage"""
    
    def __init__(self, config: Dict[str, Any]):
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb is required. Install with: pip install chromadb")
        
        super().__init__(config)
        self.persist_directory = config.get('persist_directory', './chroma_data')
        self._embedding_dimension = config.get('embedding_dimension', 384)
        self._client = None
        self._collection = None
    
    @property
    def provider_name(self) -> str:
        return "chromadb"
    
    @property
    def embedding_dimension(self) -> int:
        return self._embedding_dimension
    
    async def initialize(self) -> bool:
        """Initialize ChromaDB client and collection"""
        try:
            # Create ChromaDB client with persistence
            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self._initialized = True
            return True
        except Exception as e:
            self._initialized = False
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
    
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to ChromaDB"""
        if not self._collection:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            ids = []
            contents = []
            metadatas = []
            
            for doc in documents:
                ids.append(doc.id)
                contents.append(doc.content)
                metadata = doc.metadata.copy()
                metadata['doc_type'] = doc.doc_type
                metadata['created_at'] = doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat()
                metadatas.append(metadata)
            
            self._collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to add documents: {e}")
    
    async def query(self, query: str, top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Query ChromaDB for similar documents"""
        if not self._collection:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            where_filter = filters if filters else None
            
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )
            
            search_results = []
            
            if results and results['documents']:
                for i, (doc_id, content, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (ChromaDB returns distances)
                    score = 1.0 - distance if distance <= 1.0 else 0.0
                    
                    document = Document(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                        doc_type=DocumentType(metadata.get('doc_type', 'text')),
                        created_at=datetime.fromisoformat(metadata.get('created_at')) if metadata.get('created_at') else None
                    )
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=score
                    ))
            
            return search_results
        except Exception as e:
            raise RuntimeError(f"Query failed: {e}")
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from ChromaDB"""
        if not self._collection:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            self._collection.delete(ids=doc_ids)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete documents: {e}")
    
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """Update document in ChromaDB"""
        if not self._collection:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            metadata = document.metadata.copy()
            metadata['doc_type'] = document.doc_type
            metadata['updated_at'] = datetime.now().isoformat()
            
            self._collection.update(
                ids=[doc_id],
                documents=[document.content],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to update document: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        if not self._collection:
            return {"error": "Not initialized"}
        
        try:
            count = self._collection.count()
            return {
                "provider": self.provider_name,
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_dimension": self._embedding_dimension
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        if not self._client:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to clear collection: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ChromaDB health"""
        if not self._collection:
            return {"status": "not_initialized"}
        
        try:
            count = self._collection.count()
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "document_count": count,
                "collection": self.collection_name
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def persist(self):
        """Persist ChromaDB data to disk"""
        if self._client:
            self._client.persist()


__all__ = ['ChromaRAGProvider']
