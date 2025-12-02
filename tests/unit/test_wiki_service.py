"""Unit tests for WikiService."""
import pytest
from services.wiki_service import WikiService

class TestWikiService:
    @pytest.fixture
    def service(self):
        return WikiService()
    
    @pytest.mark.asyncio
    async def test_create_page(self, service):
        result = await service.create_page(
            title="Test Page",
            content="This is test content",
            author="test_user"
        )
        assert result is not None
        assert "title" in result
        assert result["title"] == "Test Page"
    
    @pytest.mark.asyncio
    async def test_get_page(self, service):
        result = await service.create_page("Test", "Content", "author")
        page_id = result.get("id")
        page = await service.get_page(page_id)
        assert page is not None
