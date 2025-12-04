# routes/devtools.py
"""
Chrome DevTools Support Routes
Provides endpoints to prevent 404 errors from Chrome DevTools.
"""

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["devtools"])


@router.get("/.well-known/appspecific/com.chrome.devtools.json")
async def devtools_json() -> Dict[str, Any]:
    """
    Return empty JSON for Chrome DevTools to prevent 404 errors.
    Chrome DevTools requests this endpoint when inspecting web applications.
    """
    return {}
