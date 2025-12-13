# ADR-016: Event Sourcing for Audit Trail

**Status:** Accepted  
**Date:** 2025-12-09  
**Decision Makers:** Architecture Team, Security Team, Compliance Team  
**Tags:** #event-sourcing #audit #compliance #architecture

---

## Context

The chat system needs comprehensive audit trails for compliance, debugging, and business intelligence. Current challenges with traditional CRUD approach:

1. **Lost History:** Updates overwrite previous values - no audit trail
2. **Debugging Difficulty:** Can't reconstruct state at specific point in time
3. **Compliance Requirements:** Need immutable record of all changes (GDPR, SOX, HIPAA)
4. **Complex Audit Logs:** Separate logging system disconnected from business logic
5. **Data Loss:** No way to recover from bad updates or bugs
6. **Analysis Limitations:** Can't replay history for business intelligence

### Current Architecture

```
┌─────────────┐
│   Command   │
│ (Update Msg)│
└──────┬──────┘
       │
       ▼
┌──────────────┐
│   Database   │  ← UPDATE message SET content = 'new'
│  (Overwrite) │     WHERE id = 123;
└──────────────┘
       │
       └──► Old data lost forever ❌
```

**Problems:**
- Previous content gone
- No who/when/why information
- Can't undo changes
- Can't time-travel debug
- Audit logs separate from data

### Requirements

1. **Immutability:** Never delete or modify historical data
2. **Complete Audit Trail:** Every change recorded with context
3. **Time Travel:** Reconstruct state at any point in time
4. **Compliance:** Meet regulatory requirements for data retention
5. **Debugging:** Replay events to understand bugs
6. **Business Intelligence:** Analyze patterns and trends
7. **Event-Driven:** Enable reactive architectures

---

## Decision

We will implement **Event Sourcing** pattern where all state changes are stored as immutable events in an Event Store, with read models (projections) for queries.

### 1. Core Architecture

**Event Sourcing Pattern:**

```
┌───────────────┐
│   Command     │
│ (Update Msg)  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Aggregate   │ ─────► Validate
│  (Message)    │        Business Rules
└───────┬───────┘
        │
        ▼ Emit
┌───────────────────────┐
│       Event           │
│ MessageContentUpdated │
│  - message_id         │
│  - old_content        │
│  - new_content        │
│  - user_id            │
│  - timestamp          │
│  - reason             │
└───────┬───────────────┘
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

### 2. Event Store Design

**Event Structure:**
```python
@dataclass
class BaseEvent:
    event_id: str          # UUID
    aggregate_id: str      # Entity ID
    aggregate_type: str    # "Message", "User", etc.
    event_type: str        # "MessageCreated", "MessageUpdated"
    timestamp: datetime    # When it happened
    version: int           # Optimistic locking
    user_id: str          # Who did it
    metadata: Dict        # Context (IP, user agent, etc.)
    data: Dict            # Event-specific payload
```

**Example Events:**
```python
MessageCreatedEvent(
    event_id="evt-123",
    aggregate_id="msg-456",
    event_type="MessageCreated",
    data={
        "content": "Hello world",
        "channel_id": "channel-1",
        "user_id": "user-789"
    }
)

MessageContentUpdatedEvent(
    event_id="evt-124",
    aggregate_id="msg-456",
    event_type="MessageContentUpdated",
    data={
        "old_content": "Hello world",
        "new_content": "Hello everyone",
        "reason": "typo fix"
    }
)
```

### 3. Event Store Technology

**Primary Option: PostgreSQL Event Store**
```sql
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    aggregate_id VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(100),
    metadata JSONB,
    data JSONB NOT NULL,
    UNIQUE(aggregate_id, version)
);

