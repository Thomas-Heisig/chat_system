# AI Integration and RAG System Guide

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Estimated Reading Time:** 30 minutes

## 📋 Table of Contents

- [Overview](#overview)
- [AI Model Integration](#ai-model-integration)
- [RAG System Components](#rag-system-components)
- [Document Processing](#document-processing)
- [Semantic Search](#semantic-search)
- [Advanced AI Features](#advanced-ai-features)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Overview

The Universal Chat System provides comprehensive AI integration capabilities through multiple AI providers and a sophisticated Retrieval-Augmented Generation (RAG) system. This guide covers all AI features with detailed examples.

### AI Capabilities

**Model Support**:
- Ollama (local models)
- OpenAI (cloud API)
- Custom model integrations
- Model switching and fallback

**RAG Features**:
- Multiple vector databases (ChromaDB, Qdrant, Pinecone)
- Intelligent document chunking
- Semantic search
- Context-aware responses
- Source attribution

**Processing**:
- Real-time inference
- Batch processing
- Streaming responses
- Multi-modal support (planned)

## AI Model Integration

### 1. Ollama Integration

#### Setup Ollama

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama2         # 7B parameter model
ollama pull llama2:13b     # Larger model
ollama pull mistral        # Alternative model
ollama pull codellama      # Code-specialized

# Verify installation
ollama list
```

#### Configure Ollama

```bash
# .env configuration
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama2
OLLAMA_TIMEOUT=300
```

#### Using Ollama in Chat

```python
# Python example
from services.ai_service import get_ai_service

ai_service = get_ai_service()

response = ai_service.generate(
    prompt="Explain quantum computing",
    model="llama2",
    temperature=0.7,
    max_tokens=500
)

print(response.content)
```

```bash
# REST API example
curl -X POST http://localhost:8000/api/v1/ai/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "model": "llama2",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### 2. OpenAI Integration

#### Setup OpenAI

```bash
# Get API key from https://platform.openai.com/api-keys

# Configure in .env
OPENAI_ENABLED=true
OPENAI_API_KEY=sk-...your-key...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
```

#### Using OpenAI

```python
from services.ai_service import get_ai_service

ai_service = get_ai_service()

response = ai_service.generate(
    prompt="Write a Python function to calculate fibonacci",
    model="gpt-3.5-turbo",
    temperature=0.3,  # Lower for more deterministic code
    max_tokens=300
)

print(response.content)
```

#### GPT-4 for Complex Tasks

```python
# Use GPT-4 for advanced reasoning
response = ai_service.generate(
    prompt="Analyze this code for security vulnerabilities: ...",
    model="gpt-4",
    temperature=0.2,
    max_tokens=1500
)
```

### 3. Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| llama2:7b | 7B | Fast | Good | General chat |
| llama2:13b | 13B | Medium | Better | Complex tasks |
| mistral | 7B | Fast | Good | General purpose |
| codellama | 7B | Fast | Good | Code generation |
| gpt-3.5-turbo | - | Fast | Great | Production |
| gpt-4 | - | Slow | Excellent | Complex reasoning |

### 4. Model Selection Strategy

```python
def select_model(task_type, complexity):
    """Intelligent model selection"""
    
    if task_type == "code":
        if complexity == "high":
            return "gpt-4" if openai_enabled else "codellama:13b"
        return "codellama"
    
    elif task_type == "analysis":
        if complexity == "high":
            return "gpt-4" if openai_enabled else "llama2:13b"
        return "llama2"
    
    elif task_type == "chat":
        return "llama2" if ollama_enabled else "gpt-3.5-turbo"
    
    else:
        return DEFAULT_MODEL

# Usage
model = select_model("code", "high")
response = ai_service.generate(prompt, model=model)
```

### 5. Advanced AI Parameters

```python
# Fine-tune generation
response = ai_service.generate(
    prompt="Your prompt here",
    
    # Model selection
    model="llama2",
    
    # Creativity control (0.0 = deterministic, 1.0 = creative)
    temperature=0.7,
    
    # Limit response length
    max_tokens=500,
    
    # Control randomness
    top_p=0.9,        # Nucleus sampling
    top_k=40,         # Top-k sampling
    
    # Repetition control
    frequency_penalty=0.5,
    presence_penalty=0.5,
    
    # Stop sequences
    stop=["\n\n", "END"],
    
    # Streaming
    stream=True
)
```

## RAG System Components

### 1. Vector Databases

#### ChromaDB (Default)

```bash
# Configuration
RAG_ENABLED=true
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/vectordb

# No additional installation needed (embedded)
```

```python
# Initialize ChromaDB
from services.rag.chroma_service import ChromaService

chroma = ChromaService()
chroma.initialize()

# Add documents
chroma.add_documents([
    {"id": "doc1", "text": "Content here", "metadata": {"source": "file.pdf"}}
])

# Query
results = chroma.query("search query", top_k=5)
```

#### Qdrant (High Performance)

```bash
# Install Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Configure
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key  # Optional
```

```python
from services.rag.qdrant_service import QdrantService

qdrant = QdrantService()
qdrant.create_collection("documents", vector_size=384)

# Add vectors
qdrant.add_vectors(
    collection="documents",
    vectors=[...],
    payloads=[{"text": "...", "metadata": {...}}]
)
```

#### Pinecone (Cloud)

```bash
# Configure
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX=chat-documents
```

```python
from services.rag.pinecone_service import PineconeService

pinecone = PineconeService()
pinecone.create_index("chat-documents", dimension=384)

# Upsert vectors
pinecone.upsert(
    index="chat-documents",
    vectors=[...],
    metadata=[...]
)
```

### 2. Embedding Models

```python
# Sentence Transformers (default)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("Text to embed")

# OpenAI Embeddings
from openai import OpenAI

client = OpenAI()
embedding = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Text to embed"
).data[0].embedding

# Compare models
models = {
    "all-MiniLM-L6-v2": {"size": 384, "speed": "fast", "quality": "good"},
    "all-mpnet-base-v2": {"size": 768, "speed": "medium", "quality": "better"},
    "text-embedding-ada-002": {"size": 1536, "speed": "slow", "quality": "best"}
}
```

### 3. Text Chunking Strategies

```python
# Strategy 1: Fixed-size chunking
def chunk_fixed_size(text, chunk_size=1000, overlap=200):
    """Simple fixed-size chunks with overlap"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # Overlap for context
    
    return chunks

# Strategy 2: Sentence-based chunking
def chunk_by_sentences(text, max_chunk_size=1000):
    """Chunk by complete sentences"""
    import nltk
    sentences = nltk.sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        if current_size + sentence_size > max_chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Strategy 3: Semantic chunking
def chunk_semantic(text, max_chunk_size=1000):
    """Chunk by semantic similarity"""
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    sentences = nltk.sent_tokenize(text)
    embeddings = model.encode(sentences)
    
    # Calculate similarity between consecutive sentences
    similarities = []
    for i in range(len(embeddings) - 1):
        sim = np.dot(embeddings[i], embeddings[i+1])
        similarities.append(sim)
    
    # Find split points (low similarity)
    threshold = np.percentile(similarities, 30)
    splits = [i for i, sim in enumerate(similarities) if sim < threshold]
    
    # Create chunks
    chunks = []
    start = 0
    for split in splits:
        chunk = " ".join(sentences[start:split+1])
        if len(chunk) > 0:
            chunks.append(chunk)
        start = split + 1
    
    # Add remaining sentences
    if start < len(sentences):
        chunks.append(" ".join(sentences[start:]))
    
    return chunks
```

## Document Processing

### 1. Document Upload and Processing

```python
from services.rag_service import get_rag_service

rag = get_rag_service()

# Upload document
result = rag.process_document(
    file_path="technical_spec.pdf",
    chunk_size=1000,
    chunk_overlap=200,
    metadata={
        "source": "technical_spec.pdf",
        "type": "specification",
        "date": "2025-12-06"
    }
)

print(f"Processed {result['chunks']} chunks")
print(f"Document ID: {result['document_id']}")
```

### 2. Supported Document Types

```python
# PDF Documents
from pypdf import PdfReader

def extract_pdf_text(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# DOCX Documents
from docx import Document

def extract_docx_text(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Text Files
def extract_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# Markdown Files
import markdown

def extract_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    html = markdown.markdown(md_text)
    # Convert HTML back to text or use raw markdown
    return md_text
```

### 3. Document Metadata

```python
# Rich metadata for better retrieval
metadata = {
    # Core fields
    "document_id": "doc-123",
    "filename": "quarterly_report.pdf",
    "title": "Q4 2024 Financial Report",
    
    # Content classification
    "type": "financial_report",
    "category": "finance",
    "tags": ["quarterly", "revenue", "expenses"],
    
    # Temporal
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z",
    "report_period": "Q4-2024",
    
    # Access control
    "access_level": "internal",
    "department": "finance",
    "owner": "user123",
    
    # Processing
    "chunk_strategy": "semantic",
    "embedding_model": "all-MiniLM-L6-v2",
    "language": "en",
    
    # Source
    "source_url": "https://internal.example.com/reports/q4-2024",
    "source_system": "sharepoint"
}
```

### 4. Batch Processing

```python
import asyncio
from pathlib import Path

async def process_directory(directory_path):
    """Process all documents in a directory"""
    rag = get_rag_service()
    path = Path(directory_path)
    
    # Find all supported files
    patterns = ["**/*.pdf", "**/*.docx", "**/*.txt", "**/*.md"]
    files = []
    for pattern in patterns:
        files.extend(path.glob(pattern))
    
    print(f"Found {len(files)} documents to process")
    
    # Process in parallel (limited concurrency)
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
    
    async def process_file(file_path):
        async with semaphore:
            try:
                result = await rag.process_document_async(str(file_path))
                print(f"✅ Processed: {file_path.name} ({result['chunks']} chunks)")
                return result
            except Exception as e:
                print(f"❌ Failed: {file_path.name} - {e}")
                return None
    
    results = await asyncio.gather(*[process_file(f) for f in files])
    
    # Summary
    successful = sum(1 for r in results if r)
    total_chunks = sum(r['chunks'] for r in results if r)
    
    print(f"\nProcessing complete:")
    print(f"  Successful: {successful}/{len(files)}")
    print(f"  Total chunks: {total_chunks}")
    
    return results

# Run batch processing
asyncio.run(process_directory("./documents"))
```

## Semantic Search

### 1. Basic Search

```python
from services.rag_service import get_rag_service

rag = get_rag_service()

# Simple search
results = rag.search(
    query="What are the deployment requirements?",
    top_k=5
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text'][:200]}...")
    print(f"Source: {result['metadata']['source']}")
    print("---")
```

### 2. Advanced Search with Filters

```python
# Search with metadata filters
results = rag.search(
    query="database optimization",
    top_k=10,
    filters={
        "type": "technical_doc",
        "date_from": "2025-01-01",
        "department": "engineering"
    },
    min_score=0.7  # Only high-relevance results
)
```

### 3. Hybrid Search (Keyword + Semantic)

```python
def hybrid_search(query, top_k=10, alpha=0.5):
    """
    Combine keyword and semantic search
    alpha: weight for semantic (1-alpha for keyword)
    """
    # Keyword search (BM25)
    keyword_results = bm25_search(query, top_k=top_k*2)
    
    # Semantic search (vector)
    semantic_results = vector_search(query, top_k=top_k*2)
    
    # Merge and re-rank
    combined = {}
    
    for result in keyword_results:
        doc_id = result['id']
        combined[doc_id] = {
            'doc': result,
            'keyword_score': result['score'],
            'semantic_score': 0
        }
    
    for result in semantic_results:
        doc_id = result['id']
        if doc_id in combined:
            combined[doc_id]['semantic_score'] = result['score']
        else:
            combined[doc_id] = {
                'doc': result,
                'keyword_score': 0,
                'semantic_score': result['score']
            }
    
    # Calculate hybrid score
    for doc_id in combined:
        kw_score = combined[doc_id]['keyword_score']
        sem_score = combined[doc_id]['semantic_score']
        combined[doc_id]['hybrid_score'] = (
            (1 - alpha) * kw_score + alpha * sem_score
        )
    
    # Sort by hybrid score
    sorted_results = sorted(
        combined.values(),
        key=lambda x: x['hybrid_score'],
        reverse=True
    )
    
    return sorted_results[:top_k]
```

### 4. Context-Aware Retrieval

```python
def retrieve_with_context(query, conversation_history, top_k=5):
    """Retrieve relevant documents considering conversation context"""
    
    # Build enhanced query from conversation
    recent_messages = conversation_history[-5:]
    context = " ".join([msg['content'] for msg in recent_messages])
    enhanced_query = f"{context} {query}"
    
    # Retrieve with enhanced query
    results = rag.search(enhanced_query, top_k=top_k)
    
    # Re-rank based on conversation relevance
    def relevance_score(result, history):
        score = result['score']
        
        # Boost if mentioned in recent conversation
        for msg in recent_messages:
            if any(word in result['text'].lower() 
                   for word in msg['content'].lower().split()):
                score *= 1.2
        
        return score
    
    for result in results:
        result['contextual_score'] = relevance_score(result, recent_messages)
    
    # Sort by contextual score
    results.sort(key=lambda x: x['contextual_score'], reverse=True)
    
    return results
```

## Advanced AI Features

### 1. Streaming Responses

```python
async def stream_ai_response(prompt, model="llama2"):
    """Stream AI response token by token"""
    ai_service = get_ai_service()
    
    async for token in ai_service.generate_stream(prompt, model=model):
        print(token, end='', flush=True)
        # Or send via WebSocket
        await websocket.send_text(token)
    
    print()  # Newline at end
```

```javascript
// JavaScript client for streaming
const ws = new WebSocket('ws://localhost:8000/ws');

ws.send(JSON.stringify({
    type: 'ai_stream',
    prompt: 'Explain machine learning',
    model: 'llama2'
}));

let fullResponse = '';
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'ai_token') {
        fullResponse += data.token;
        updateUI(fullResponse);  // Update UI incrementally
    } else if (data.type === 'ai_complete') {
        console.log('Stream complete');
    }
};
```

### 2. RAG-Enhanced AI Responses

```python
async def generate_rag_response(query, conversation_history=[]):
    """Generate AI response with RAG context"""
    
    # 1. Retrieve relevant documents
    docs = retrieve_with_context(
        query,
        conversation_history,
        top_k=5
    )
    
    # 2. Build context from retrieved documents
    context = "\n\n".join([
        f"Source: {doc['metadata']['source']}\n{doc['text']}"
        for doc in docs
    ])
    
    # 3. Build prompt with context
    prompt = f"""Context from knowledge base:
{context}

Conversation history:
{format_history(conversation_history)}

User question: {query}

Please answer the question based on the provided context. 
If the context doesn't contain relevant information, say so.
Always cite your sources."""

    # 4. Generate response
    ai_service = get_ai_service()
    response = await ai_service.generate_async(
        prompt=prompt,
        model="llama2:13b",
        temperature=0.3,  # Lower for fact-based responses
        max_tokens=800
    )
    
    # 5. Add source citations
    response_with_sources = {
        "content": response.content,
        "sources": [
            {
                "title": doc['metadata'].get('title', 'Unknown'),
                "source": doc['metadata']['source'],
                "relevance": doc['score']
            }
            for doc in docs
        ],
        "confidence": calculate_confidence(response, docs)
    }
    
    return response_with_sources
```

### 3. Multi-Turn Conversations

```python
class ConversationManager:
    """Manage multi-turn conversations with context"""
    
    def __init__(self, max_history=10):
        self.conversations = {}
        self.max_history = max_history
    
    def add_message(self, conversation_id, role, content):
        """Add message to conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
        
        # Trim old messages
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = \
                self.conversations[conversation_id][-self.max_history:]
    
    async def generate_response(self, conversation_id, user_message):
        """Generate contextual response"""
        self.add_message(conversation_id, "user", user_message)
        
        history = self.conversations[conversation_id]
        
        # Generate response with full context
        response = await generate_rag_response(
            user_message,
            conversation_history=history
        )
        
        self.add_message(conversation_id, "assistant", response['content'])
        
        return response

# Usage
conv_manager = ConversationManager()

response1 = await conv_manager.generate_response(
    "conv123",
    "What is machine learning?"
)

response2 = await conv_manager.generate_response(
    "conv123",
    "Can you give an example?"  # Refers to previous context
)
```

### 4. Function Calling / Tool Use

```python
# Define available tools
tools = [
    {
        "name": "search_documents",
        "description": "Search the knowledge base for relevant documents",
        "parameters": {
            "query": "string",
            "filters": "object (optional)"
        }
    },
    {
        "name": "create_ticket",
        "description": "Create a new ticket in the project management system",
        "parameters": {
            "title": "string",
            "description": "string",
            "priority": "string (low|medium|high)"
        }
    },
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "location": "string"
        }
    }
]

async def ai_with_tools(user_message, conversation_history=[]):
    """AI that can use tools"""
    
    # Build prompt with tool descriptions
    tools_desc = "\n".join([
        f"- {tool['name']}: {tool['description']}"
        for tool in tools
    ])
    
    prompt = f"""You are a helpful assistant with access to these tools:

{tools_desc}

To use a tool, respond in this format:
TOOL: tool_name
PARAMS: {{"param1": "value1", "param2": "value2"}}

User: {user_message}
Assistant:"""

    # Get AI response
    response = await ai_service.generate(prompt)
    
    # Check if AI wants to use a tool
    if "TOOL:" in response:
        tool_name = extract_tool_name(response)
        params = extract_params(response)
        
        # Execute tool
        result = await execute_tool(tool_name, params)
        
        # Generate final response with tool result
        final_prompt = f"""{prompt}

Tool result: {result}

Now provide a natural response to the user incorporating this result:"""
        
        final_response = await ai_service.generate(final_prompt)
        return final_response
    
    return response
```

## Performance Optimization

### 1. Caching Strategies

```python
from functools import lru_cache
import redis

# In-memory cache
@lru_cache(maxsize=1000)
def get_embedding_cached(text):
    """Cache embeddings for frequently used texts"""
    return embedding_model.encode(text)

# Redis cache for distributed systems
class EmbeddingCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)
        self.ttl = 86400  # 24 hours
    
    def get(self, text):
        key = f"emb:{hash(text)}"
        cached = self.redis.get(key)
        if cached:
            return pickle.loads(cached)
        return None
    
    def set(self, text, embedding):
        key = f"emb:{hash(text)}"
        self.redis.setex(
            key,
            self.ttl,
            pickle.dumps(embedding)
        )
    
    def get_or_compute(self, text):
        embedding = self.get(text)
        if embedding is None:
            embedding = embedding_model.encode(text)
            self.set(text, embedding)
        return embedding
```

### 2. Batch Processing

```python
async def process_batch(texts, batch_size=32):
    """Process texts in batches for efficiency"""
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        
        # Batch encode
        embeddings = embedding_model.encode(batch)
        
        results.extend(embeddings)
    
    return results
```

### 3. Async Operations

```python
import asyncio

async def parallel_rag_search(queries):
    """Search multiple queries in parallel"""
    rag = get_rag_service()
    
    # Create tasks
    tasks = [
        rag.search_async(query, top_k=5)
        for query in queries
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks)
    
    return results

# Usage
queries = [
    "What are the system requirements?",
    "How do I deploy to production?",
    "What is the architecture?"
]

results = await parallel_rag_search(queries)
```

## Troubleshooting

### Common Issues

#### 1. Slow AI Responses

```python
# Check model size
ollama list  # Use smaller models for speed

# Reduce max_tokens
response = ai_service.generate(prompt, max_tokens=200)

# Use GPU if available
OLLAMA_USE_GPU=true

# Use faster model
DEFAULT_MODEL=llama2:7b  # Instead of 13b
```

#### 2. Poor RAG Retrieval

```python
# Adjust chunk size
CHUNK_SIZE=500  # Smaller chunks for more precise matching

# Increase top_k
results = rag.search(query, top_k=10)  # Retrieve more candidates

# Lower similarity threshold
results = rag.search(query, min_score=0.6)  # From 0.7

# Try different embedding model
EMBEDDING_MODEL=all-mpnet-base-v2  # Higher quality
```

#### 3. Out of Memory

```python
# Reduce batch size
BATCH_SIZE=16  # From 32

# Limit concurrent processing
semaphore = asyncio.Semaphore(2)  # From 5

# Use smaller embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller memory footprint
```

## Next Steps

- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - Explore advanced system capabilities
- **[KNOWLEDGE_DATABASE.md](KNOWLEDGE_DATABASE.md)** - Deep dive into RAG system
- **[Examples](examples/)** - Practical code examples
- **[API Reference](docs/04-api-reference/README.md)** - Complete API documentation

---

**Need Help?** Check the [documentation](docs/) or [open an issue](https://github.com/Thomas-Heisig/chat_system/issues).
