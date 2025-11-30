from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import uuid
from pathlib import Path

class MessageType(str, Enum):
    """Types of messages in the chat system"""
    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    COMMAND = "command"
    NOTIFICATION = "notification"

class AIModelType(str, Enum):
    """Types of AI models supported"""
    OLLAMA = "ollama"
    CUSTOM = "custom"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    ANTHROPIC = "anthropic"

class TicketStatus(str, Enum):
    """Ticket status options"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

class TicketPriority(str, Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketType(str, Enum):
    """Ticket types"""
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"
    INCIDENT = "incident"

class ProjectStatus(str, Enum):
    """Project status options"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    """User role types"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MANAGER = "manager"

class RoomRole(str, Enum):
    """Chat room role types"""
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"

class FileType(str, Enum):
    """File type categories"""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    CODE = "code"
    DATA = "data"
    OTHER = "other"

class BaseDatabaseModel(BaseModel):
    """Base model with common fields and configuration"""
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        populate_by_name=True,
        str_strip_whitespace=True
    )

class Message(BaseDatabaseModel):
    """Enhanced model for chat messages with AI and project support"""
    id: Optional[int] = Field(default=None, description="Unique message identifier")
    username: str = Field(..., min_length=1, max_length=100, description="User who sent the message")
    message: str = Field(..., min_length=1, max_length=10000, description="Message content")
    message_compressed: Optional[bytes] = Field(default=None, description="Compressed message content")
    timestamp: Optional[datetime] = Field(default=None, description="When the message was sent")
    message_type: MessageType = Field(default=MessageType.USER, description="Type of message")
    
    # Enhanced fields
    parent_id: Optional[int] = Field(default=None, description="Parent message for threads")
    room_id: Optional[str] = Field(default=None, description="Chat room/channel ID")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    ticket_id: Optional[str] = Field(default=None, description="Associated ticket ID")
    
    # AI-related fields
    is_ai_response: bool = Field(default=False, description="Whether this is an AI-generated response")
    ai_model_used: Optional[str] = Field(default=None, description="AI model used for generation")
    context_message_ids: List[int] = Field(default_factory=list, description="IDs of context messages")
    rag_sources: List[Dict[str, Any]] = Field(default_factory=list, description="RAG source documents")
    sentiment: Optional[Dict[str, Any]] = Field(default=None, description="Sentiment analysis results")
    
    # Message management
    is_edited: bool = Field(default=False, description="Whether message was edited")
    edit_history: List[Dict[str, Any]] = Field(default_factory=list, description="Edit history")
    reaction_count: int = Field(default=0, description="Number of reactions")
    flags: int = Field(default=0, description="Bit flags for pinned, deleted, etc.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        import re
        if not re.match(r'^[a-zA-Z0-9_\- .@]+$', v):
            raise ValueError('Username contains invalid characters')
        return v.strip()

    @validator('message')
    def validate_message_content(cls, v):
        """Validate message content"""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

    def __init__(self, **data):
        """Initialize message with automatic timestamp"""
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

    def to_websocket_format(self) -> Dict[str, Any]:
        """Convert to WebSocket-compatible format"""
        return {
            "type": "chat_message",
            "id": self.id,
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_type": self.message_type,
            "room_id": self.room_id,
            "project_id": self.project_id,
            "ticket_id": self.ticket_id,
            "is_ai_response": self.is_ai_response,
            "ai_model_used": self.ai_model_used,
            "is_edited": self.is_edited,
            "reaction_count": self.reaction_count,
            "metadata": self.metadata
        }

    def get_context_text(self) -> str:
        """Get message text for AI context"""
        return f"{self.username}: {self.message}"

    def add_reaction(self):
        """Increment reaction count"""
        self.reaction_count += 1

    def mark_edited(self, old_content: str, edit_reason: str = None):
        """Mark message as edited and add to history"""
        self.is_edited = True
        self.edit_history.append({
            "old_content": old_content,
            "new_content": self.message,
            "timestamp": datetime.now().isoformat(),
            "reason": edit_reason
        })

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "john_doe",
                "message": "Hello world!",
                "timestamp": "2024-01-01T12:00:00",
                "message_type": "user",
                "is_ai_response": False,
                "room_id": "general",
                "metadata": {}
            }
        }
    )

