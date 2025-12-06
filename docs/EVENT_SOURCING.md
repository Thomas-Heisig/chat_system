# Event Sourcing for Audit Trail

## Overview

This document describes the Event Sourcing implementation for the Chat System, providing complete audit trails, time-travel debugging, and event-driven architecture capabilities. Event Sourcing stores all changes as immutable events rather than updating state directly.

## Configuration

### Environment Variables

```bash
# Event Sourcing Configuration
EVENT_SOURCING_ENABLED=false  # Enable event sourcing
EVENT_STORE_TYPE=postgresql  # postgresql, mongodb, eventstore
EVENT_STORE_URL=postgresql://user:pass@localhost:5432/events

# Event Store Settings
EVENT_STORE_RETENTION_DAYS=365  # Keep events for 1 year
EVENT_STORE_SNAPSHOT_INTERVAL=100  # Create snapshot every 100 events
EVENT_STORE_COMPRESSION_ENABLED=true  # Compress old events

# Event Publishing
EVENT_PUBLISH_TO_QUEUE=false  # Publish events to message queue
EVENT_QUEUE_URL=redis://localhost:6379/0  # Redis or RabbitMQ
```

### Settings in Code

```python
from config.settings import event_config

# Check event sourcing status
if event_config.enabled:
    store_type = event_config.store_type
    retention = event_config.retention_days
```

## Architecture

### Core Concepts

1. **Events**: Immutable facts about what happened
2. **Event Store**: Database of all events
3. **Aggregates**: Domain objects rebuilt from events
4. **Projections**: Read models built from events
5. **Snapshots**: Performance optimization for aggregates

```
┌───────────────┐
│   Command     │
│  (Create Msg) │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Aggregate   │ ─────► Validate
│  (Message)    │
└───────┬───────┘
        │
        ▼ Emit
┌───────────────┐
│     Event     │
│(MessageCreated)│
└───────┬───────┘
        │
        ├──────► ┌──────────────┐
        │        │ Event Store  │
        │        │  (Append)    │
        │        └──────────────┘
        │
        └──────► ┌──────────────┐
                 │  Projections │
                 │ (Read Models)│
                 └──────────────┘
```

## Implementation

### 1. Event Base Classes

**File:** `event_sourcing/events.py`

```python
"""Event sourcing base classes and events."""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from uuid import uuid4
import json


@dataclass
class BaseEvent:
    """Base class for all events."""
    event_id: str
    aggregate_id: str
    aggregate_type: str
    event_type: str
    timestamp: datetime
    version: int
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, aggregate_id: str, aggregate_type: str, **kwargs):
        """Create a new event with generated ID and timestamp."""
        return cls(
            event_id=str(uuid4()),
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=cls.__name__,
            timestamp=datetime.utcnow(),
            **kwargs
        )
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert event to JSON."""
        return json.dumps(self.to_dict())


# Message Events
@dataclass
class MessageCreatedEvent(BaseEvent):
    """Event emitted when message is created."""
    content: str
    username: str
    message_type: str
    
    def __post_init__(self):
        self.event_type = "MessageCreated"


@dataclass
class MessageUpdatedEvent(BaseEvent):
    """Event emitted when message is updated."""
    content: str
    
    def __post_init__(self):
        self.event_type = "MessageUpdated"


@dataclass
class MessageDeletedEvent(BaseEvent):
    """Event emitted when message is deleted."""
    
    def __post_init__(self):
        self.event_type = "MessageDeleted"


# User Events
@dataclass
class UserCreatedEvent(BaseEvent):
    """Event emitted when user is created."""
    username: str
    email: str
    role: str
    
    def __post_init__(self):
        self.event_type = "UserCreated"


@dataclass
class UserUpdatedEvent(BaseEvent):
    """Event emitted when user is updated."""
    updates: Dict[str, Any]
    
    def __post_init__(self):
        self.event_type = "UserUpdated"


# Project Events
@dataclass
class ProjectCreatedEvent(BaseEvent):
    """Event emitted when project is created."""
    name: str
    description: str
    owner_id: int
    
    def __post_init__(self):
        self.event_type = "ProjectCreated"


@dataclass
class ProjectStatusChangedEvent(BaseEvent):
    """Event emitted when project status changes."""
    old_status: str
    new_status: str
    
    def __post_init__(self):
        self.event_type = "ProjectStatusChanged"


# Ticket Events
@dataclass
class TicketCreatedEvent(BaseEvent):
    """Event emitted when ticket is created."""
    title: str
    description: str
    project_id: int
    priority: str
    
    def __post_init__(self):
        self.event_type = "TicketCreated"


@dataclass
class TicketAssignedEvent(BaseEvent):
    """Event emitted when ticket is assigned."""
    assigned_to: int
    assigned_by: int
    
    def __post_init__(self):
        self.event_type = "TicketAssigned"


@dataclass
class TicketStatusChangedEvent(BaseEvent):
    """Event emitted when ticket status changes."""
    old_status: str
    new_status: str
    
    def __post_init__(self):
        self.event_type = "TicketStatusChanged"
```

