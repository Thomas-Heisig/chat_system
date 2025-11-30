# services/rag/qdrant_rag.py
"""
Qdrant RAG Provider
Production-grade vector database for scalable deployments
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
import uuid
import hashlib
import logging

from .base_rag import BaseRAGProvider, Document, SearchResult, DocumentType

# Type imports for better IDE support
if TYPE_CHECKING:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models

# Optional import - Qdrant support
# Hint to type checkers: this will be assigned to the real module when available
qdrant_models: Any = None
_QdrantClient: Any = None
try:
    from qdrant_client import QdrantClient as _ImportedQdrantClient
    from qdrant_client.http import models as qdrant_models
    _QdrantClient = _ImportedQdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    # Keep as None at runtime but typed as Any to avoid "attribute of None" diagnostics
    qdrant_models = None

logger = logging.getLogger(__name__)


class QdrantRAGProvider(BaseRAGProvider):
    """Qdrant RAG provider for production vector storage"""
    
    def __init__(self, config: Dict[str, Any]):
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "qdrant-client is required for Qdrant support. "
                "Install with: pip install qdrant-client"
            )
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6333)
        self.grpc_port = config.get('grpc_port', 6334)
        self.api_key = config.get('api_key')
        self._embedding_dimension = config.get('embedding_dimension', 384)
        self._client: Optional['QdrantClient'] = None
        self._use_async = config.get('use_async', False)
    
    @property
    def provider_name(self) -> str:
        return "qdrant"
    
    @property
    def embedding_dimension(self) -> int:
        return self._embedding_dimension
    
    def _generate_point_id(self, doc_id: str) -> int:
        """Generate consistent integer point ID from string document ID"""
        # Use hash to convert string to consistent integer
        hash_obj = hashlib.md5(doc_id.encode())
        return int(hash_obj.hexdigest()[:16], 16) % (2**63 - 1)
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate deterministic pseudo-embedding from query text.
        
        In production, replace with actual embedding model like:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode(query).tolist()
        """
        # Create deterministic pseudo-embedding based on query text
        # This ensures different queries get different vectors
        hash_obj = hashlib.sha256(query.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash to vector of required dimension
        vector = []
        for i in range(self._embedding_dimension):
            # Use different parts of hash for each dimension
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] / 255.0) * 2 - 1  # Normalize to [-1, 1]
            vector.append(float(value))
        
        return vector
    
    async def initialize(self) -> bool:
        """Initialize Qdrant client and collection"""
        try:
            self._client = _QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                grpc_port=self.grpc_port,
                prefer_grpc=self._use_async
            )
            assert self._client is not None
            
            # Check if collection exists
            # Check if collection exists
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection with optimized configuration
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self._embedding_dimension,
                        distance=qdrant_models.Distance.COSINE
                    ),
                    # Add optimization settings for production
                    optimizers_config=qdrant_models.OptimizersConfigDiff(
                        default_segment_number=2,
                        max_segment_size=50000,
                        memmap_threshold=20000
                    ),
                    # Enable persistence
                    hnsw_config=qdrant_models.HnswConfigDiff(
                        m=16,
                        ef_construct=100
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
            
            self._initialized = True
            logger.info("Qdrant RAG provider initialized successfully")
            return True
        except Exception as e:
            self._initialized = False
            logger.error(f"Failed to initialize Qdrant: {e}")
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
                    doc.embedding = self._generate_query_embedding(doc.content)
                
                # Convert string ID to integer point ID
                point_id = self._generate_point_id(doc.id)
                
                payload = doc.metadata.copy()
                payload['content'] = doc.content
                payload['doc_type'] = doc.doc_type.value  # Store enum value
                payload['original_doc_id'] = doc.id  # Keep original ID
                payload['created_at'] = doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat()
                
                points.append(qdrant_models.PointStruct(
                    id=point_id,
                    vector=doc.embedding,
                    payload=payload
                ))
            
            # Use upsert for idempotent operation
            self._client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True  # Wait for operation to complete
            )
            
            logger.info(f"Added {len(documents)} documents to Qdrant collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to Qdrant: {e}")
            raise RuntimeError(f"Failed to add documents: {e}")
    
    async def query(self, query: str, top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Query Qdrant for similar documents"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=value)
                        )
                    )
                qdrant_filter = qdrant_models.Filter(must=conditions)
            
            # Execute search
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                score_threshold=0.1  # Minimum similarity threshold
            )
            
            search_results = []
            
            for hit in results:
                payload = hit.payload or {}
                
                # Reconstruct document
                document = Document(
                    id=payload.get('original_doc_id', str(hit.id)),  # Use original ID
                    content=payload.get('content', ''),
                    metadata={k: v for k, v in payload.items() 
                             if k not in ['content', 'doc_type', 'created_at', 'original_doc_id']},
                    doc_type=DocumentType(payload.get('doc_type', 'text')),
                    created_at=datetime.fromisoformat(created_at_str) if (created_at_str := payload.get('created_at')) and isinstance(created_at_str, str) else None
                )
                
                search_results.append(SearchResult(
                    document=document,
                    score=hit.score
                ))
            
            logger.debug(f"Qdrant query returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Qdrant query failed: {e}")
            raise RuntimeError(f"Query failed: {e}")
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from Qdrant"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # Convert string document IDs to point IDs
            point_ids = [self._generate_point_id(doc_id) for doc_id in doc_ids]
            
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(points=point_ids),
                wait=True
            )
            
            logger.info(f"Deleted {len(doc_ids)} documents from Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from Qdrant: {e}")
            raise RuntimeError(f"Failed to delete documents: {e}")
    
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """Update document in Qdrant"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # Generate embedding if not provided
            if document.embedding is None:
                document.embedding = self._generate_query_embedding(document.content)
            
            # Convert string ID to integer point ID
            point_id = self._generate_point_id(doc_id)
            
            payload = document.metadata.copy()
            payload['content'] = document.content
            payload['doc_type'] = document.doc_type.value
            payload['original_doc_id'] = doc_id
            payload['updated_at'] = datetime.now().isoformat()
            
            self._client.upsert(
                collection_name=self.collection_name,
                points=[qdrant_models.PointStruct(
                    id=point_id,
                    vector=document.embedding,
                    payload=payload
                )],
                wait=True
            )
            
            logger.info(f"Updated document {doc_id} in Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document in Qdrant: {e}")
            raise RuntimeError(f"Failed to update document: {e}")
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve specific document by ID"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            point_id = self._generate_point_id(doc_id)
            
            points = self._client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return None
            
            point = points[0]
            payload = point.payload or {}
            
            return Document(
                id=payload.get('original_doc_id', str(point.id)),
                content=payload.get('content', ''),
                metadata={k: v for k, v in payload.items() 
                         if k not in ['content', 'doc_type', 'created_at', 'original_doc_id']},
                doc_type=DocumentType(payload.get('doc_type', 'text')),
                created_at=datetime.fromisoformat(created_at_str) if (created_at_str := payload.get('created_at')) and isinstance(created_at_str, str) else None
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve document from Qdrant: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant collection statistics"""
        if not self._client:
            return {"error": "Not initialized"}
        
        try:
            collection_info = self._client.get_collection(self.collection_name)
            
            # Get approximate count
            count_result = self._client.count(
                collection_name=self.collection_name,
                exact=False  # Faster approximate count
            )
            
            return {
                "provider": self.provider_name,
                "collection_name": self.collection_name,
                "document_count": count_result.count,
                "vector_dimension": self._embedding_dimension,
                "status": str(collection_info.status),
                "host": self.host,
                "port": self.port,
                "vectors_count": collection_info.vectors_count,
                "segments_count": collection_info.segments_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get Qdrant stats: {e}")
            return {"error": str(e)}
    
    async def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            self._client.delete_collection(self.collection_name)
            
            # Recreate collection
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self._embedding_dimension,
                    distance=qdrant_models.Distance.COSINE
                )
            )
            
            logger.info(f"Cleared Qdrant collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear Qdrant collection: {e}")
            raise RuntimeError(f"Failed to clear collection: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health and connectivity"""
        if not self._client:
            return {"status": "not_initialized"}
        
        try:
            # Test connection by listing collections
            collections = self._client.get_collections()
            collection_info = self._client.get_collection(self.collection_name)
            
            count_result = self._client.count(
                collection_name=self.collection_name,
                exact=False
            )
            
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "document_count": count_result.count,
                "collection": self.collection_name,
                "total_collections": len(collections.collections),
                "collection_status": str(collection_info.status),
                "host": self.host,
                "port": self.port
            }
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def create_snapshot(self, snapshot_path: str) -> bool:
        """Create collection snapshot (Qdrant Cloud feature)"""
        if not self._client:
            raise RuntimeError("Qdrant not initialized")
        
        try:
            # This requires Qdrant Cloud or self-hosted with snapshot support
            snapshot_info = self._client.create_snapshot(
                collection_name=self.collection_name
            )
            
            logger.info(f"Created snapshot: {snapshot_info.name}")
            return True
            
        except Exception as e:
            logger.warning(f"Snapshot creation not supported: {e}")
            return False


__all__ = ['QdrantRAGProvider']