class MessageBatch(BaseDatabaseModel):
    """Batch of messages for efficient processing"""
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Batch identifier")
    created_at: Optional[datetime] = Field(default=None, description="Batch creation timestamp")
    total_messages: int = Field(default=0, description="Total messages in batch")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Batch metadata")

    def __init__(self, **data):
        """Initialize batch with timestamp and count"""
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        if 'messages' in data:
            data['total_messages'] = len(data['messages'])
        super().__init__(**data)

    def add_message(self, message: Message):
        """Add message to batch"""
        self.messages.append(message)
        self.total_messages = len(self.messages)

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch to dictionary"""
        return {
            "batch_id": self.batch_id,
            "total_messages": self.total_messages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "messages": [msg.model_dump() for msg in self.messages],  # Pydantic v2 kompatibel
            "metadata": self.metadata
        }

class User(BaseDatabaseModel):
    """User model for authentication and profile management"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique user ID")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User email address")
    password_hash: str = Field(..., description="Hashed password")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    avatar_url: Optional[str] = Field(default=None, description="Avatar URL")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    created_at: Optional[datetime] = Field(default=None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('username')
    def validate_username_format(cls, v):
        """Validate username format"""
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers and underscores')
        return v

    def __init__(self, **data):
        """Initialize user with timestamps"""
        now = datetime.now()
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = now
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = now
        super().__init__(**data)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now()

    def to_safe_dict(self) -> Dict[str, Any]:
        """Return user data without sensitive information"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "preferences": self.preferences
        }

# ... (Rest der Klassen bleiben gleich - Project, Ticket, File, etc.) ...

class Project(BaseDatabaseModel):
    """Project model for project management"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique project ID")
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    created_by: str = Field(..., description="User ID who created the project")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    due_date: Optional[datetime] = Field(default=None, description="Project due date")
    
    # Project details
    tags: List[str] = Field(default_factory=list, description="Project tags")
    members: List[str] = Field(default_factory=list, description="Project member user IDs")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Project settings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Statistics
    ticket_count: int = Field(default=0, description="Number of tickets")
    completed_ticket_count: int = Field(default=0, description="Number of completed tickets")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Project progress")

    def __init__(self, **data):
        """Initialize project with timestamps"""
        now = datetime.now()
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = now
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = now
        super().__init__(**data)

    def add_member(self, user_id: str):
        """Add member to project"""
        if user_id not in self.members:
            self.members.append(user_id)

    def remove_member(self, user_id: str):
        """Remove member from project"""
        if user_id in self.members:
            self.members.remove(user_id)

    def update_progress(self):
        """Update progress percentage"""
        if self.ticket_count > 0:
            self.progress_percentage = (self.completed_ticket_count / self.ticket_count) * 100
        else:
            self.progress_percentage = 0.0

class Ticket(BaseDatabaseModel):
    """Ticket model for issue tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ticket ID")
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: Optional[str] = Field(default=None, description="Ticket description")
    project_id: str = Field(..., description="Associated project ID")
    created_by: str = Field(..., description="User ID who created the ticket")
    assigned_to: Optional[str] = Field(default=None, description="Assigned user ID")
    
    # Ticket properties
    status: TicketStatus = Field(default=TicketStatus.OPEN, description="Ticket status")
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, description="Ticket priority")
    type: TicketType = Field(default=TicketType.TASK, description="Ticket type")
    
    # Dates
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(default=None, description="Resolution timestamp")
    
    # Time tracking
    estimated_hours: Optional[float] = Field(default=None, ge=0.0, description="Estimated hours")
    actual_hours: Optional[float] = Field(default=None, ge=0.0, description="Actual hours spent")
    
    # Relationships and metadata
    related_tickets: List[str] = Field(default_factory=list, description="Related ticket IDs")
    tags: List[str] = Field(default_factory=list, description="Ticket tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Statistics
    comment_count: int = Field(default=0, description="Number of comments")
    attachment_count: int = Field(default=0, description="Number of attachments")

    def __init__(self, **data):
        """Initialize ticket with timestamps"""
        now = datetime.now()
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = now
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = now
        super().__init__(**data)

    def mark_resolved(self):
        """Mark ticket as resolved"""
        self.status = TicketStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.updated_at = datetime.now()

    def reopen(self):
        """Reopen ticket"""
        self.status = TicketStatus.REOPENED
        self.resolved_at = None
        self.updated_at = datetime.now()

    def assign(self, user_id: str):
        """Assign ticket to user"""
        self.assigned_to = user_id
        self.updated_at = datetime.now()

class File(BaseDatabaseModel):
    """File model for uploaded files"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique file ID")
    original_filename: str = Field(..., description="Original filename")
    stored_filename: str = Field(..., description="Stored filename on server")
    file_path: str = Field(..., description="Full file path")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_hash: str = Field(..., description="MD5 file hash for deduplication")
    mime_type: str = Field(..., description="File MIME type")
    file_type: FileType = Field(..., description="File type category")
    
    # Ownership and context
    uploaded_by: str = Field(..., description="User ID who uploaded the file")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    ticket_id: Optional[str] = Field(default=None, description="Associated ticket ID")
    message_id: Optional[int] = Field(default=None, description="Associated message ID")
    
    # File metadata
    upload_date: Optional[datetime] = Field(default=None, description="Upload timestamp")
    description: Optional[str] = Field(default=None, description="File description")
    download_count: int = Field(default=0, description="Number of downloads")
    is_public: bool = Field(default=False, description="Whether file is publicly accessible")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="File tags")

    def __init__(self, **data):
        """Initialize file with upload timestamp"""
        if 'upload_date' not in data or data['upload_date'] is None:
            data['upload_date'] = datetime.now()
        super().__init__(**data)

    def increment_download(self):
        """Increment download count"""
        self.download_count += 1

    def get_file_extension(self) -> str:
        """Get file extension"""
        return Path(self.original_filename).suffix.lower()

    def to_download_dict(self) -> Dict[str, Any]:
        """Return file info for download"""
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "description": self.description,
            "download_url": f"/api/files/{self.id}/download"
        }