### 2. Event Store Implementation

**File:** `event_sourcing/event_store.py`

```python
"""Event store implementation for storing and retrieving events."""
from typing import List, Optional, Type
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

from database.session import Base, SessionLocal
from event_sourcing.events import BaseEvent

logger = logging.getLogger(__name__)


class EventStoreModel(Base):
    """Database model for event store."""
    __tablename__ = "event_store"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(36), unique=True, index=True, nullable=False)
    aggregate_id = Column(String(100), index=True, nullable=False)
    aggregate_type = Column(String(50), index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(100), nullable=True)
    event_data = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_aggregate_version', 'aggregate_id', 'version', unique=True),
        Index('idx_aggregate_type_timestamp', 'aggregate_type', 'timestamp'),
    )


class EventStore:
    """Event store for persisting and retrieving events."""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def append_event(self, event: BaseEvent) -> bool:
        """Append event to store."""
        try:
            event_record = EventStoreModel(
                event_id=event.event_id,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                event_type=event.event_type,
                version=event.version,
                timestamp=event.timestamp,
                user_id=event.user_id,
                event_data=event.to_json(),
                metadata=json.dumps(event.metadata) if event.metadata else None
            )
            self.db.add(event_record)
            self.db.commit()
            logger.info(f"Event appended: {event.event_type} for {event.aggregate_id}")
            return True
        except Exception as e:
            logger.error(f"Error appending event: {e}")
            self.db.rollback()
            return False
    
    def get_events_for_aggregate(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[dict]:
        """Get all events for an aggregate."""
        query = self.db.query(EventStoreModel).filter(
            EventStoreModel.aggregate_id == aggregate_id,
            EventStoreModel.version >= from_version
        )
        
        if to_version:
            query = query.filter(EventStoreModel.version <= to_version)
        
        events = query.order_by(EventStoreModel.version).all()
        return [json.loads(e.event_data) for e in events]
    
    def get_events_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get events by type."""
        query = self.db.query(EventStoreModel).filter(
            EventStoreModel.event_type == event_type
        )
        
        if since:
            query = query.filter(EventStoreModel.timestamp >= since)
        
        events = query.order_by(EventStoreModel.timestamp.desc()).limit(limit).all()
        return [json.loads(e.event_data) for e in events]
    
    def get_all_events(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[dict]:
        """Get all events with optional filtering."""
        query = self.db.query(EventStoreModel)
        
        if since:
            query = query.filter(EventStoreModel.timestamp >= since)
        if until:
            query = query.filter(EventStoreModel.timestamp <= until)
        
        events = query.order_by(EventStoreModel.timestamp).offset(offset).limit(limit).all()
        return [json.loads(e.event_data) for e in events]
    
    def get_aggregate_version(self, aggregate_id: str) -> int:
        """Get current version of aggregate."""
        result = self.db.query(EventStoreModel.version).filter(
            EventStoreModel.aggregate_id == aggregate_id
        ).order_by(EventStoreModel.version.desc()).first()
        
        return result[0] if result else 0
    
    def get_event_count(self, aggregate_id: Optional[str] = None) -> int:
        """Get total event count."""
        query = self.db.query(EventStoreModel)
        if aggregate_id:
            query = query.filter(EventStoreModel.aggregate_id == aggregate_id)
        return query.count()


# Global instance
event_store = EventStore()
```

### 3. Aggregate Base Class

**File:** `event_sourcing/aggregate.py`

