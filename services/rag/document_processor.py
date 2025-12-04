# services/rag/document_processor.py
"""
Document Processor for RAG System
Handles document chunking, extraction, and preprocessing
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_rag import Document, DocumentType


@dataclass
class ChunkConfig:
    """Configuration for document chunking"""

    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    separator: str = "\n\n"
    word_based: bool = True


class DocumentProcessor:
    """
    Document processor for RAG system.
    Handles text extraction, chunking, and preprocessing.
    """

    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()

    def process_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None
    ) -> List[Document]:
        """
        Process raw text into document chunks.

        Args:
            text: Raw text content
            metadata: Optional metadata to attach to chunks
            doc_id: Optional document ID prefix

        Returns:
            List of Document objects
        """
        if not text or not text.strip():
            return []

        # Clean text
        text = self._clean_text(text)

        # Split into chunks
        chunks = self._chunk_text(text)

        # Create documents
        documents = []
        base_id = doc_id or str(uuid.uuid4())
        base_metadata = metadata or {}

        for i, chunk in enumerate(chunks):
            doc = Document(
                id=f"{base_id}_chunk_{i}",
                content=chunk,
                metadata={
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "parent_doc_id": base_id,
                },
                doc_type=DocumentType.TEXT,
                created_at=datetime.now(),
            )
            documents.append(doc)

        return documents

    def process_file(
        self, file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process a file into document chunks.

        Args:
            file_path: Path to the file
            metadata: Optional metadata

        Returns:
            List of Document objects
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type
        extension = path.suffix.lower()
        doc_type = self._get_doc_type(extension)

        # Extract text based on file type
        text = self._extract_text(file_path, extension)

        # Add file metadata
        file_metadata = {
            "filename": path.name,
            "file_path": str(path.absolute()),
            "file_extension": extension,
            "file_size": path.stat().st_size,
            "doc_type": doc_type.value,
            **(metadata or {}),
        }

        # Process text into chunks
        documents = self.process_text(text, file_metadata, doc_id=path.stem)

        # Update doc_type for all chunks
        for doc in documents:
            doc.doc_type = doc_type

        return documents

    def process_chat_messages(
        self, messages: List[Dict[str, Any]], window_size: int = 10
    ) -> List[Document]:
        """
        Process chat messages into searchable documents.

        Args:
            messages: List of message dicts with 'username', 'message', 'timestamp'
            window_size: Number of messages to group together

        Returns:
            List of Document objects
        """
        documents = []

        # Group messages into windows
        for i in range(0, len(messages), window_size):
            window = messages[i : i + window_size]

            # Combine messages in window
            content_parts = []
            for msg in window:
                username = msg.get("username", "Unknown")
                text = msg.get("message", "")
                content_parts.append(f"{username}: {text}")

            content = "\n".join(content_parts)

            # Get time range
            timestamps = [
                msg.get("timestamp") for msg in window if msg.get("timestamp") is not None
            ]
            valid_timestamps = [ts for ts in timestamps if ts is not None]
            start_time = min(valid_timestamps) if valid_timestamps else None
            end_time = max(valid_timestamps) if valid_timestamps else None

            doc = Document(
                id=f"chat_window_{i // window_size}",
                content=content,
                metadata={
                    "message_count": len(window),
                    "start_index": i,
                    "end_index": i + len(window),
                    "start_time": start_time,
                    "end_time": end_time,
                    "usernames": list(set(msg.get("username", "Unknown") for msg in window)),
                },
                doc_type=DocumentType.CHAT_MESSAGE,
                created_at=datetime.now(),
            )
            documents.append(doc)

        return documents

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        return text.strip()

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        chunks = []

        if self.config.word_based:
            chunks = self._chunk_by_words(text)
        else:
            chunks = self._chunk_by_characters(text)

        # Filter out chunks that are too small
        chunks = [c for c in chunks if len(c) >= self.config.min_chunk_size]

        return chunks

    def _chunk_by_words(self, text: str) -> List[str]:
        """Split text by words with overlap"""
        words = text.split()
        chunks = []

        # Calculate words per chunk (approximate)
        words_per_chunk = self.config.chunk_size // 5  # Average word length
        overlap_words = self.config.chunk_overlap // 5

        start = 0
        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            # Move start with overlap
            start = end - overlap_words
            if start >= len(words) - overlap_words:
                break

        return chunks

    def _chunk_by_characters(self, text: str) -> List[str]:
        """Split text by characters with overlap"""
        chunks = []

        start = 0
        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(".")
                if last_period > self.config.min_chunk_size:
                    chunk = chunk[: last_period + 1]
                    end = start + last_period + 1

            chunks.append(chunk)

            # Move start with overlap
            start = end - self.config.chunk_overlap
            if start >= len(text) - self.config.chunk_overlap:
                break

        return chunks

    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from file based on extension"""
        if extension in [".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif extension == ".pdf":
            return self._extract_pdf_text(file_path)

        elif extension in [".html", ".htm"]:
            return self._extract_html_text(file_path)

        else:
            # Try to read as text
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                raise ValueError(f"Unsupported file type: {extension}")

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            # Try PyPDF2
            import PyPDF2

            text = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n\n".join(text)
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF extraction. Install with: pip install PyPDF2"
            )

    def _extract_html_text(self, file_path: str) -> str:
        """Extract text from HTML file"""
        try:
            from bs4 import BeautifulSoup

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                # Remove scripts and styles
                for element in soup(["script", "style"]):
                    element.decompose()
                return soup.get_text(separator=" ", strip=True)
        except ImportError:
            # Fallback: simple regex
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
                # Remove tags
                text = re.sub(r"<[^>]+>", " ", html)
                return self._clean_text(text)

    def _get_doc_type(self, extension: str) -> DocumentType:
        """Determine document type from file extension"""
        type_map = {
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
            ".pdf": DocumentType.PDF,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
            ".py": DocumentType.CODE,
            ".js": DocumentType.CODE,
            ".ts": DocumentType.CODE,
            ".java": DocumentType.CODE,
            ".cpp": DocumentType.CODE,
            ".c": DocumentType.CODE,
            ".go": DocumentType.CODE,
            ".rs": DocumentType.CODE,
        }
        return type_map.get(extension.lower(), DocumentType.TEXT)


__all__ = ["DocumentProcessor", "ChunkConfig"]
