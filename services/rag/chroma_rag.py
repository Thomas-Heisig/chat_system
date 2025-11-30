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
            if chromadb is None:
                raise ImportError("chromadb is not installed or failed to import.")
            # Create ChromaDB client with persistence (new API)
            self._client = chromadb.PersistentClient(
                path=self.persist_directory
            )
            
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
            
            if (
                results
                and results.get('documents')
                and results.get('ids')
                and results.get('metadatas') is not None
                and results.get('distances') is not None
            ):
                docs = results.get('documents')
                ids = results.get('ids')
                metadatas = results.get('metadatas')
                distances = results.get('distances')
                if docs is None or ids is None or metadatas is None or distances is None:
                    return search_results

                for doc_id, content, metadata, distance in zip(
                    ids[0],
                    docs[0],
                    metadatas[0],
                    distances[0]
                ):
                    # Convert distance to similarity score
                    # For cosine distance (0-2 range): similarity = 1 - (distance / 2)
                    # For L2 distance: similarity = 1 / (1 + distance)
                    # Using cosine-normalized calculation since we configured cosine space
                    if distance < 0:
                        score = 0.0
                    elif distance > 2:
                        score = 0.0
                    else:
                        score = 1.0 - (distance / 2.0)  # Normalized for cosine distance (0-2 range)
                    
                    # Ensure metadata is a dict
                    metadata_dict = dict(metadata) if not isinstance(metadata, dict) else metadata

                    # Ensure created_at is a string before parsing
                    created_at_val = metadata_dict.get('created_at')
                    created_at = None
                    if isinstance(created_at_val, str):
                        try:
                            created_at = datetime.fromisoformat(created_at_val)
                        except Exception:
                            created_at = None

                    document = Document(
                        id=doc_id,
                        content=content,
                        metadata=metadata_dict,
                        doc_type=DocumentType(metadata_dict.get('doc_type', 'text')),
                        created_at=created_at
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


__all__ = ['ChromaRAGProvider']
