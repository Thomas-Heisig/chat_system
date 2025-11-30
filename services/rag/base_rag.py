# services/rag/base_rag.py
"""
Base RAG Provider Interface
Abstract base class for all RAG (Retrieval Augmented Generation) providers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents that can be indexed"""
    TEXT = "text"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"
    CHAT_MESSAGE = "chat_message"


@dataclass
class Document:
    """Document representation for RAG system"""
    id: str
    content: str
    metadata: Dict[str, Any]
    doc_type: DocumentType = DocumentType.TEXT
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "doc_type": self.doc_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class SearchResult:
    """Search result from RAG query"""
    document: Document
    score: float
    highlights: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "highlights": self.highlights
        }


class BaseRAGProvider(ABC):
    """
    Abstract base class for RAG providers.
    All RAG providers must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize RAG provider with configuration"""
        self.config = config
        self.collection_name = config.get('collection_name', 'documents')
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the RAG provider (create collections, load models, etc.)
        Returns True if initialization successful.
        """
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> bool:
        """
        Add documents to the vector store.
        Returns True if all documents were added successfully.
        """
        pass
    
    @abstractmethod
    async def query(self, query: str, top_k: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Query the vector store and return top_k most similar documents.
        
        Args:
            query: The search query string
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        pass
    
    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete documents from the vector store by their IDs.
        Returns True if all documents were deleted successfully.
        """
        pass
    
    @abstractmethod
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """
        Update an existing document in the vector store.
        Returns True if update was successful.
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        Returns dict with document count, index size, etc.
        """
        pass
    
    @abstractmethod
    async def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        Returns True if successful.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the RAG provider.
        Returns dict with status and details.
        """
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized"""
        return self._initialized
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name identifier"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the embedding dimension being used"""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Return sanitized configuration"""
        safe_config = self.config.copy()
        if 'api_key' in safe_config:
            safe_config['api_key'] = '***'
        return safe_config
    
    async def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None,
                       doc_id: Optional[str] = None) -> str:
        """
        Convenience method to add a single text document.
        Returns the document ID.
        """
        import uuid
        doc_id = doc_id or str(uuid.uuid4())
        
        document = Document(
            id=doc_id,
            content=text,
            metadata=metadata or {},
            doc_type=DocumentType.TEXT,
            created_at=datetime.now()
        )
        
        await self.add_documents([document])
        return doc_id
    
    async def search_similar(self, text: str, top_k: int = 5) -> List[SearchResult]:
        """
        Convenience method to search for similar documents.
        """
        return await self.query(text, top_k=top_k)


__all__ = ['BaseRAGProvider', 'Document', 'SearchResult', 'DocumentType']
