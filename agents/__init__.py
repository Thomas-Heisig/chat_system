"""
🤖 Multi-Agent System Package

This package provides a comprehensive multi-agent architecture for the chat system,
enabling distributed AI processing, specialized agent capabilities, and coordinated workflows.
"""

from .core.orchestrator import AgentOrchestrator
from .core.registry import AgentRegistry
from .core.messaging import AgentMessage, MessageBus

__all__ = [
    'AgentOrchestrator',
    'AgentRegistry',
    'AgentMessage',
    'MessageBus'
]
