# services/rag/qdrant_rag.py
"""
Qdrant RAG Provider
Production-grade vector database for scalable deployments
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .base_rag import BaseRAGProvider, Document, SearchResult, DocumentType

# Optional import - Qdrant support
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None


class QdrantRAGProvider(BaseRAGProvider):
    """Qdrant RAG provider for production vector storage"""
    
    def __init__(self, config: Dict[str, Any]):
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant-client is required. Install with: pip install qdrant-client")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6333)
        self.grpc_port = config.get('grpc_port', 6334)
        self.api_key = config.get('api_key')
        self._embedding_dimension = config.get('embedding_dimension', 384)
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "qdrant"
    
    @property
    def embedding_dimension(self) -> int:
        return self._embedding_dimension
    
    async def initialize(self) -> bool:
        """Initialize Qdrant client and collection"""
        try:
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key
            )
            
            # Check if collection exists
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self._embedding_dimension,
                        distance=models.Distance.COSINE
                    )
                )
            
            self._initialized = True
            return True
        except Exception as e:
            self._initialized = False
            raise RuntimeError(f"Failed to initialize Qdrant: {e}")
    
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to Qdrant"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            points = []
            
            for doc in documents:
                # Generate embedding if not provided
                if doc.embedding is None:
                    # Placeholder - in production, use actual embedding model
                    doc.embedding = [0.0] * self._embedding_dimension
                
                payload = doc.metadata.copy()
                payload['content'] = doc.content
                payload['doc_type'] = doc.doc_type
                payload['created_at'] = doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat()
                
                points.append(models.PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload=payload
                ))
            
            self._client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to add documents: {e}")
    
    async def query(self, query: str, top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Query Qdrant for similar documents
        
        Note: This implementation uses placeholder zero vectors for query embedding.
        In production, integrate a proper embedding model like sentence-transformers.
        """
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # Generate query embedding
            # IMPORTANT: This is a placeholder. In production, use actual embedding model.
            # Example: query_embedding = embedding_model.encode(query)
            query_embedding = [0.0] * self._embedding_dimension
            
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                qdrant_filter = models.Filter(must=conditions)
            
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter
            )
            
            search_results = []
            
            for hit in results:
                payload = hit.payload or {}
                
                document = Document(
                    id=str(hit.id),
                    content=payload.get('content', ''),
                    metadata={k: v for k, v in payload.items() if k not in ['content', 'doc_type', 'created_at']},
                    doc_type=DocumentType(payload.get('doc_type', 'text')),
                    created_at=datetime.fromisoformat(payload.get('created_at')) if payload.get('created_at') else None
                )
                
                search_results.append(SearchResult(
                    document=document,
                    score=hit.score
                ))
            
            return search_results
        except Exception as e:
            raise RuntimeError(f"Query failed: {e}")
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from Qdrant"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=doc_ids)
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete documents: {e}")
    
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """Update document in Qdrant"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # Generate embedding if not provided
            if document.embedding is None:
                document.embedding = [0.0] * self._embedding_dimension
            
            payload = document.metadata.copy()
            payload['content'] = document.content
            payload['doc_type'] = document.doc_type
            payload['updated_at'] = datetime.now().isoformat()
            
            self._client.upsert(
                collection_name=self.collection_name,
                points=[models.PointStruct(
                    id=doc_id,
                    vector=document.embedding,
                    payload=payload
                )]
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to update document: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant statistics"""
        if not self._client:
            return {"error": "Not initialized"}
        
        try:
            collection_info = self._client.get_collection(self.collection_name)
            
            return {
                "provider": self.provider_name,
                "collection_name": self.collection_name,
                "document_count": collection_info.points_count,
                "vector_dimension": self._embedding_dimension,
                "status": collection_info.status,
                "host": self.host,
                "port": self.port
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self._embedding_dimension,
                    distance=models.Distance.COSINE
                )
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to clear collection: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health"""
        if not self._client:
            return {"status": "not_initialized"}
        
        try:
            collections = self._client.get_collections()
            collection_info = self._client.get_collection(self.collection_name)
            
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "document_count": collection_info.points_count,
                "collection": self.collection_name,
                "total_collections": len(collections.collections)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


__all__ = ['QdrantRAGProvider']
