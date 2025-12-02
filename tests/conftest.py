"""
Pytest configuration and shared fixtures for tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["APP_ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENABLE_ELYZA_FALLBACK"] = "true"


@pytest.fixture
def sample_message():
    """Sample message for testing."""
    return "Hello, how are you?"


@pytest.fixture
def sample_messages_list():
    """Sample list of messages for testing."""
    return [
        "Hello!",
        "How are you?",
        "What can you do?",
        "Thanks for your help"
    ]


@pytest.fixture
def mock_repository():
    """Mock repository for testing services."""
    from unittest.mock import Mock
    return Mock()
