"""
Tests for Dictionary Service
"""

import pytest

from services.dictionary_service import DictionaryService, get_dictionary_service


@pytest.fixture
def dictionary_service():
    """Get dictionary service instance"""
    return DictionaryService()


@pytest.mark.asyncio
async def test_add_term(dictionary_service):
    """Test adding a term to dictionary"""
    result = await dictionary_service.add_term(
        term="API",
        definition="Application Programming Interface",
        category="technology",
        examples=["REST API", "GraphQL API"],
        synonyms=["interface", "endpoint"],
    )

    assert result is not None
    assert result["term"] == "API"
    assert result["definition"] == "Application Programming Interface"
    assert result["category"] == "technology"
    assert len(result["examples"]) == 2
    assert "status" in result


@pytest.mark.asyncio
async def test_lookup_term(dictionary_service):
    """Test looking up a term"""
    # First add a term
    await dictionary_service.add_term(term="FastAPI", definition="Modern Python web framework")

    # Lookup the term
    result = await dictionary_service.lookup("FastAPI")

    assert result is not None
    assert result["term"] == "FastAPI"
    assert "definition" in result


@pytest.mark.asyncio
async def test_lookup_nonexistent_term(dictionary_service):
    """Test looking up a term that doesn't exist"""
    result = await dictionary_service.lookup("NonexistentTerm")

    assert result is None


@pytest.mark.asyncio
async def test_suggest_terms(dictionary_service):
    """Test term auto-completion"""
    # Add some terms
    await dictionary_service.add_term("Python", "Programming language")
    await dictionary_service.add_term("PyTest", "Testing framework")
    await dictionary_service.add_term("Pydantic", "Data validation")

    # Get suggestions
    suggestions = await dictionary_service.suggest("Py", limit=5)

    assert len(suggestions) >= 2
    assert all(s.lower().startswith("py") for s in suggestions)


@pytest.mark.asyncio
async def test_search_terms(dictionary_service):
    """Test searching for terms"""
    # Add terms
    await dictionary_service.add_term("Docker", "Container platform", category="devops")
    await dictionary_service.add_term("Kubernetes", "Container orchestration", category="devops")

    # Search by query
    results = await dictionary_service.search_terms("container")

    assert len(results) >= 2
    assert any("Docker" in r["term"] for r in results)


@pytest.mark.asyncio
async def test_get_statistics(dictionary_service):
    """Test getting dictionary statistics"""
    # Add some terms
    await dictionary_service.add_term("Term1", "Definition1", category="cat1")
    await dictionary_service.add_term("Term2", "Definition2", category="cat2")

    stats = await dictionary_service.get_statistics()

    assert "total_terms" in stats
    assert stats["total_terms"] >= 2
    assert "total_categories" in stats


def test_singleton():
    """Test that get_dictionary_service returns singleton"""
    service1 = get_dictionary_service()
    service2 = get_dictionary_service()

    assert service1 is service2
