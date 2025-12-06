# Knowledge Database and RAG System Guide

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Estimated Reading Time:** 25 minutes

## 📋 Table of Contents

- [Overview](#overview)
- [Training Data Storage](#training-data-storage)
- [Vector Database Management](#vector-database-management)
- [Document Retrieval](#document-retrieval)
- [Knowledge Base Organization](#knowledge-base-organization)
- [Performance Optimization](#performance-optimization)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Overview

The Knowledge Database is the core storage and retrieval system for the RAG (Retrieval-Augmented Generation) capabilities. It provides semantic search, document management, and intelligent knowledge retrieval to enhance AI responses with relevant context.

### System Architecture

```
┌─────────────────┐
│  Document Input │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Text Extraction │ ← PDF, DOCX, TXT, MD
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Chunking     │ ← Strategy: Fixed, Semantic, Sentence
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Embedding     │ ← Model: MiniLM, MPNet, Ada-002
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vector Store   │ ← ChromaDB, Qdrant, Pinecone
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Semantic Query │ ← Similarity Search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context for AI  │
└─────────────────┘
```

### Key Components

**Storage Backends**:
- ChromaDB (embedded, local)
- Qdrant (high-performance, distributed)
- Pinecone (cloud-native, managed)

**Embedding Models**:
- all-MiniLM-L6-v2 (384 dimensions, fast)
- all-mpnet-base-v2 (768 dimensions, quality)
- text-embedding-ada-002 (1536 dimensions, OpenAI)

**Features**:
- Multi-format document support
- Intelligent chunking strategies
- Metadata filtering
- Hybrid search (keyword + semantic)
- Version control for documents

## Training Data Storage

### 1. Document Structure

```python
class Document:
    """Document schema for knowledge base"""
    
    def __init__(self, content, metadata):
        self.id = generate_uuid()
        self.content = content
        self.metadata = {
            # Required fields
            "source": metadata.get("source"),
            "title": metadata.get("title"),
            "created_at": datetime.now().isoformat(),
            
            # Classification
            "type": metadata.get("type"),  # doc, code, conversation, etc.
            "category": metadata.get("category"),
            "tags": metadata.get("tags", []),
            
            # Processing
            "chunk_strategy": metadata.get("chunk_strategy", "fixed"),
            "embedding_model": metadata.get("embedding_model"),
            "language": metadata.get("language", "en"),
            
            # Access control
            "access_level": metadata.get("access_level", "public"),
            "owner_id": metadata.get("owner_id"),
            
            # Versioning
            "version": metadata.get("version", 1),
            "parent_id": metadata.get("parent_id"),
            
            # Additional metadata
            **{k: v for k, v in metadata.items() 
               if k not in ["source", "title", "type", "category"]}
        }
        self.chunks = []
        self.embeddings = []
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "chunks": self.chunks,
            "embeddings": self.embeddings
        }
```

### 2. Storage Formats

#### Structured Storage (PostgreSQL)

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    content TEXT,
    source VARCHAR(500),
    type VARCHAR(50),
    category VARCHAR(100),
    owner_id UUID,
    access_level VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata JSONB,
    INDEX idx_type (type),
    INDEX idx_category (category),
    INDEX idx_owner (owner_id),
    INDEX idx_created (created_at)
);

-- Chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT,
    token_count INTEGER,
    created_at TIMESTAMP,
    INDEX idx_document (document_id),
    INDEX idx_chunk_index (document_id, chunk_index)
);

-- Embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    model VARCHAR(100),
    embedding VECTOR(384),  -- Using pgvector extension
    created_at TIMESTAMP,
    INDEX idx_chunk (chunk_id),
    INDEX idx_model (model)
);
```

#### File-Based Storage

```python
class FileStorageBackend:
    """File-based document storage"""
    
    def __init__(self, base_path="./data/documents"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_document(self, document):
        """Save document to file system"""
        doc_dir = self.base_path / document.id
        doc_dir.mkdir(exist_ok=True)
        
        # Save main content
        with open(doc_dir / "content.txt", "w") as f:
            f.write(document.content)
        
        # Save metadata
        with open(doc_dir / "metadata.json", "w") as f:
            json.dump(document.metadata, f, indent=2)
        
        # Save chunks
        chunks_dir = doc_dir / "chunks"
        chunks_dir.mkdir(exist_ok=True)
        
        for i, chunk in enumerate(document.chunks):
            with open(chunks_dir / f"chunk_{i:04d}.txt", "w") as f:
                f.write(chunk)
        
        # Save embeddings (numpy format)
        if document.embeddings:
            embeddings_file = doc_dir / "embeddings.npy"
            np.save(embeddings_file, document.embeddings)
    
    def load_document(self, document_id):
        """Load document from file system"""
        doc_dir = self.base_path / document_id
        
        if not doc_dir.exists():
            return None
        
        # Load content
        with open(doc_dir / "content.txt", "r") as f:
            content = f.read()
        
        # Load metadata
        with open(doc_dir / "metadata.json", "r") as f:
            metadata = json.load(f)
        
        # Load chunks
        chunks = []
        chunks_dir = doc_dir / "chunks"
        if chunks_dir.exists():
            chunk_files = sorted(chunks_dir.glob("chunk_*.txt"))
            for chunk_file in chunk_files:
                with open(chunk_file, "r") as f:
                    chunks.append(f.read())
        
        # Load embeddings
        embeddings = []
        embeddings_file = doc_dir / "embeddings.npy"
        if embeddings_file.exists():
            embeddings = np.load(embeddings_file)
        
        document = Document(content, metadata)
        document.id = document_id
        document.chunks = chunks
        document.embeddings = embeddings
        
        return document
```

### 3. Data Ingestion Pipeline

```python
class IngestionPipeline:
    """Document ingestion and processing pipeline"""
    
    def __init__(self, storage_backend, vector_store, embedding_model):
        self.storage = storage_backend
        self.vector_store = vector_store
        self.embedding_model = embedding_model
    
    async def ingest_document(self, file_path, metadata=None):
        """Ingest a document into the knowledge base"""
        
        # Step 1: Extract text
        logger.info(f"Extracting text from {file_path}")
        content = await self.extract_text(file_path)
        
        # Step 2: Create document
        doc_metadata = metadata or {}
        doc_metadata.update({
            "source": str(file_path),
            "file_type": Path(file_path).suffix,
            "file_size": Path(file_path).stat().st_size
        })
        
        document = Document(content, doc_metadata)
        
        # Step 3: Chunk document
        logger.info(f"Chunking document: {document.id}")
        document.chunks = await self.chunk_document(document)
        
        # Step 4: Generate embeddings
        logger.info(f"Generating embeddings: {document.id}")
        document.embeddings = await self.generate_embeddings(document.chunks)
        
        # Step 5: Store in vector database
        logger.info(f"Storing in vector database: {document.id}")
        await self.vector_store.add_documents(
            ids=[f"{document.id}_{i}" for i in range(len(document.chunks))],
            embeddings=document.embeddings,
            documents=document.chunks,
            metadatas=[
                {**document.metadata, "chunk_index": i}
                for i in range(len(document.chunks))
            ]
        )
        
        # Step 6: Store document metadata
        logger.info(f"Storing metadata: {document.id}")
        await self.storage.save_document(document)
        
        logger.info(f"Successfully ingested document: {document.id}")
        
        return {
            "document_id": document.id,
            "chunks": len(document.chunks),
            "embeddings": len(document.embeddings),
            "metadata": document.metadata
        }
    
    async def extract_text(self, file_path):
        """Extract text from various file formats"""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            return await self.extract_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            return await self.extract_docx(file_path)
        elif suffix in [".txt", ".md"]:
            return await self.extract_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    async def extract_pdf(self, file_path):
        """Extract text from PDF"""
        from pypdf import PdfReader
        
        reader = PdfReader(file_path)
        text = []
        
        for page in reader.pages:
            text.append(page.extract_text())
        
        return "\n\n".join(text)
    
    async def extract_docx(self, file_path):
        """Extract text from DOCX"""
        from docx import Document
        
        doc = Document(file_path)
        text = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text.append(para.text)
        
        return "\n\n".join(text)
    
    async def extract_text_file(self, file_path):
        """Extract text from plain text file"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    async def chunk_document(self, document):
        """Chunk document based on strategy"""
        strategy = document.metadata.get("chunk_strategy", "fixed")
        
        if strategy == "fixed":
            return self.chunk_fixed_size(document.content)
        elif strategy == "semantic":
            return await self.chunk_semantic(document.content)
        elif strategy == "sentence":
            return self.chunk_sentences(document.content)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def chunk_fixed_size(self, text, size=1000, overlap=200):
        """Fixed-size chunking with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start = end - overlap
        
        return chunks
    
    def chunk_sentences(self, text, max_size=1000):
        """Sentence-based chunking"""
        import nltk
        sentences = nltk.sent_tokenize(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > max_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def chunk_semantic(self, text):
        """Semantic chunking using embeddings"""
        import nltk
        from sentence_transformers import SentenceTransformer
        
        # Split into sentences
        sentences = nltk.sent_tokenize(text)
        
        # Generate embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(sentences)
        
        # Find semantic boundaries
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = np.dot(embeddings[i], embeddings[i+1])
            similarities.append(sim)
        
        # Split at low similarity points
        threshold = np.percentile(similarities, 30)
        splits = [i for i, sim in enumerate(similarities) if sim < threshold]
        
        # Create chunks
        chunks = []
        start = 0
        for split in splits:
            chunk = " ".join(sentences[start:split+1])
            if chunk.strip():
                chunks.append(chunk)
            start = split + 1
        
        if start < len(sentences):
            chunks.append(" ".join(sentences[start:]))
        
        return chunks
    
    async def generate_embeddings(self, chunks):
        """Generate embeddings for chunks"""
        embeddings = self.embedding_model.encode(chunks)
        return embeddings
```

## Vector Database Management

### 1. ChromaDB Backend

```python
class ChromaDBBackend:
    """ChromaDB vector database backend"""
    
    def __init__(self, persist_directory="./data/chromadb"):
        import chromadb
        from chromadb.config import Settings
        
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document knowledge base"}
        )
    
    async def add_documents(self, ids, embeddings, documents, metadatas):
        """Add documents to collection"""
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas
        )
    
    async def query(self, query_embedding, n_results=5, where=None):
        """Query similar documents"""
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where
        )
        
        return {
            "ids": results["ids"][0],
            "distances": results["distances"][0],
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0]
        }
    
    async def delete(self, ids):
        """Delete documents"""
        self.collection.delete(ids=ids)
    
    async def get_stats(self):
        """Get collection statistics"""
        count = self.collection.count()
        
        return {
            "total_documents": count,
            "collection_name": self.collection.name
        }
```

### 2. Qdrant Backend

```python
class QdrantBackend:
    """Qdrant vector database backend"""
    
    def __init__(self, url="http://localhost:6333", collection_name="documents"):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        
        # Create collection if not exists
        try:
            self.client.get_collection(collection_name)
        except:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,  # Embedding dimension
                    distance=Distance.COSINE
                )
            )
    
    async def add_documents(self, ids, embeddings, documents, metadatas):
        """Add documents to collection"""
        from qdrant_client.models import PointStruct
        
        points = [
            PointStruct(
                id=ids[i],
                vector=embeddings[i].tolist(),
                payload={
                    "text": documents[i],
                    **metadatas[i]
                }
            )
            for i in range(len(ids))
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    async def query(self, query_embedding, n_results=5, where=None):
        """Query similar documents"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Build filter
        filter_obj = None
        if where:
            conditions = [
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
                for key, value in where.items()
            ]
            filter_obj = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=n_results,
            query_filter=filter_obj
        )
        
        return {
            "ids": [r.id for r in results],
            "scores": [r.score for r in results],
            "documents": [r.payload["text"] for r in results],
            "metadatas": [
                {k: v for k, v in r.payload.items() if k != "text"}
                for r in results
            ]
        }
```

### 3. Database Operations

```python
class KnowledgeBase:
    """High-level knowledge base operations"""
    
    def __init__(self, vector_backend, storage_backend, embedding_model):
        self.vector_db = vector_backend
        self.storage = storage_backend
        self.embedding_model = embedding_model
    
    async def add_document(self, content, metadata):
        """Add document to knowledge base"""
        pipeline = IngestionPipeline(
            self.storage,
            self.vector_db,
            self.embedding_model
        )
        
        return await pipeline.ingest_document(content, metadata)
    
    async def search(self, query, top_k=5, filters=None):
        """Search knowledge base"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Query vector database
        results = await self.vector_db.query(
            query_embedding,
            n_results=top_k,
            where=filters
        )
        
        return [
            {
                "id": results["ids"][i],
                "text": results["documents"][i],
                "score": results.get("scores", results.get("distances"))[i],
                "metadata": results["metadatas"][i]
            }
            for i in range(len(results["ids"]))
        ]
    
    async def delete_document(self, document_id):
        """Delete document from knowledge base"""
        # Get all chunk IDs for document
        chunks = await self.storage.get_document_chunks(document_id)
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        
        # Delete from vector database
        await self.vector_db.delete(chunk_ids)
        
        # Delete from storage
        await self.storage.delete_document(document_id)
    
    async def update_document(self, document_id, new_content=None, new_metadata=None):
        """Update existing document"""
        # Load existing document
        document = await self.storage.load_document(document_id)
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Update content if provided
        if new_content:
            document.content = new_content
            # Re-chunk and re-embed
            document.chunks = await self.chunk_document(document)
            document.embeddings = await self.generate_embeddings(document.chunks)
            
            # Update vector database
            chunk_ids = [f"{document_id}_{i}" for i in range(len(document.chunks))]
            await self.vector_db.delete(chunk_ids)
            await self.vector_db.add_documents(
                ids=chunk_ids,
                embeddings=document.embeddings,
                documents=document.chunks,
                metadatas=[
                    {**document.metadata, "chunk_index": i}
                    for i in range(len(document.chunks))
                ]
            )
        
        # Update metadata if provided
        if new_metadata:
            document.metadata.update(new_metadata)
        
        # Increment version
        document.metadata["version"] += 1
        document.metadata["updated_at"] = datetime.now().isoformat()
        
        # Save updated document
        await self.storage.save_document(document)
        
        return document
    
    async def get_stats(self):
        """Get knowledge base statistics"""
        vector_stats = await self.vector_db.get_stats()
        storage_stats = await self.storage.get_stats()
        
        return {
            **vector_stats,
            **storage_stats
        }
```

## Document Retrieval

### 1. Semantic Search

```python
async def semantic_search(query, knowledge_base, top_k=5):
    """Perform semantic search"""
    results = await knowledge_base.search(query, top_k=top_k)
    
    return [
        {
            "text": result["text"],
            "score": result["score"],
            "source": result["metadata"]["source"],
            "title": result["metadata"].get("title", "Untitled")
        }
        for result in results
    ]
```

### 2. Hybrid Search (Keyword + Semantic)

```python
from rank_bm25 import BM25Okapi

class HybridSearch:
    """Combine keyword and semantic search"""
    
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.bm25_index = None
        self.documents = []
    
    async def build_keyword_index(self):
        """Build BM25 keyword index"""
        # Get all documents
        self.documents = await self.kb.storage.get_all_documents()
        
        # Tokenize documents
        tokenized = [doc["content"].split() for doc in self.documents]
        
        # Create BM25 index
        self.bm25_index = BM25Okapi(tokenized)
    
    async def search(self, query, top_k=10, alpha=0.5):
        """
        Hybrid search
        alpha: weight for semantic search (1-alpha for keyword)
        """
        # Keyword search
        tokenized_query = query.split()
        keyword_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Semantic search
        semantic_results = await self.kb.search(query, top_k=top_k*2)
        
        # Combine scores
        combined = {}
        
        # Add keyword scores
        for i, score in enumerate(keyword_scores):
            doc_id = self.documents[i]["id"]
            combined[doc_id] = {
                "doc": self.documents[i],
                "keyword_score": score,
                "semantic_score": 0
            }
        
        # Add semantic scores
        for result in semantic_results:
            doc_id = result["id"].split("_")[0]
            if doc_id in combined:
                combined[doc_id]["semantic_score"] = result["score"]
            else:
                combined[doc_id] = {
                    "doc": result,
                    "keyword_score": 0,
                    "semantic_score": result["score"]
                }
        
        # Calculate hybrid scores
        for doc_id in combined:
            kw = combined[doc_id]["keyword_score"]
            sem = combined[doc_id]["semantic_score"]
            combined[doc_id]["hybrid_score"] = (1 - alpha) * kw + alpha * sem
        
        # Sort by hybrid score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x["hybrid_score"],
            reverse=True
        )
        
        return sorted_results[:top_k]