# ... (Rest der Klassen - ChatRoom, RoomMember, MessageReaction, AIConversation, AIModel) ...

class ChatRoom(BaseDatabaseModel):
    """Chat room/channel model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique room ID")
    name: str = Field(..., min_length=1, max_length=100, description="Room name")
    description: Optional[str] = Field(default=None, description="Room description")
    is_public: bool = Field(default=True, description="Whether room is public")
    created_by: str = Field(..., description="User ID who created the room")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    
    # Room statistics
    member_count: int = Field(default=0, description="Number of members")
    message_count: int = Field(default=0, description="Number of messages")
    
    # Room settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Room settings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Moderation
    allowed_roles: List[UserRole] = Field(default_factory=list, description="Allowed user roles")
    is_archived: bool = Field(default=False, description="Whether room is archived")

    def __init__(self, **data):
        """Initialize room with creation timestamp"""
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        super().__init__(**data)

    def can_user_join(self, user_role: UserRole) -> bool:
        """Check if user can join room based on role"""
        if self.is_public:
            return True
        return user_role in self.allowed_roles or user_role == UserRole.ADMIN

class RoomMember(BaseDatabaseModel):
    """Room membership model"""
    room_id: str = Field(..., description="Room ID")
    user_id: str = Field(..., description="User ID")
    role: RoomRole = Field(default=RoomRole.MEMBER, description="Member role")
    joined_at: Optional[datetime] = Field(default=None, description="Join timestamp")
    last_read_at: Optional[datetime] = Field(default=None, description="Last read timestamp")
    
    # Notification settings
    notifications_enabled: bool = Field(default=True, description="Whether notifications are enabled")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom member settings")

    def __init__(self, **data):
        """Initialize membership with join timestamp"""
        if 'joined_at' not in data or data['joined_at'] is None:
            data['joined_at'] = datetime.now()
        super().__init__(**data)

    def update_last_read(self):
        """Update last read timestamp"""
        self.last_read_at = datetime.now()

class MessageReaction(BaseDatabaseModel):
    """Message reaction model"""
    id: int = Field(default=None, description="Reaction ID")
    message_id: int = Field(..., description="Message ID")
    user_id: str = Field(..., description="User ID")
    reaction: str = Field(..., min_length=1, max_length=10, description="Reaction emoji or code")
    created_at: Optional[datetime] = Field(default=None, description="Reaction timestamp")

    def __init__(self, **data):
        """Initialize reaction with timestamp"""
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        super().__init__(**data)

class AIConversation(BaseDatabaseModel):
    """AI conversation context model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique conversation ID")
    title: str = Field(..., description="Conversation title")
    context: Optional[Dict[str, Any]] = Field(default=None, description="AI context data")
    message_count: int = Field(default=0, description="Number of messages")
    user_id: Optional[str] = Field(default=None, description="Associated user ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    is_archived: bool = Field(default=False, description="Whether conversation is archived")
    
    # AI settings
    ai_model: Optional[str] = Field(default=None, description="Preferred AI model")
    conversation_settings: Dict[str, Any] = Field(default_factory=dict, description="Conversation settings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def __init__(self, **data):
        """Initialize conversation with timestamps"""
        now = datetime.now()
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = now
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = now
        super().__init__(**data)

    def add_message(self):
        """Increment message count and update timestamp"""
        self.message_count += 1
        self.updated_at = datetime.now()

class AIModel(BaseDatabaseModel):
    """AI model configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique model ID")
    name: str = Field(..., description="Model name")
    model_type: AIModelType = Field(..., description="Model type")
    provider: str = Field(..., description="Model provider")
    config: Dict[str, Any] = Field(default_factory=dict, description="Model configuration")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    is_active: bool = Field(default=True, description="Whether model is active")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    cost_per_token: float = Field(default=0.0, description="Cost per token")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    def __init__(self, **data):
        """Initialize AI model with timestamps"""
        now = datetime.now()
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = now
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = now
        super().__init__(**data)

# Utility functions
def create_message(username: str, message: str, **kwargs) -> Message:
    """Factory function to create a new message"""
    return Message(username=username, message=message, **kwargs)

def create_ai_message(message: str, model_used: str, **kwargs) -> Message:
    """Factory function to create an AI message"""
    return Message(
        username="AI Assistant",
        message=message,
        message_type=MessageType.AI,
        is_ai_response=True,
        ai_model_used=model_used,
        **kwargs
    )

def create_user(username: str, email: str, password_hash: str, **kwargs) -> User:
    """Factory function to create a user"""
    return User(
        username=username,
        email=email,
        password_hash=password_hash,
        display_name=kwargs.pop('display_name', username),
        **kwargs
    )

def create_project(name: str, created_by: str, **kwargs) -> Project:
    """Factory function to create a project"""
    return Project(name=name, created_by=created_by, **kwargs)

def create_ticket(title: str, project_id: str, created_by: str, **kwargs) -> Ticket:
    """Factory function to create a ticket"""
    return Ticket(title=title, project_id=project_id, created_by=created_by, **kwargs)

def create_file(original_filename: str, stored_filename: str, file_path: str, 
                file_size: int, file_hash: str, mime_type: str, uploaded_by: str, **kwargs) -> File:
    """Factory function to create a file record"""
    # Determine file type from MIME type
    file_type = FileType.OTHER
    if mime_type.startswith('image/'):
        file_type = FileType.IMAGE
    elif mime_type.startswith('audio/'):
        file_type = FileType.AUDIO
    elif mime_type.startswith('video/'):
        file_type = FileType.VIDEO
    elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        file_type = FileType.DOCUMENT
    elif mime_type.startswith('text/') or 'code' in mime_type:
        file_type = FileType.CODE
    
    return File(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash,
        mime_type=mime_type,
        file_type=file_type,
        uploaded_by=uploaded_by,
        **kwargs
    )

# Search and filter models
class MessageFilter(BaseDatabaseModel):
    """Filter criteria for message queries"""
    username: Optional[str] = None
    message_type: Optional[MessageType] = None
    room_id: Optional[str] = None
    project_id: Optional[str] = None
    ticket_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contains_text: Optional[str] = None
    is_ai_response: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class ProjectFilter(BaseDatabaseModel):
    """Filter criteria for project queries"""
    status: Optional[ProjectStatus] = None
    created_by: Optional[str] = None
    member_id: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class TicketFilter(BaseDatabaseModel):
    """Filter criteria for ticket queries"""
    project_id: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    type: Optional[TicketType] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

# Response models
class PaginatedResponse(BaseDatabaseModel):
    """Paginated response model"""
    items: List[Any] = Field(default_factory=list)
    total: int = Field(default=0)
    page: int = Field(default=1)
    page_size: int = Field(default=50)
    total_pages: int = Field(default=0)

class SearchResults(BaseDatabaseModel):
    """Search results model"""
    messages: List[Message] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    tickets: List[Ticket] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)
    total_results: int = Field(default=0)

# WebSocket message models (separate for WebSocket communication)
class WebSocketMessage(BaseDatabaseModel):
    """WebSocket message model"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    user_id: Optional[str] = None
    room_id: Optional[str] = None
    username: Optional[str] = Field(default=None, description="Username for chat messages")
    message: Optional[str] = Field(default=None, description="Message content for chat messages")

class ChatMessageData(BaseDatabaseModel):
    """Chat message data for WebSocket"""
    message: Message
    room_id: Optional[str] = None
    project_id: Optional[str] = None

class TypingIndicatorData(BaseDatabaseModel):
    """Typing indicator data for WebSocket"""
    user_id: str
    username: str
    room_id: str
    is_typing: bool

# Pydantic v2 Forward References auflösen
Message.model_rebuild()
MessageBatch.model_rebuild()
User.model_rebuild()
Project.model_rebuild()
Ticket.model_rebuild()
File.model_rebuild()
ChatRoom.model_rebuild()
RoomMember.model_rebuild()
MessageReaction.model_rebuild()
AIConversation.model_rebuild()
AIModel.model_rebuild()
MessageFilter.model_rebuild()
ProjectFilter.model_rebuild()
TicketFilter.model_rebuild()
PaginatedResponse.model_rebuild()
SearchResults.model_rebuild()
WebSocketMessage.model_rebuild()
ChatMessageData.model_rebuild()
TypingIndicatorData.model_rebuild()