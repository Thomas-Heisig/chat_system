"""
Response Compression Middleware for FastAPI

This module provides response compression using Gzip and Brotli.
Automatically compresses responses based on client Accept-Encoding header.

Features:
- Gzip compression (widely supported)
- Brotli compression (better compression ratio, modern browsers)
- Configurable compression level
- Minimum size threshold
- Content-type filtering

Author: Chat System Team
Date: 2025-12-06
"""

import gzip
import io
from typing import Callable

try:
    import brotli

    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

from fastapi import Request, Response
from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress HTTP responses
    """

    # Content types that should be compressed
    COMPRESSIBLE_TYPES = {
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
        "text/javascript",
        "application/javascript",
        "application/x-javascript",
        "application/json",
        "application/xml",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
        "image/svg+xml",
    }

    def __init__(
        self,
        app,
        minimum_size: int = 500,
        gzip_level: int = 6,
        brotli_quality: int = 4,
    ):
        """
        Initialize compression middleware

        Args:
            app: The FastAPI application
            minimum_size: Minimum response size in bytes to compress (default 500)
            gzip_level: Gzip compression level 0-9 (default 6)
            brotli_quality: Brotli compression quality 0-11 (default 4)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.gzip_level = gzip_level
        self.brotli_quality = brotli_quality

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and compress response if appropriate

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response (possibly compressed)
        """
        # Get client's accepted encodings
        accept_encoding = request.headers.get("accept-encoding", "").lower()

        # Get the response
        response = await call_next(request)

        # Skip compression for certain conditions
        if not self._should_compress(response, accept_encoding):
            return response

        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Check if body meets minimum size requirement
        if len(body) < self.minimum_size:
            return self._create_response(response, body)

        # Compress with best available method
        if "br" in accept_encoding and BROTLI_AVAILABLE:
            # Brotli compression (better ratio)
            compressed_body = self._compress_brotli(body)
            encoding = "br"
        elif "gzip" in accept_encoding:
            # Gzip compression (widely supported)
            compressed_body = self._compress_gzip(body)
            encoding = "gzip"
        else:
            # No compression
            return self._create_response(response, body)

        # Only use compressed version if it's smaller
        if len(compressed_body) < len(body):
            response.headers["Content-Encoding"] = encoding
            response.headers["Content-Length"] = str(len(compressed_body))
            # Add Vary header to indicate compression depends on Accept-Encoding
            response.headers["Vary"] = "Accept-Encoding"
            return self._create_response(response, compressed_body)
        else:
            return self._create_response(response, body)

    def _should_compress(self, response: Response, accept_encoding: str) -> bool:
        """
        Determine if response should be compressed

        Args:
            response: The response to check
            accept_encoding: Client's Accept-Encoding header

        Returns:
            True if response should be compressed
        """
        # Don't compress if already compressed
        if "content-encoding" in response.headers:
            return False

        # Don't compress if no encoding is accepted
        if not accept_encoding or (
            "gzip" not in accept_encoding and "br" not in accept_encoding
        ):
            return False

        # Don't compress if it's not a compressible content type
        content_type = response.headers.get("content-type", "")
        # Extract base content type (before semicolon)
        base_content_type = content_type.split(";")[0].strip().lower()

        if base_content_type not in self.COMPRESSIBLE_TYPES:
            return False

        # Don't compress streaming responses
        if response.headers.get("transfer-encoding") == "chunked":
            return False

        return True

    def _compress_gzip(self, body: bytes) -> bytes:
        """
        Compress body using Gzip

        Args:
            body: The response body to compress

        Returns:
            Compressed body
        """
        buffer = io.BytesIO()
        with gzip.GzipFile(
            fileobj=buffer, mode="wb", compresslevel=self.gzip_level
        ) as gz:
            gz.write(body)
        return buffer.getvalue()

    def _compress_brotli(self, body: bytes) -> bytes:
        """
        Compress body using Brotli

        Args:
            body: The response body to compress

        Returns:
            Compressed body
        """
        if not BROTLI_AVAILABLE:
            raise RuntimeError("Brotli compression not available")

        return brotli.compress(body, quality=self.brotli_quality)

    def _create_response(self, original_response: Response, body: bytes) -> Response:
        """
        Create a new response with the given body

        Args:
            original_response: The original response
            body: The response body (possibly compressed)

        Returns:
            New response with updated body
        """
        return Response(
            content=body,
            status_code=original_response.status_code,
            headers=dict(original_response.headers),
            media_type=original_response.media_type,
        )
