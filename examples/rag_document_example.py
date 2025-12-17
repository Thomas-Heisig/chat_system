#!/usr/bin/env python3
"""
RAG Document Processing Example

This script demonstrates how to use the RAG (Retrieval-Augmented Generation)
system for document processing and knowledge-based question answering, including:
- Uploading documents
- Document processing and chunking
- Semantic search
- RAG-enhanced AI responses
- Document management

Usage:
    python examples/rag_document_example.py

Requirements:
    - Chat system running with RAG enabled
    - Vector database configured (ChromaDB, Qdrant, or Pinecone)
    - Valid authentication token
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp  # noqa: E402


class RAGDocumentExample:
    """Example RAG document client"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authenticate(self, username: str, password: str) -> str:
        """Authenticate and get JWT token"""
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login", json={"username": username, "password": password}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.api_key = data["access_token"]
                print(f"✅ Authenticated as {username}")
                return self.api_key
            else:
                error = await response.text()
                raise Exception(f"Authentication failed: {error}")

    async def upload_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """Upload document for RAG processing"""

        if not self.api_key:
            raise Exception("Not authenticated")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Prepare multipart form data
        data = aiohttp.FormData()
        data.add_field(
            "file",
            open(file_path, "rb"),
            filename=file_path.name,
            content_type="application/octet-stream",
        )

        if title:
            data.add_field("title", title)
        if description:
            data.add_field("description", description)
        if tags:
            data.add_field("tags", ",".join(tags))

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.post(
            f"{self.base_url}/api/v1/rag/documents", data=data, headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Uploaded: {file_path.name}")
                print(f"   Document ID: {result['document_id']}")
                print(f"   Chunks: {result['chunks']}")
                return result
            else:
                error = await response.text()
                raise Exception(f"Upload failed: {error}")

    async def search_documents(
        self, query: str, top_k: int = 5, filters: Optional[dict] = None
    ) -> List[dict]:
        """Search documents using semantic search"""

        if not self.api_key:
            raise Exception("Not authenticated")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"query": query, "top_k": top_k}

        if filters:
            params["filters"] = filters

        async with self.session.get(
            f"{self.base_url}/api/v1/rag/search", params=params, headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["results"]
            else:
                error = await response.text()
                raise Exception(f"Search failed: {error}")

    async def ask_question(self, question: str, top_k: int = 5, model: str = "llama2") -> dict:
        """Ask question with RAG context"""

        if not self.api_key:
            raise Exception("Not authenticated")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        request_data = {"question": question, "top_k": top_k, "model": model}

        async with self.session.post(
            f"{self.base_url}/api/v1/rag/ask", json=request_data, headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                error = await response.text()
                raise Exception(f"Question failed: {error}")

    async def list_documents(self) -> List[dict]:
        """List all documents in RAG system"""

        if not self.api_key:
            raise Exception("Not authenticated")

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.get(
            f"{self.base_url}/api/v1/rag/documents", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["documents"]
            else:
                error = await response.text()
                raise Exception(f"List failed: {error}")

    async def delete_document(self, document_id: str):
        """Delete document from RAG system"""

        if not self.api_key:
            raise Exception("Not authenticated")

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.delete(
            f"{self.base_url}/api/v1/rag/documents/{document_id}", headers=headers
        ) as response:
            if response.status == 200:
                print(f"✅ Deleted document: {document_id}")
            else:
                error = await response.text()
                raise Exception(f"Delete failed: {error}")

    async def get_rag_stats(self) -> dict:
        """Get RAG system statistics"""

        if not self.api_key:
            raise Exception("Not authenticated")

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.get(
            f"{self.base_url}/api/v1/rag/stats", headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"Stats failed: {error}")


async def create_sample_document():
    """Create a sample document for testing"""

    sample_content = """
# Python Programming Guide

## Introduction
Python is a high-level, interpreted programming language known for its
simplicity and readability. It was created by Guido van Rossum and first
released in 1991.

## Key Features
- Easy to learn and use
- Extensive standard library
- Dynamic typing
- Cross-platform compatibility
- Strong community support

## Common Uses
1. Web Development (Django, Flask)
2. Data Science and Machine Learning (NumPy, Pandas, Scikit-learn)
3. Automation and Scripting
4. Scientific Computing
5. Artificial Intelligence

## Basic Syntax

### Variables
```python
name = "Alice"
age = 30
is_student = False
```

### Functions
```python
def greet(name):
    return f"Hello, {name}!"

result = greet("World")
print(result)
```

### Loops
```python
for i in range(5):
    print(i)

while condition:
    # do something
    pass
```

## Popular Frameworks
- Django: Full-featured web framework
- Flask: Lightweight web framework
- FastAPI: Modern API framework
- PyTorch: Deep learning framework
- TensorFlow: Machine learning platform

## Best Practices
1. Follow PEP 8 style guide
2. Write clear documentation
3. Use virtual environments
4. Write unit tests
5. Use type hints
"""

    # Create sample file
    sample_file = Path("/tmp/python_guide.md")
    with open(sample_file, "w") as f:
        f.write(sample_content)

    print(f"Created sample document: {sample_file}")
    return str(sample_file)


async def example_upload_document():
    """Example: Upload and process document"""
    print("\n" + "=" * 60)
    print("Example 1: Upload and Process Document")
    print("=" * 60 + "\n")

    async with RAGDocumentExample() as rag:
        await rag.authenticate("admin", "admin")

        # Create sample document
        sample_file = await create_sample_document()

        # Upload document
        result = await rag.upload_document(
            sample_file,
            title="Python Programming Guide",
            description="Comprehensive guide to Python programming",
            tags=["python", "programming", "tutorial"],
        )

        print("\n📄 Document processed:")
        print(f"   Chunks created: {result['chunks']}")
        print(f"   Embeddings generated: {result.get('embeddings', 'N/A')}")

        return result["document_id"]


async def example_semantic_search():
    """Example: Semantic search"""
    print("\n" + "=" * 60)
    print("Example 2: Semantic Search")
    print("=" * 60 + "\n")

    async with RAGDocumentExample() as rag:
        await rag.authenticate("admin", "admin")

        # Ensure document exists
        _ = await example_upload_document()  # Result used for side effects

        # Wait for processing
        await asyncio.sleep(2)

        # Search queries
        queries = [
            "What is Python used for?",
            "How do you define a function in Python?",
            "What are popular Python frameworks?",
        ]

        for query in queries:
            print(f"\n🔍 Query: {query}")
            results = await rag.search_documents(query, top_k=3)

            print(f"   Found {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"   [{i}] Score: {result['score']:.3f}")
                print(f"       {result['text'][:150]}...")
                print()


async def example_rag_qa():
    """Example: RAG-enhanced Q&A"""
    print("\n" + "=" * 60)
    print("Example 3: RAG-Enhanced Question Answering")
    print("=" * 60 + "\n")

    async with RAGDocumentExample() as rag:
        await rag.authenticate("admin", "admin")

        # Ensure document exists
        await example_upload_document()
        await asyncio.sleep(2)

        # Ask questions
        questions = [
            "What are the key features of Python?",
            "Give me an example of a Python function",
            "What frameworks are mentioned for web development?",
        ]

        for question in questions:
            print(f"\n❓ Question: {question}")
            print("   Thinking...", end="", flush=True)

            response = await rag.ask_question(question, top_k=5)

            print(f"\r   AI Answer: {response['answer']}\n")

            # Show sources
            if response.get("sources"):
                print("   📚 Sources:")
                for source in response["sources"]:
                    print(f"      - {source['title']} (relevance: {source['relevance']:.2f})")
                print()


async def example_document_management():
    """Example: Document management"""
    print("\n" + "=" * 60)
    print("Example 4: Document Management")
    print("=" * 60 + "\n")

    async with RAGDocumentExample() as rag:
        await rag.authenticate("admin", "admin")

        # Upload document
        _ = await example_upload_document()  # Result used for side effects
        await asyncio.sleep(1)

        # List documents
        print("\n📚 Listing all documents:")
        documents = await rag.list_documents()

        for doc in documents:
            print(f"\n   • {doc.get('title', 'Untitled')}")
            print(f"     ID: {doc['id']}")
            print(f"     Chunks: {doc.get('chunk_count', 'N/A')}")
            print(f"     Created: {doc.get('created_at', 'N/A')}")

        # Get statistics
        print("\n📊 RAG System Statistics:")
        stats = await rag.get_rag_stats()

        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Vector DB: {stats.get('vector_db_type', 'N/A')}")
        print(f"   Embedding model: {stats.get('embedding_model', 'N/A')}")


async def example_batch_upload():
    """Example: Batch document upload"""
    print("\n" + "=" * 60)
    print("Example 5: Batch Document Upload")
    print("=" * 60 + "\n")

    async with RAGDocumentExample() as rag:
        await rag.authenticate("admin", "admin")

        # Create multiple sample documents
        documents = []

        for i in range(3):
            content = f"""
# Document {i+1}

This is sample document number {i+1}.

## Section 1
Content for section 1 of document {i+1}.

## Section 2
More content with information about topic {i+1}.
"""
            file_path = f"/tmp/doc_{i+1}.md"
            with open(file_path, "w") as f:
                f.write(content)
            documents.append(file_path)

        # Upload in parallel
        print(f"📤 Uploading {len(documents)} documents...")

        tasks = [
            rag.upload_document(
                doc_path, title=f"Sample Document {i+1}", tags=["sample", f"doc{i+1}"]
            )
            for i, doc_path in enumerate(documents)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Report results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        print(f"\n✅ Successfully uploaded: {successful}/{len(documents)}")

        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"   ❌ Document {i}: {result}")
            else:
                print(f"   ✅ Document {i}: {result['chunks']} chunks")


async def interactive_rag():
    """Interactive RAG Q&A session"""
    print("\n" + "=" * 60)
    print("Interactive RAG Question Answering")
    print("=" * 60)
    print("\nCommands:")
    print("  /upload <file> - Upload document")
    print("  /list - List documents")
    print("  /stats - Show RAG statistics")
    print("  /search <query> - Search documents")
    print("  /quit - Exit")
    print("\n" + "=" * 60 + "\n")

    async with RAGDocumentExample() as rag:
        # Authenticate
        username = input("Username [admin]: ").strip() or "admin"
        password = input("Password [admin]: ").strip() or "admin"

        try:
            await rag.authenticate(username, password)
        except Exception as e:
            print(f"Authentication failed: {e}")
            return

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input[1:].split(maxsplit=1)
                    cmd = parts[0].lower()

                    if cmd == "quit":
                        print("Goodbye!")
                        break

                    elif cmd == "upload" and len(parts) > 1:
                        file_path = parts[1]
                        try:
                            result = await rag.upload_document(file_path)
                            print(f"✅ Uploaded: {result['chunks']} chunks created")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                        continue

                    elif cmd == "list":
                        documents = await rag.list_documents()
                        print(f"\n📚 Documents ({len(documents)}):")
                        for doc in documents:
                            print(f"   • {doc.get('title', 'Untitled')} - {doc['id']}")
                        continue

                    elif cmd == "stats":
                        stats = await rag.get_rag_stats()
                        print("\n📊 Statistics:")
                        for key, value in stats.items():
                            print(f"   {key}: {value}")
                        continue

                    elif cmd == "search" and len(parts) > 1:
                        query = parts[1]
                        results = await rag.search_documents(query, top_k=3)
                        print(f"\n🔍 Found {len(results)} results:")
                        for i, result in enumerate(results, 1):
                            print(f"\n[{i}] Score: {result['score']:.3f}")
                            print(f"    {result['text'][:200]}...")
                        continue

                    else:
                        print(f"Unknown command: /{cmd}")
                        continue

                # Ask question with RAG
                print("🤔 Thinking...", end="", flush=True)
                response = await rag.ask_question(user_input)
                print(f"\r💡 AI: {response['answer']}\n")

                # Show sources
                if response.get("sources"):
                    print("📚 Sources:")
                    for source in response["sources"][:3]:
                        print(f"   - {source.get('title', 'Unknown')}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


async def main():
    """Run all examples"""

    print("\n" + "=" * 60)
    print("RAG Document Processing Examples")
    print("Universal Chat System")
    print("=" * 60)

    # Check RAG is enabled
    print("\n⚙️  Checking RAG system...")

    # Menu
    print("\nSelect an example:")
    print("  1. Upload and Process Document")
    print("  2. Semantic Search")
    print("  3. RAG-Enhanced Q&A")
    print("  4. Document Management")
    print("  5. Batch Upload")
    print("  6. Interactive RAG Session")
    print("  7. Run All Examples")

    choice = input("\nEnter choice (1-7) [7]: ").strip() or "7"

    try:
        if choice == "1":
            await example_upload_document()
        elif choice == "2":
            await example_semantic_search()
        elif choice == "3":
            await example_rag_qa()
        elif choice == "4":
            await example_document_management()
        elif choice == "5":
            await example_batch_upload()
        elif choice == "6":
            await interactive_rag()
        elif choice == "7":
            await example_upload_document()
            await example_semantic_search()
            await example_rag_qa()
            await example_document_management()
            await example_batch_upload()
        else:
            print("Invalid choice")
            return

        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
