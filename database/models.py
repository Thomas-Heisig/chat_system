"""
Database models for the chat system.

TODO: This is a stub file. Implement complete models in production.
"""

from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    AI = "ai"


class Message:
    """
    Message model.
    
    TODO: Replace with proper ORM model (SQLAlchemy, etc.)
    """
    
    def __init__(
        self,
        id: Optional[int] = None,
        username: str = "",
        message: str = "",
        message_type: MessageType = MessageType.TEXT,
        timestamp: Optional[datetime] = None,
        room_id: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        self.id = id
        self.username = username
        self.message = message
        self.message_type = message_type
        self.timestamp = timestamp or datetime.now()
        self.room_id = room_id
        self.user_id = user_id
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "message": self.message,
            "message_type": self.message_type.value if isinstance(self.message_type, MessageType) else self.message_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "room_id": self.room_id,
            "user_id": self.user_id
        }


class User:
    """
    User model.
    
    TODO: Replace with proper ORM model.
    """
    
    def __init__(
        self,
        id: Optional[int] = None,
        username: str = "",
        email: str = "",
        password_hash: str = "",
        is_active: bool = True,
        is_admin: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        """Convert to dictionary (exclude password)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Room:
    """
    Room model for chat rooms.
    
    TODO: Replace with proper ORM model.
    """
    
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        description: str = "",
        is_private: bool = False,
        created_by: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.is_private = is_private
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_private": self.is_private,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