```

### 3. Contextual Retrieval

```python
def retrieve_with_context(query, conversation_history, knowledge_base, top_k=5):
    """Retrieve documents with conversation context"""
    
    # Build enhanced query from conversation
    recent_messages = conversation_history[-5:]
    context_keywords = extract_keywords(recent_messages)
    enhanced_query = f"{query} {' '.join(context_keywords)}"
    
    # Retrieve documents
    results = await knowledge_base.search(enhanced_query, top_k=top_k*2)
    
    # Re-rank based on conversation relevance
    for result in results:
        relevance_boost = 0
        
        # Boost if mentioned in recent conversation
        for msg in recent_messages:
            if any(word in result["text"].lower() 
                   for word in msg["content"].lower().split()):
                relevance_boost += 0.1
        
        result["score"] *= (1 + relevance_boost)
    
    # Sort by adjusted score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]
```

## Knowledge Base Organization

### 1. Collections and Namespaces

```python
class OrganizedKnowledgeBase:
    """Knowledge base with collections"""
    
    def __init__(self):
        self.collections = {}
    
    def create_collection(self, name, description=""):
        """Create a new collection"""
        self.collections[name] = {
            "description": description,
            "documents": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "document_count": 0
            }
        }
    
    async def add_to_collection(self, collection_name, document_id):
        """Add document to collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        
        self.collections[collection_name]["documents"].append(document_id)
        self.collections[collection_name]["metadata"]["document_count"] += 1
    
    async def search_collection(self, collection_name, query, top_k=5):
        """Search within a collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        
        # Get document IDs in collection
        doc_ids = self.collections[collection_name]["documents"]
        
        # Search with filter
        results = await self.kb.search(
            query,
            top_k=top_k,
            filters={"document_id": {"$in": doc_ids}}
        )
        
        return results