CREATE INDEX idx_events_aggregate ON events(aggregate_id);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_type ON events(event_type);
```

**Alternative: EventStoreDB**
- Purpose-built for event sourcing
- Optimized for append operations
- Built-in projections
- Higher learning curve and operational overhead

**Decision:** Use PostgreSQL for simplicity and existing expertise.

### 4. Aggregate Pattern

**Load Aggregate from Events:**
```python
class MessageAggregate:
    def __init__(self, message_id: str):
        self.id = message_id
        self.version = 0
        self.content = None
        self.created_at = None
        self.updated_at = None
    
    @classmethod
    async def load(cls, message_id: str) -> "MessageAggregate":
        aggregate = cls(message_id)
        events = await event_store.get_events(message_id)
        for event in events:
            aggregate.apply(event)
        return aggregate
    
    def apply(self, event: BaseEvent):
        """Apply event to update state."""
        if event.event_type == "MessageCreated":
            self.content = event.data["content"]
            self.created_at = event.timestamp
        elif event.event_type == "MessageContentUpdated":
            self.content = event.data["new_content"]
            self.updated_at = event.timestamp
        
        self.version = event.version
    
    def update_content(self, new_content: str, user_id: str) -> BaseEvent:
        """Create event for state change."""
        event = MessageContentUpdatedEvent(
            event_id=str(uuid4()),
            aggregate_id=self.id,
            version=self.version + 1,
            timestamp=datetime.now(),
            user_id=user_id,
            data={
                "old_content": self.content,
                "new_content": new_content
            }
        )
        self.apply(event)  # Apply locally
        return event  # Return for persistence
```

### 5. Projection Pattern (Read Models)

**Current State Projection:**
```python
class MessageProjection:
    """Read-optimized view of current message state."""
    
    async def handle_event(self, event: BaseEvent):
        if event.event_type == "MessageCreated":
            await db.execute("""
                INSERT INTO messages_current (id, content, created_at)
                VALUES ($1, $2, $3)
            """, event.aggregate_id, event.data["content"], event.timestamp)
        
        elif event.event_type == "MessageContentUpdated":
            await db.execute("""
                UPDATE messages_current
                SET content = $1, updated_at = $2
                WHERE id = $3
            """, event.data["new_content"], event.timestamp, event.aggregate_id)
```

**Multiple Projections:**
- Current state (optimized for queries)
- Audit trail view (compliance)
- Analytics view (business intelligence)
- Full-text search index
- Notification queue

### 6. Snapshot Optimization

**Performance Issue:** Loading 10,000 events to reconstruct state is slow.

**Solution:** Snapshots
```python
class MessageSnapshot:
    """Periodic snapshot of aggregate state."""
    
    aggregate_id: str
    version: int        # Event version at snapshot time
    timestamp: datetime
    state: Dict        # Complete aggregate state
```

**Snapshot Strategy:**
- Create snapshot every 100 events
- Load latest snapshot + subsequent events
- Dramatically reduces load time

```python
async def load_with_snapshot(aggregate_id: str):
    snapshot = await get_latest_snapshot(aggregate_id)
    aggregate = restore_from_snapshot(snapshot)
    
    events = await get_events_after(aggregate_id, snapshot.version)
    for event in events:
        aggregate.apply(event)
    
    return aggregate
