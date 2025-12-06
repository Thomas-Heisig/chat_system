# ADR-005: Vector Database Choice for RAG System

## Status
Accepted

## Date
2025-12-06

## Context
The Universal Chat System requires a vector database to support the RAG (Retrieval-Augmented Generation) system for semantic search and context-aware AI responses. The system needs to:
- Store document embeddings efficiently
- Support fast similarity searches (cosine similarity)
- Handle multiple document types (PDF, DOCX, TXT, Markdown)
- Scale from development to production environments
- Provide flexible deployment options (local, cloud, self-hosted)

## Decision
We decided to support **multiple vector databases** with ChromaDB as the default:
1. **ChromaDB** - Default for development and small deployments
2. **Qdrant** - For high-performance production deployments
3. **Pinecone** - For cloud-native deployments

This is implemented through a unified interface in `services/rag/` with provider-specific adapters.

## Consequences

### Positive
- **Flexibility**: Users can choose the database that fits their requirements
- **Low Barrier to Entry**: ChromaDB requires no setup, perfect for development
- **Scalability**: Can upgrade to Qdrant/Pinecone for production workloads
- **Portability**: Unified interface makes switching databases easy
- **Performance Options**: Different performance/cost tradeoffs available

### Negative
- **Increased Complexity**: Need to maintain multiple adapters
- **Testing Overhead**: Must test against all supported databases
- **Documentation Burden**: Need to document all three options
- **Feature Parity**: Must ensure consistent behavior across providers

### Neutral
- **Configuration Required**: Users must choose and configure their database
- **Dependency Management**: Multiple optional dependencies (chroma, qdrant-client, pinecone-client)

## Alternatives Considered

### Alternative 1: Single Vector Database (ChromaDB only)
- **Description**: Support only ChromaDB to simplify implementation
- **Pros**: 
  - Simpler codebase
  - Less maintenance
  - Easier testing
- **Cons**: 
  - Limited scalability
  - No performance optimization options
  - Vendor lock-in
- **Why Rejected**: Too limiting for enterprise deployments

### Alternative 2: PostgreSQL with pgvector
- **Description**: Use existing PostgreSQL database with pgvector extension
- **Pros**: 
  - No additional database needed
  - Unified data storage
  - Transactional consistency
- **Cons**: 
  - Lower performance for vector operations
  - Requires PostgreSQL (not compatible with SQLite/MongoDB option)
  - Limited vector-specific optimizations
- **Why Rejected**: Performance concerns and database dependency

### Alternative 3: Elasticsearch with Dense Vector
- **Description**: Use Elasticsearch for both search and vector storage
- **Pros**: 
  - Mature technology
  - Good full-text search capabilities
  - Can combine keyword and vector search
- **Cons**: 
  - Heavy resource requirements
  - Complex setup and maintenance
  - Overkill for simple vector search
- **Why Rejected**: Too complex for the use case

### Alternative 4: Milvus
- **Description**: Use Milvus, an open-source vector database
- **Pros**: 
  - Purpose-built for vectors
  - Good performance
  - Open source
- **Cons**: 
  - Less mature ecosystem
  - Steeper learning curve
  - Fewer managed hosting options
- **Why Rejected**: ChromaDB and Qdrant offer better developer experience

## References
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- RAG System implementation: `services/rag/`
- Configuration: `FEATURE_FLAGS.md` (RAG_ENABLED, VECTOR_DB_TYPE)