```

### 2. Tagging and Categorization

```python
class TagManager:
    """Manage document tags"""
    
    def __init__(self):
        self.tags = {}  # tag -> [document_ids]
        self.document_tags = {}  # document_id -> [tags]
    
    def add_tag(self, document_id, tag):
        """Add tag to document"""
        # Add to tags index
        if tag not in self.tags:
            self.tags[tag] = []
        if document_id not in self.tags[tag]:
            self.tags[tag].append(document_id)
        
        # Add to document tags
        if document_id not in self.document_tags:
            self.document_tags[document_id] = []
        if tag not in self.document_tags[document_id]:
            self.document_tags[document_id].append(tag)
    
    def get_documents_by_tag(self, tag):
        """Get all documents with tag"""
        return self.tags.get(tag, [])
    
    def get_tags_for_document(self, document_id):
        """Get all tags for document"""
        return self.document_tags.get(document_id, [])
    
    def search_by_tags(self, tags, operator="OR"):
        """Search documents by tags"""
        if operator == "OR":
            # Union of all documents with any tag
            doc_ids = set()
            for tag in tags:
                doc_ids.update(self.tags.get(tag, []))
            return list(doc_ids)
        
        elif operator == "AND":
            # Intersection of documents with all tags
            if not tags:
                return []
            
            doc_ids = set(self.tags.get(tags[0], []))
            for tag in tags[1:]:
                doc_ids &= set(self.tags.get(tag, []))
            return list(doc_ids)
