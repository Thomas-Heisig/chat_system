"""Unit tests for DictionaryService."""
import pytest
from services.dictionary_service import DictionaryService

class TestDictionaryService:
    @pytest.fixture
    def service(self):
        return DictionaryService()
    
    @pytest.mark.asyncio
    async def test_add_term(self, service):
        result = await service.add_term(
            term="API",
            definition="Application Programming Interface",
            category="tech"
        )
        assert result is not None
        assert "term" in result
        assert result["term"] == "API"
    
    @pytest.mark.asyncio
    async def test_search_term(self, service):
        await service.add_term("API", "Application Programming Interface")
        results = await service.search_term("API")
        assert len(results) > 0
