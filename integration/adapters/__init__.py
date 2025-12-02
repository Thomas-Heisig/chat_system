"""
Platform adapters for external integrations
"""

from .base_adapter import BaseAdapter
from .slack_adapter import SlackAdapter

__all__ = ['BaseAdapter', 'SlackAdapter']