```

## Performance Optimization

### 1. Caching Layer

```python
from functools import lru_cache
import hashlib

class CachedKnowledgeBase:
    """Knowledge base with caching"""
    
    def __init__(self, knowledge_base, cache_size=1000, ttl=3600):
        self.kb = knowledge_base
        self.cache_size = cache_size
        self.ttl = ttl
        self.cache = {}
    
    def _cache_key(self, query, top_k, filters):
        """Generate cache key"""
        key_data = f"{query}:{top_k}:{str(filters)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def search(self, query, top_k=5, filters=None):
        """Search with caching"""
        cache_key = self._cache_key(query, top_k, filters)
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < self.ttl:
                return cached["results"]
        
        # Perform search
        results = await self.kb.search(query, top_k, filters)
        
        # Store in cache
        self.cache[cache_key] = {
            "results": results,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self.cache) > self.cache_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        return results
```

### 2. Batch Operations

```python
async def batch_add_documents(knowledge_base, documents, batch_size=10):
    """Add multiple documents in batches"""
    results = []
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        
        # Process batch in parallel
        tasks = [
            knowledge_base.add_document(doc["content"], doc["metadata"])
            for doc in batch
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(batch_results)
    
    return results
```

## Monitoring and Maintenance

### 1. Health Checks

```python
async def check_knowledge_base_health(knowledge_base):
    """Check knowledge base health"""
    health = {
        "status": "healthy",
        "issues": []
    }
    
    # Check vector database
    try:
        stats = await knowledge_base.get_stats()
        health["vector_db"] = {
            "status": "ok",
            "document_count": stats.get("total_documents", 0)
        }
    except Exception as e:
        health["status"] = "degraded"
        health["issues"].append(f"Vector DB error: {e}")
        health["vector_db"] = {"status": "error"}
    
    # Check storage
    try:
        storage_stats = await knowledge_base.storage.get_stats()
        health["storage"] = {
            "status": "ok",
            **storage_stats
        }
    except Exception as e:
        health["status"] = "degraded"
        health["issues"].append(f"Storage error: {e}")
        health["storage"] = {"status": "error"}
    
    return health
```

### 2. Maintenance Tasks

```python
async def maintenance_tasks(knowledge_base):
    """Run maintenance tasks"""
    
    # 1. Clean up orphaned chunks
    await cleanup_orphaned_chunks(knowledge_base)
    
    # 2. Rebuild indexes
    await rebuild_indexes(knowledge_base)
    
    # 3. Optimize storage
    await optimize_storage(knowledge_base)
    
    # 4. Update statistics
    await update_statistics(knowledge_base)

async def cleanup_orphaned_chunks(knowledge_base):
    """Remove chunks without parent documents"""
    # Implementation
    pass

async def rebuild_indexes(knowledge_base):
    """Rebuild search indexes"""
    # Implementation
    pass
```

## Next Steps

- **[AI_INTEGRATION.md](AI_INTEGRATION.md)** - Learn about AI and RAG integration
- **[Examples](examples/)** - Practical code examples
- **[API Reference](docs/04-api-reference/README.md)** - Complete API documentation

---

**Need Help?** Check the [documentation](docs/) or [open an issue](https://github.com/Thomas-Heisig/chat_system/issues).
