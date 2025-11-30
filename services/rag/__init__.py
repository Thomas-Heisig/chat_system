# services/rag/__init__.py
"""
Modular RAG (Retrieval Augmented Generation) System
Supports multiple vector database backends
"""

from typing import Type, Dict
from .base_rag import BaseRAGProvider
from .document_processor import DocumentProcessor, ChunkConfig

# Registry of available RAG providers
RAG_PROVIDER_REGISTRY: Dict[str, Type[BaseRAGProvider]] = {}

# Try to import ChromaDB provider
try:
    from .chroma_rag import ChromaRAGProvider
    RAG_PROVIDER_REGISTRY["chromadb"] = ChromaRAGProvider
except ImportError:
    pass

# Try to import Qdrant provider
try:
    from .qdrant_rag import QdrantRAGProvider
    RAG_PROVIDER_REGISTRY["qdrant"] = QdrantRAGProvider
except ImportError:
    pass


def get_rag_provider(provider_name: str) -> Type[BaseRAGProvider]:
    """Get RAG provider class by name"""
    provider = RAG_PROVIDER_REGISTRY.get(provider_name.lower())
    if not provider:
        available = list(RAG_PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unknown RAG provider: {provider_name}. Available: {available}")
    return provider


def get_available_providers() -> Dict[str, bool]:
    """Get list of available RAG providers"""
    return {
        "chromadb": "chromadb" in RAG_PROVIDER_REGISTRY,
        "qdrant": "qdrant" in RAG_PROVIDER_REGISTRY,
        "pinecone": "pinecone" in RAG_PROVIDER_REGISTRY,
        "weaviate": "weaviate" in RAG_PROVIDER_REGISTRY,
        "milvus": "milvus" in RAG_PROVIDER_REGISTRY
    }


__all__ = [
    'BaseRAGProvider',
    'DocumentProcessor',
    'ChunkConfig',
    'get_rag_provider',
    'get_available_providers',
    'RAG_PROVIDER_REGISTRY'
]