```python
"""Base aggregate class for event sourcing."""
from typing import List, Optional
from abc import ABC, abstractmethod
from event_sourcing.events import BaseEvent
from event_sourcing.event_store import event_store
import logging

logger = logging.getLogger(__name__)


class Aggregate(ABC):
    """Base class for aggregates in event sourcing."""
    
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.uncommitted_events: List[BaseEvent] = []
    
    @abstractmethod
    def aggregate_type(self) -> str:
        """Return the aggregate type name."""
        pass
    
    def apply_event(self, event: BaseEvent, is_new: bool = True):
        """Apply event to aggregate state."""
        # Call specific handler method
        handler_name = f"_apply_{event.event_type}"
        if hasattr(self, handler_name):
            getattr(self, handler_name)(event)
            if is_new:
                self.uncommitted_events.append(event)
            self.version += 1
        else:
            logger.warning(f"No handler for event type: {event.event_type}")
    
    def load_from_history(self, events: List[dict]):
        """Rebuild aggregate from event history."""
        for event_data in events:
            # Reconstruct event object (simplified - needs proper deserialization)
            event = BaseEvent(**event_data)
            self.apply_event(event, is_new=False)
    
    def save(self) -> bool:
        """Save uncommitted events to event store."""
        for event in self.uncommitted_events:
            event.version = self.version
            event.aggregate_id = self.aggregate_id
            event.aggregate_type = self.aggregate_type()
            
            if not event_store.append_event(event):
                return False
        
        self.uncommitted_events = []
        return True
    
    @classmethod
    def load(cls, aggregate_id: str) -> Optional['Aggregate']:
        """Load aggregate from event store."""
        aggregate = cls(aggregate_id)
        events = event_store.get_events_for_aggregate(aggregate_id)
        if events:
            aggregate.load_from_history(events)
        return aggregate


class MessageAggregate(Aggregate):
    """Message aggregate for event sourcing."""
    
    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id)
        self.content = ""
        self.username = ""
        self.message_type = ""
        self.is_deleted = False
    
    def aggregate_type(self) -> str:
        return "Message"
    
    def create(self, content: str, username: str, message_type: str, user_id: str):
        """Create message."""
        from event_sourcing.events import MessageCreatedEvent
        event = MessageCreatedEvent(
            event_id="",  # Will be set when saving
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type(),
            event_type="MessageCreated",
            timestamp=None,  # Will be set
            version=self.version + 1,
            user_id=user_id,
            content=content,
            username=username,
            message_type=message_type
        )
        self.apply_event(event)
    
    def update(self, content: str, user_id: str):
        """Update message content."""
        from event_sourcing.events import MessageUpdatedEvent
        event = MessageUpdatedEvent(
            event_id="",
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type(),
            event_type="MessageUpdated",
            timestamp=None,
            version=self.version + 1,
            user_id=user_id,
            content=content
        )
        self.apply_event(event)
    
    def delete(self, user_id: str):
        """Delete message."""
        from event_sourcing.events import MessageDeletedEvent
        event = MessageDeletedEvent(
            event_id="",
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type(),
            event_type="MessageDeleted",
            timestamp=None,
            version=self.version + 1,
            user_id=user_id
        )
        self.apply_event(event)
    
    def _apply_MessageCreated(self, event):
        """Apply MessageCreated event."""
        self.content = event.content
        self.username = event.username
        self.message_type = event.message_type
    
    def _apply_MessageUpdated(self, event):
        """Apply MessageUpdated event."""
        self.content = event.content
    
    def _apply_MessageDeleted(self, event):
        """Apply MessageDeleted event."""
        self.is_deleted = True
```

### 4. Projections (Read Models)

**File:** `event_sourcing/projections.py`

```python
"""Projections - read models built from events."""
from typing import List
from sqlalchemy.orm import Session
from database.models import Message, User, Project, Ticket
from event_sourcing.event_store import event_store
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProjectionBuilder:
    """Build read models from events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def rebuild_all(self):
        """Rebuild all projections from events."""
        logger.info("Starting projection rebuild...")
        
        # Clear existing data
        self.db.query(Message).delete()
        self.db.commit()
        
        # Get all events
        events = event_store.get_all_events()
        
        # Process events
        for event_data in events:
            self.process_event(event_data)
        
        logger.info(f"Rebuilt projections from {len(events)} events")
    
    def process_event(self, event_data: dict):
        """Process single event and update read model."""
        event_type = event_data.get('event_type')
        
        if event_type == 'MessageCreated':
            self._handle_message_created(event_data)
        elif event_type == 'MessageUpdated':
            self._handle_message_updated(event_data)
        elif event_type == 'MessageDeleted':
            self._handle_message_deleted(event_data)
        # Add more handlers for other event types
    
    def _handle_message_created(self, event: dict):
        """Handle MessageCreated event."""
        message = Message(
            id=int(event['aggregate_id'].split('_')[1]),  # Extract ID
            content=event['content'],
            username=event['username'],
            message_type=event['message_type'],
            timestamp=datetime.fromisoformat(event['timestamp'])
        )
        self.db.merge(message)
        self.db.commit()
    
    def _handle_message_updated(self, event: dict):
        """Handle MessageUpdated event."""
        message_id = int(event['aggregate_id'].split('_')[1])
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            message.content = event['content']
            self.db.commit()
    
    def _handle_message_deleted(self, event: dict):
        """Handle MessageDeleted event."""
        message_id = int(event['aggregate_id'].split('_')[1])
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            self.db.delete(message)
            self.db.commit()
```

### 5. Integration with Routes

**File:** `routes/messages_eventsourced.py`

