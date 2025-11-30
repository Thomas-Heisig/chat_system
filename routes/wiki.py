# routes/wiki.py
"""
📚 Wiki Routes
API endpoints for wiki and documentation management.

This is a placeholder for the planned wiki routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from config.settings import settings, logger
from services.wiki_service import get_wiki_service

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


@router.get("/status")
async def wiki_status() -> Dict[str, Any]:
    """Get wiki service status"""
    return {
        "service": "wiki",
        "status": "placeholder",
        "feature_enabled": getattr(settings, 'FEATURE_WIKI', True),
        "message": "Wiki functionality is available in basic placeholder form"
    }


@router.post("/pages")
async def create_page(
    title: str,
    content: str,
    author: str,
    category: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """Create a new wiki page"""
    wiki_service = get_wiki_service()
    return await wiki_service.create_page(title, content, author, category, tags)


@router.get("/pages")
async def list_pages(
    limit: int = 20,
    category: str = None
) -> Dict[str, Any]:
    """List wiki pages"""
    wiki_service = get_wiki_service()
    pages = await wiki_service.get_recent_pages(limit)
    return {
        "items": pages,
        "total": len(pages)
    }


@router.get("/pages/{page_id}")
async def get_page(page_id: str) -> Dict[str, Any]:
    """Get a wiki page by ID"""
    wiki_service = get_wiki_service()
    page = await wiki_service.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.put("/pages/{page_id}")
async def update_page(
    page_id: str,
    content: str,
    editor: str,
    comment: str = None
) -> Dict[str, Any]:
    """Update a wiki page"""
    wiki_service = get_wiki_service()
    return await wiki_service.update_page(page_id, content, editor, comment)


@router.delete("/pages/{page_id}")
async def delete_page(page_id: str) -> Dict[str, Any]:
    """Delete a wiki page"""
    wiki_service = get_wiki_service()
    success = await wiki_service.delete_page(page_id)
    return {"deleted": success, "page_id": page_id}


@router.get("/pages/{page_id}/history")
async def get_page_history(page_id: str) -> List[Dict[str, Any]]:
    """Get version history for a wiki page"""
    wiki_service = get_wiki_service()
    return await wiki_service.get_page_history(page_id)


@router.post("/pages/{page_id}/restore")
async def restore_page_version(
    page_id: str,
    version: int,
    editor: str
) -> Dict[str, Any]:
    """Restore a previous version of a wiki page"""
    wiki_service = get_wiki_service()
    return await wiki_service.restore_version(page_id, version, editor)


@router.get("/search")
async def search_wiki(
    query: str,
    category: str = None,
    tags: List[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Search wiki pages"""
    wiki_service = get_wiki_service()
    results = await wiki_service.search(query, category, tags, limit)
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@router.get("/categories")
async def get_categories() -> List[str]:
    """Get all wiki categories"""
    wiki_service = get_wiki_service()
    return await wiki_service.get_categories()


@router.get("/tags")
async def get_tags() -> List[str]:
    """Get all wiki tags"""
    wiki_service = get_wiki_service()
    return await wiki_service.get_all_tags()