```

---

## Consequences

### Positive

1. **Complete Audit Trail:** Every change recorded permanently
2. **Time Travel:** Reconstruct state at any point
3. **Debugging:** Replay events to reproduce bugs
4. **Compliance:** Immutable audit trail meets regulations
5. **Undo/Replay:** Can reverse or replay operations
6. **Business Intelligence:** Rich historical data for analysis
7. **Event-Driven:** Foundation for reactive architectures
8. **Bug Recovery:** Rebuild from events after fixing code
9. **Multiple Views:** Create projections for different use cases
10. **Scalability:** Read and write models scale independently

### Negative

1. **Complexity:** More complex than CRUD
2. **Learning Curve:** Team needs to learn event sourcing
3. **Storage:** Events accumulate (but cheap storage)
4. **Eventual Consistency:** Projections lag behind events
5. **Query Complexity:** Can't query events directly, need projections
6. **Schema Evolution:** Events must remain compatible forever
7. **Testing:** More complex testing scenarios
8. **Debugging:** Different debugging approach needed

### Neutral

1. **Event Versioning:** Need strategy for evolving events
2. **Projection Management:** Multiple projections to maintain
3. **Snapshot Strategy:** Need to determine snapshot frequency
4. **Archival:** Old events may need archival strategy

---

## Alternatives Considered

### Alternative 1: Traditional Audit Log Table

**Approach:** Separate table logging all changes

**Pros:**
- Simple to understand
- Familiar pattern
- Low complexity

**Cons:**
- Disconnected from business logic
- Can forget to log
- Can't reconstruct state
- Not source of truth

**Decision:** Rejected - doesn't provide time-travel or state reconstruction

---

### Alternative 2: Database Triggers for Audit

**Approach:** Use database triggers to log changes

**Pros:**
- Automatic logging
- Can't forget
- Database-level

**Cons:**
- Tightly coupled to schema
- Limited context (no business info)
- Hard to test
- Database-specific

**Decision:** Rejected - insufficient context and inflexible

---

### Alternative 3: Change Data Capture (CDC)

**Approach:** Use CDC tools (Debezium, etc.)

**Pros:**
- Captures all changes
- Works with existing schema
- No application changes

**Cons:**
- Technical changes only (no business context)
- Complex infrastructure
- Limited control over event structure

**Decision:** Rejected - lacks business semantics

---

### Alternative 4: Temporal Tables (SQL:2011)

**Approach:** Use database temporal features

**Pros:**
- Database-native
- Automatic history
- Simple queries

**Cons:**
- Database-specific
- Limited to table changes
- No business events
- Complex with relationships

**Decision:** Rejected - too limited, lacks business context

---

## Implementation

### Phase 1: Foundation (Estimated: 12 hours)

1. **Event Store Infrastructure:**
   - Create events table
   - Create snapshots table
   - Add indexes
   - Setup retention policies

2. **Base Event Classes:**
   - `BaseEvent` abstract class
   - Event serialization/deserialization
   - Event versioning support

3. **Event Store Repository:**
   - `append_event(event)`
   - `get_events(aggregate_id)`
   - `get_events_after(aggregate_id, version)`

### Phase 2: First Aggregate (Estimated: 10 hours)

1. **Message Aggregate:**
   - Define message events
   - Implement aggregate logic
   - Add validation
   - Write tests

2. **Message Projection:**
   - Current state projection
   - Event handlers
   - Database schema
   - Update logic

3. **Command Handlers:**
   - Create message command
   - Update message command
   - Delete message command

### Phase 3: Infrastructure (Estimated: 10 hours)

1. **Snapshot System:**
   - Snapshot creation
   - Snapshot loading
   - Automatic snapshot triggers

2. **Event Publishing:**
   - Publish events to message queue
   - Enable reactive subscribers
   - Event replay capability

3. **Projection Rebuild:**
   - Rebuild projections from events
   - Handle schema migrations
   - Progress tracking

---

## Event Schema Versioning

### Challenge
Events are permanent - how do we evolve them?

### Strategy

**1. Additive Changes Only:**
```python
# Version 1
MessageCreatedEvent {
    "content": str
}

# Version 2 - ADD field, don't remove
MessageCreatedEvent {
    "content": str,
    "content_type": str = "text"  # New, optional
}
```

**2. Event Upcasting:**
```python
class EventUpcaster:
    def upcast(self, event: Dict) -> Dict:
        if event["version"] == 1:
            event["content_type"] = "text"
            event["version"] = 2
        return event
```

**3. Multiple Event Versions:**
```python
# Keep both, convert between them
MessageCreatedEvent_V1
MessageCreatedEvent_V2

