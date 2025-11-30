# routes/dictionary.py
"""
📖 Dictionary Routes
API endpoints for dictionary and glossary management.

This is a placeholder for the planned dictionary routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from config.settings import settings, logger
from services.dictionary_service import get_dictionary_service

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])


@router.get("/status")
async def dictionary_status() -> Dict[str, Any]:
    """Get dictionary service status"""
    return {
        "service": "dictionary",
        "status": "placeholder",
        "feature_enabled": getattr(settings, 'FEATURE_DICTIONARY', True),
        "message": "Dictionary functionality is available in basic placeholder form"
    }


@router.post("/terms")
async def add_term(
    term: str,
    definition: str,
    category: str = None,
    examples: List[str] = None,
    synonyms: List[str] = None,
    related_terms: List[str] = None,
    language: str = "de"
) -> Dict[str, Any]:
    """Add a new term to the dictionary"""
    dictionary_service = get_dictionary_service()
    return await dictionary_service.add_term(
        term, definition, category, examples, synonyms, related_terms, language
    )


@router.get("/terms")
async def list_terms(
    category: str = None,
    limit: int = 50
) -> Dict[str, Any]:
    """List dictionary terms"""
    dictionary_service = get_dictionary_service()
    
    if category:
        terms = await dictionary_service.get_terms_by_category(category, limit)
    else:
        # Get all terms (limited)
        terms = list(dictionary_service.terms.values())[:limit]
    
    return {
        "items": terms,
        "total": len(terms)
    }


@router.get("/terms/{term_id}")
async def get_term(term_id: str) -> Dict[str, Any]:
    """Get a term by ID"""
    dictionary_service = get_dictionary_service()
    term = dictionary_service.terms.get(term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term


@router.get("/lookup/{term}")
async def lookup_term(term: str) -> Dict[str, Any]:
    """Look up a term by name"""
    dictionary_service = get_dictionary_service()
    result = await dictionary_service.lookup(term)
    if not result:
        raise HTTPException(status_code=404, detail="Term not found")
    return result


@router.put("/terms/{term_id}")
async def update_term(
    term_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Update a dictionary term"""
    dictionary_service = get_dictionary_service()
    return await dictionary_service.update_term(term_id, updates)


@router.delete("/terms/{term_id}")
async def delete_term(term_id: str) -> Dict[str, Any]:
    """Delete a dictionary term"""
    dictionary_service = get_dictionary_service()
    success = await dictionary_service.delete_term(term_id)
    return {"deleted": success, "term_id": term_id}


@router.get("/suggest")
async def suggest_terms(
    partial: str,
    limit: int = 10
) -> List[str]:
    """Get term suggestions for autocomplete"""
    dictionary_service = get_dictionary_service()
    return await dictionary_service.suggest(partial, limit)


@router.get("/search")
async def search_terms(
    query: str,
    category: str = None,
    language: str = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Search dictionary terms"""
    dictionary_service = get_dictionary_service()
    results = await dictionary_service.search_terms(query, category, language, limit)
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@router.get("/terms/{term_id}/related")
async def get_related_terms(term_id: str) -> List[Dict[str, Any]]:
    """Get related terms"""
    dictionary_service = get_dictionary_service()
    return await dictionary_service.get_related_terms(term_id)


@router.get("/categories")
async def get_categories() -> List[str]:
    """Get all dictionary categories"""
    dictionary_service = get_dictionary_service()
    return await dictionary_service.get_all_categories()


@router.get("/statistics")
async def get_statistics() -> Dict[str, Any]:
    """Get dictionary statistics"""
    dictionary_service = get_dictionary_service()
    return await dictionary_service.get_statistics()