```python
"""Message routes using event sourcing."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db_write
from core.auth import get_current_user
from event_sourcing.aggregate import MessageAggregate
from event_sourcing.projections import ProjectionBuilder
from pydantic import BaseModel

router = APIRouter()


class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"


@router.post("/messages/eventsourced")
async def create_message_eventsourced(
    data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_write)
):
    """Create message using event sourcing."""
    # Generate aggregate ID
    aggregate_id = f"message_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Create aggregate
    message = MessageAggregate(aggregate_id)
    message.create(
        content=data.content,
        username=current_user["username"],
        message_type=data.message_type,
        user_id=str(current_user["id"])
    )
    
    # Save events
    if message.save():
        # Update projection
        projection_builder = ProjectionBuilder(db)
        for event in message.uncommitted_events:
            projection_builder.process_event(event.to_dict())
        
        return {
            "success": True,
            "aggregate_id": aggregate_id,
            "version": message.version
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save message")
```

## Use Cases

### 1. Complete Audit Trail

```python
# Get all changes to a message
def get_message_history(message_id: str) -> List[dict]:
    """Get complete history of message changes."""
    aggregate_id = f"message_{message_id}"
    events = event_store.get_events_for_aggregate(aggregate_id)
    return events

# Example output:
# [
#   {"event_type": "MessageCreated", "timestamp": "2024-01-01T10:00:00", ...},
#   {"event_type": "MessageUpdated", "timestamp": "2024-01-01T10:05:00", ...},
#   {"event_type": "MessageDeleted", "timestamp": "2024-01-01T10:10:00", ...}
# ]
```

### 2. Time Travel Debugging

```python
# Rebuild state at specific point in time
def get_state_at_time(aggregate_id: str, timestamp: datetime):
    """Get aggregate state at specific time."""
    events = event_store.get_events_for_aggregate(aggregate_id)
    
    # Filter events up to timestamp
    historical_events = [
        e for e in events
        if datetime.fromisoformat(e['timestamp']) <= timestamp
    ]
    
    # Rebuild aggregate
    aggregate = MessageAggregate(aggregate_id)
    aggregate.load_from_history(historical_events)
    return aggregate
```

### 3. Event Replay

```python
# Replay events to rebuild read models
def replay_events():
    """Replay all events to rebuild projections."""
    db = SessionLocal()
    builder = ProjectionBuilder(db)
    builder.rebuild_all()
```

## Monitoring

### Event Store Metrics

```python
from prometheus_client import Counter, Gauge

events_appended = Counter('events_appended_total', 'Total events appended', ['aggregate_type'])
events_processed = Counter('events_processed_total', 'Total events processed')
event_store_size = Gauge('event_store_size_bytes', 'Event store size in bytes')
```

### Health Check

```python
@router.get("/health/events")
async def event_store_health():
    """Check event store health."""
    count = event_store.get_event_count()
    return {
        "status": "healthy",
        "total_events": count,
        "oldest_event": "...",  # Query from DB
        "newest_event": "..."
    }
```

## Performance Optimization

### 1. Snapshots

Create snapshots to avoid replaying all events:

```python
class SnapshotStore:
    """Store aggregate snapshots for performance."""
    
    def save_snapshot(self, aggregate_id: str, state: dict, version: int):
        """Save aggregate snapshot."""
        # Save to database
        pass
    
    def load_snapshot(self, aggregate_id: str) -> Optional[dict]:
        """Load latest snapshot."""
        # Load from database
        pass

# Load with snapshot
def load_aggregate_optimized(aggregate_id: str):
    snapshot = snapshot_store.load_snapshot(aggregate_id)
    if snapshot:
        aggregate = MessageAggregate(aggregate_id)
        # Load snapshot state
        # Load events after snapshot
        events = event_store.get_events_for_aggregate(
            aggregate_id,
            from_version=snapshot['version']
        )
        aggregate.load_from_history(events)
        return aggregate
```

### 2. Event Compression

Compress old events to save space:

```python
import gzip

def compress_old_events(days_old: int = 90):
    """Compress events older than specified days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    # Query old events
    # Compress event_data field
    # Update in database
    pass
```

## Best Practices

1. **Event Immutability**: Never modify events after they're stored
2. **Event Versioning**: Version events for schema evolution
3. **Small Events**: Keep events focused and small
4. **Idempotency**: Handle duplicate events gracefully
5. **Backward Compatibility**: New event types should be additive
6. **Snapshot Strategy**: Snapshot frequently accessed aggregates
7. **Retention Policy**: Archive or delete old events
8. **Testing**: Test event handlers thoroughly

## References

- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [ADR-016: Event Sourcing for Audit Trail](adr/ADR-016-event-sourcing-audit-trail.md)