def handle_v1(event: MessageCreatedEvent_V1):
    return MessageCreatedEvent_V2(
        content=event.content,
        content_type="text"
    )
```

---

## Security and Compliance

### GDPR Compliance

**Right to be Forgotten:**
```python
# Pseudonymization approach
UserDeletedEvent {
    "user_id": "user-123",
    "anonymization_key": "anon-456"
}

# Subsequent events reference anonymized ID
MessageCreatedEvent {
    "user_id": "anon-456",  # Anonymized
    "content": "[redacted]"  # Content removed
}
```

**Encryption:**
- Encrypt sensitive data in events
- Maintain encryption keys separately
- Allow key rotation

### Access Control

```python
@require_permission("audit.read")
async def get_event_history(aggregate_id: str):
    return await event_store.get_events(aggregate_id)
```

---

## Monitoring and Observability

### Key Metrics

1. **Event Store:**
   - Events written per second
   - Event store latency
   - Storage growth rate

2. **Projections:**
   - Projection lag (time behind events)
   - Projection failures
   - Rebuild duration

3. **Aggregates:**
   - Aggregate load time
   - Snapshot hit rate
   - Events per aggregate

### Alerting

- Critical: Projection lag > 5 seconds
- Warning: Event write failures
- Info: Snapshot creation

---

## Testing Strategy

### 1. Event Store Tests
```python
async def test_event_append():
    event = MessageCreatedEvent(...)
    await event_store.append(event)
    events = await event_store.get_events(event.aggregate_id)
    assert len(events) == 1
```

### 2. Aggregate Tests
```python
def test_aggregate_state():
    aggregate = MessageAggregate("msg-123")
    aggregate.apply(MessageCreatedEvent(...))
    aggregate.apply(MessageContentUpdatedEvent(...))
    assert aggregate.content == "updated content"
```

### 3. Projection Tests
```python
async def test_projection():
    projection = MessageProjection()
    await projection.handle(MessageCreatedEvent(...))
    msg = await db.get_message("msg-123")
    assert msg is not None
```

### 4. Time Travel Tests
```python
async def test_time_travel():
    aggregate = await load_at_timestamp(
        "msg-123",
        datetime(2025, 1, 1)
    )
    assert aggregate.content == "old content"
```

---

## Migration Path

### Phase 1: Parallel Operation (Month 1)
- Deploy event sourcing for new messages only
- Keep CRUD for existing messages
- Monitor and learn

### Phase 2: Selective Migration (Month 2-3)
- Migrate critical entities to event sourcing
- Keep audit-critical data in events
- Less critical data stays CRUD

### Phase 3: Full Migration (Month 4+)
- Generate events from existing data
- Migrate remaining entities
- Deprecate direct database writes

---

## Success Criteria

1. **Audit Trail:** 100% of changes captured in events
2. **Performance:** < 10ms to append event
3. **Compliance:** Pass audit requirements
4. **Debugging:** Can reproduce any bug from events
5. **Time Travel:** Can reconstruct state at any point
6. **Reliability:** Zero event loss

---

## Approval

**Approved By:**
- Chief Technology Officer
- Head of Security
- Compliance Officer
- Lead Architect

**Date:** 2025-12-09

---

## References

- [Event Sourcing Pattern - Martin Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Journey - Microsoft](https://docs.microsoft.com/en-us/previous-versions/msp-n-p/jj554200(v=pandp.10))
- [EVENT_SOURCING.md](../EVENT_SOURCING.md) - Implementation Guide
- Implementation: `event_sourcing/event_store.py`, `event_sourcing/aggregates/`

---

## Related ADRs

- ADR-013: Database Read Replicas (for projection performance)
- [ADR-007: Multi-Database Support](../05-architecture/adr/ADR-007-multi-database-support.md) (event store can use different DB)
- Future: CQRS pattern (natural fit with event sourcing)

---

**Last Updated:** 2025-12-09  
**Next Review:** Q4 2026 (after 1 year in production)
