"""
Tests for Elyza Service
"""

import pytest

from services.elyza_service import ElyzaService, Language, SentimentType, get_elyza_service


@pytest.fixture
def elyza_service():
    """Get elyza service instance"""
    return ElyzaService()


@pytest.mark.asyncio
async def test_generate_response_greeting(elyza_service):
    """Test generating response to greeting"""
    result = await elyza_service.generate_response("Hallo")

    assert result is not None
    assert "response" in result
    assert result["source"] == "elyza"
    assert result["fallback"] is True
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_generate_response_question(elyza_service):
    """Test generating response to question"""
    result = await elyza_service.generate_response("Wie geht es dir?")

    assert result is not None
    assert result["sentiment"] == SentimentType.QUESTION.value or result["sentiment"] == "question"
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_generate_response_thanks(elyza_service):
    """Test generating response to thanks"""
    result = await elyza_service.generate_response("Danke für die Hilfe")

    assert result is not None
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_generate_response_with_user_context(elyza_service):
    """Test generating response with user context"""
    user_id = "test_user_123"

    # First message
    result1 = await elyza_service.generate_response("Hallo", user_id=user_id)

    # Second message (should have context)
    result2 = await elyza_service.generate_response("Wie heißt du?", user_id=user_id)

    assert result1 is not None
    assert result2 is not None
    assert user_id in elyza_service.context


@pytest.mark.asyncio
async def test_generate_response_english(elyza_service):
    """Test generating response in English"""
    result = await elyza_service.generate_response("Hello", language=Language.ENGLISH)

    assert result is not None
    assert result["language"] == Language.ENGLISH.value


@pytest.mark.asyncio
async def test_sentiment_detection(elyza_service):
    """Test sentiment detection"""
    positive_sentiment = elyza_service._detect_sentiment("Das ist toll!")
    assert positive_sentiment == SentimentType.POSITIVE

    negative_sentiment = elyza_service._detect_sentiment("Das ist ein Problem")
    assert negative_sentiment == SentimentType.NEGATIVE

    question_sentiment = elyza_service._detect_sentiment("Was ist das?")
    assert question_sentiment == SentimentType.QUESTION


def test_is_available(elyza_service):
    """Test service availability check"""
    # Should be available by default if ENABLE_ELYZA_FALLBACK is true
    available = elyza_service.is_available()
    assert isinstance(available, bool)


def test_get_status(elyza_service):
    """Test getting service status"""
    status = elyza_service.get_status()

    assert "service" in status
    assert status["service"] == "elyza"
    assert "enabled" in status
    assert "pattern_count_de" in status
    assert "pattern_count_en" in status


def test_clear_context(elyza_service):
    """Test clearing user context"""
    user_id = "test_user_456"

    # Add some context
    elyza_service.context[user_id] = ["message1", "message2"]

    # Clear context
    result = elyza_service.clear_context(user_id)

    assert result is True
    assert user_id not in elyza_service.context


def test_singleton():
    """Test that get_elyza_service returns singleton"""
    service1 = get_elyza_service()
    service2 = get_elyza_service()

    assert service1 is service2


@pytest.mark.asyncio
async def test_fallback_response_generation(elyza_service):
    """Test fallback response for unmatched patterns"""
    result = await elyza_service.generate_response(
        "Some random unknown query that doesn't match any pattern"
    )

    assert result is not None
    assert result["source"] == "elyza"
    assert len(result["response"]) > 0
