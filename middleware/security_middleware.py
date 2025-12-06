"""
Security Headers Middleware for FastAPI

This module implements comprehensive security headers including:
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security (HSTS)
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy

Author: Chat System Team
Date: 2025-12-06
"""

import secrets
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses
    """

    def __init__(self, app, enable_csp: bool = True, enable_hsts: bool = False):
        """
        Initialize security middleware

        Args:
            app: The FastAPI application
            enable_csp: Whether to enable Content Security Policy
            enable_hsts: Whether to enable HTTP Strict Transport Security (only for HTTPS)
        """
        super().__init__(app)
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts and settings.APP_ENVIRONMENT == "production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to response

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response with security headers added
        """
        # Generate nonce for CSP if enabled
        nonce = None
        if self.enable_csp:
            nonce = secrets.token_urlsafe(16)
            request.state.csp_nonce = nonce

        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response, nonce, request.url.path)

        return response

    def _add_security_headers(
        self, response: Response, nonce: str = None, path: str = "/"
    ):
        """
        Add comprehensive security headers to the response

        Args:
            response: The response object
            nonce: CSP nonce for inline scripts/styles
        """
        # Content Security Policy
        if self.enable_csp:
            csp_directives = self._build_csp_policy(nonce)
            response.headers["Content-Security-Policy"] = csp_directives

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = self._build_permissions_policy()

        # HTTP Strict Transport Security (HSTS) - only for production with HTTPS
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Disable DNS prefetching for privacy
        response.headers["X-DNS-Prefetch-Control"] = "off"

        # Prevent browser from caching sensitive API pages
        if "/api/" in path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

    def _build_csp_policy(self, nonce: str = None) -> str:
        """
        Build Content Security Policy directives

        Args:
            nonce: Nonce for inline scripts/styles

        Returns:
            CSP policy string
        """
        # Base CSP policy
        directives = [
            "default-src 'self'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]

        # Script sources
        script_sources = ["'self'"]
        if nonce:
            script_sources.append(f"'nonce-{nonce}'")
        if settings.APP_DEBUG:
            # Allow inline scripts in development for hot reload
            script_sources.append("'unsafe-inline'")
        directives.append(f"script-src {' '.join(script_sources)}")

        # Style sources
        style_sources = ["'self'"]
        if nonce:
            style_sources.append(f"'nonce-{nonce}'")
        if settings.APP_DEBUG:
            # Allow inline styles in development
            style_sources.append("'unsafe-inline'")
        directives.append(f"style-src {' '.join(style_sources)}")

        # Image sources (allow data: for inline images)
        directives.append("img-src 'self' data: https:")

        # Font sources
        directives.append("font-src 'self' data:")

        # Connect sources (for API calls and WebSocket)
        connect_sources = ["'self'"]
        if settings.WEBSOCKET_ENABLED:
            connect_sources.append("ws:")
            connect_sources.append("wss:")
        # Allow connections to AI services if enabled
        if settings.AI_ENABLED:
            if settings.OLLAMA_BASE_URL:
                connect_sources.append(settings.OLLAMA_BASE_URL)
        directives.append(f"connect-src {' '.join(connect_sources)}")

        # Media sources
        directives.append("media-src 'self'")

        # Object sources (block Flash, Java, etc.)
        directives.append("object-src 'none'")

        # Worker sources
        directives.append("worker-src 'self'")

        # Manifest sources
        directives.append("manifest-src 'self'")

        # Report violations in non-production environments
        if not settings.APP_ENVIRONMENT == "production":
            directives.append("report-uri /api/csp-report")

        # Upgrade insecure requests in production
        if settings.APP_ENVIRONMENT == "production":
            directives.append("upgrade-insecure-requests")

        return "; ".join(directives)

    def _build_permissions_policy(self) -> str:
        """
        Build Permissions Policy (formerly Feature-Policy)

        Returns:
            Permissions policy string
        """
        # Disable unnecessary browser features
        policies = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=()",
            "encrypted-media=()",
            "fullscreen=(self)",  # Allow fullscreen for own origin
            "picture-in-picture=()",
            "screen-wake-lock=()",
            "web-share=()",
        ]

        return ", ".join(policies)


def get_csp_nonce(request: Request) -> str:
    """
    Get the CSP nonce for the current request

    Args:
        request: The current request

    Returns:
        The CSP nonce string or empty string if not available
    """
    return getattr(request.state, "csp_nonce", "")
