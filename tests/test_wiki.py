"""
Tests for Wiki Service
"""

import pytest
from services.wiki_service import WikiService, get_wiki_service


@pytest.fixture
def wiki_service():
    """Get wiki service instance"""
    return WikiService()


@pytest.mark.asyncio
async def test_create_page(wiki_service):
    """Test creating a wiki page"""
    result = await wiki_service.create_page(
        title="Test Page",
        content="This is test content",
        author="test_user",
        category="testing",
        tags=["test", "example"]
    )
    
    assert result is not None
    assert result["title"] == "Test Page"
    assert result["content"] == "This is test content"
    assert result["author"] == "test_user"
    assert result["version"] == 1
    assert "status" in result


@pytest.mark.asyncio
async def test_get_page(wiki_service):
    """Test getting a wiki page"""
    # Create a page
    created = await wiki_service.create_page(
        title="Get Test",
        content="Content",
        author="user"
    )
    
    page_id = created["id"]
    
    # Get the page
    result = await wiki_service.get_page(page_id)
    
    assert result is not None
    assert result["id"] == page_id
    assert result["title"] == "Get Test"


@pytest.mark.asyncio
async def test_get_page_by_title(wiki_service):
    """Test getting a page by title"""
    await wiki_service.create_page(
        title="Unique Title",
        content="Content",
        author="user"
    )
    
    result = await wiki_service.get_page_by_title("Unique Title")
    
    assert result is not None
    assert result["title"] == "Unique Title"


@pytest.mark.asyncio
async def test_update_page(wiki_service):
    """Test updating a wiki page"""
    # Create page
    created = await wiki_service.create_page(
        title="Update Test",
        content="Original content",
        author="user"
    )
    
    page_id = created["id"]
    
    # Update page
    result = await wiki_service.update_page(
        page_id=page_id,
        content="Updated content",
        editor="editor",
        comment="Updated for testing"
    )
    
    assert result["content"] == "Updated content"
    assert result["version"] == 2
    assert result["last_editor"] == "editor"


@pytest.mark.asyncio
async def test_page_history(wiki_service):
    """Test page version history"""
    # Create and update page
    created = await wiki_service.create_page(
        title="History Test",
        content="Version 1",
        author="user"
    )
    
    page_id = created["id"]
    
    await wiki_service.update_page(page_id, "Version 2", "user")
    await wiki_service.update_page(page_id, "Version 3", "user")
    
    # Get history
    history = await wiki_service.get_page_history(page_id)
    
    assert len(history) >= 2  # At least 2 versions stored


@pytest.mark.asyncio
async def test_search_pages(wiki_service):
    """Test searching wiki pages"""
    # Create pages
    await wiki_service.create_page(
        "Docker Guide",
        "Docker is a container platform",
        "user",
        category="devops"
    )
    await wiki_service.create_page(
        "Kubernetes Guide",
        "Kubernetes orchestrates containers",
        "user",
        category="devops"
    )
    
    # Search
    results = await wiki_service.search("container")
    
    assert len(results) >= 2
    assert any("Docker" in r["title"] for r in results)


@pytest.mark.asyncio
async def test_delete_page(wiki_service):
    """Test deleting a wiki page"""
    # Create page
    created = await wiki_service.create_page(
        "Delete Test",
        "To be deleted",
        "user"
    )
    
    page_id = created["id"]
    
    # Delete
    result = await wiki_service.delete_page(page_id)
    assert result is True
    
    # Verify deleted
    page = await wiki_service.get_page(page_id)
    assert page is None


@pytest.mark.asyncio
async def test_get_recent_pages(wiki_service):
    """Test getting recent pages"""
    # Create pages
    await wiki_service.create_page("Page 1", "Content 1", "user")
    await wiki_service.create_page("Page 2", "Content 2", "user")
    await wiki_service.create_page("Page 3", "Content 3", "user")
    
    recent = await wiki_service.get_recent_pages(limit=2)
    
    assert len(recent) == 2


def test_singleton():
    """Test that get_wiki_service returns singleton"""
    service1 = get_wiki_service()
    service2 = get_wiki_service()
    
    assert service1 is service2
