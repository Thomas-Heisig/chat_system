# GraphQL API Gateway

## Overview

This document describes the GraphQL API implementation for the Chat System, providing a flexible and efficient alternative to the REST API. The GraphQL API runs in parallel with the existing REST API, allowing clients to choose the most suitable interface for their needs.

## Configuration

### Environment Variables

```bash
# GraphQL Configuration
GRAPHQL_ENABLED=false  # Enable GraphQL API
GRAPHQL_PATH=/graphql  # GraphQL endpoint path
GRAPHQL_PLAYGROUND_ENABLED=true  # Enable GraphQL Playground (disable in production)
GRAPHQL_INTROSPECTION_ENABLED=true  # Enable schema introspection (disable in production)

# GraphQL Features
GRAPHQL_SUBSCRIPTIONS_ENABLED=false  # Enable real-time subscriptions via WebSocket
GRAPHQL_DATALOADER_ENABLED=true  # Enable DataLoader for N+1 query optimization
GRAPHQL_QUERY_DEPTH_LIMIT=10  # Maximum query depth to prevent abuse
GRAPHQL_COMPLEXITY_LIMIT=1000  # Maximum query complexity score

# Performance
GRAPHQL_CACHE_ENABLED=true  # Enable query result caching
GRAPHQL_CACHE_TTL=300  # Cache TTL in seconds
GRAPHQL_BATCH_ENABLED=true  # Enable query batching
```

### Settings in Code

```python
from config.settings import api_config

# Check GraphQL status
if api_config.graphql_enabled:
    playground = api_config.graphql_playground_enabled
    path = api_config.graphql_path
```

## Architecture

### Technology Stack

**Recommended:** Strawberry GraphQL (Modern, type-safe, FastAPI integration)

**Alternative:** Ariadne (Schema-first approach)

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ├─────► /api/rest/* (REST API - existing)
       │
       └─────► /graphql (GraphQL API - new)
                   │
                   ├─► Queries (Read operations)
                   ├─► Mutations (Write operations)
                   └─► Subscriptions (Real-time)
                         │
                   ┌─────▼─────┐
                   │  Resolvers │
                   └─────┬─────┘
                         │
                   ┌─────▼─────┐
                   │  Services │
                   └─────┬─────┘
                         │
                   ┌─────▼─────┐
                   │  Database │
                   └───────────┘
```

## Implementation

### 1. Install Dependencies

```bash
pip install strawberry-graphql[fastapi]
pip install strawberry-graphql-django  # If using Django ORM features
```

Add to `requirements.txt`:
```txt
strawberry-graphql[fastapi]==0.214.0
```

### 2. GraphQL Schema Definition

**File:** `graphql_api/schema.py`

```python
"""GraphQL schema definition using Strawberry."""
import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class User:
    """User type."""
    id: int
    username: str
    email: str
    role: str
    created_at: datetime
    is_active: bool


@strawberry.type
class Message:
    """Message type."""
    id: int
    content: str
    username: str
    timestamp: datetime
    message_type: str
    
    @strawberry.field
    def user(self) -> Optional[User]:
        """Get user who sent the message."""
        # Resolved via DataLoader for efficiency
        return None  # Placeholder


@strawberry.type
class Project:
    """Project type."""
    id: int
    name: str
    description: Optional[str]
    status: str
    owner_id: int
    created_at: datetime
    
    @strawberry.field
    def owner(self) -> Optional[User]:
        """Get project owner."""
        return None  # Resolved via DataLoader


@strawberry.type
class Ticket:
    """Ticket type."""
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    project_id: int
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    def project(self) -> Optional[Project]:
        """Get associated project."""
        return None  # Resolved via DataLoader
    
    @strawberry.field
    def assignee(self) -> Optional[User]:
        """Get assigned user."""
        return None  # Resolved via DataLoader


@strawberry.input
class CreateUserInput:
    """Input for creating a user."""
    username: str
    email: str
    password: str
    role: str = "user"


@strawberry.input
class CreateMessageInput:
    """Input for creating a message."""
    content: str
    message_type: str = "text"


@strawberry.input
class UpdateTicketInput:
    """Input for updating a ticket."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None


@strawberry.type
class Query:
    """GraphQL queries (read operations)."""
    
    @strawberry.field
    async def users(self, limit: int = 10, offset: int = 0) -> List[User]:
        """Get list of users."""
        # Import here to avoid circular dependencies
        from graphql_api.resolvers import get_users
        return await get_users(limit, offset)
    
    @strawberry.field
    async def user(self, id: int) -> Optional[User]:
        """Get user by ID."""
        from graphql_api.resolvers import get_user
        return await get_user(id)
    
    @strawberry.field
    async def messages(
        self,
        limit: int = 50,
        offset: int = 0,
        username: Optional[str] = None
    ) -> List[Message]:
        """Get messages with optional filtering."""
        from graphql_api.resolvers import get_messages
        return await get_messages(limit, offset, username)
    
    @strawberry.field
    async def projects(self, limit: int = 10, offset: int = 0) -> List[Project]:
        """Get list of projects."""
        from graphql_api.resolvers import get_projects
        return await get_projects(limit, offset)
    
    @strawberry.field
    async def project(self, id: int) -> Optional[Project]:
        """Get project by ID."""
        from graphql_api.resolvers import get_project
        return await get_project(id)
    
    @strawberry.field
    async def tickets(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Ticket]:
        """Get tickets with optional filtering."""
        from graphql_api.resolvers import get_tickets
        return await get_tickets(project_id, status, limit, offset)


@strawberry.type
class Mutation:
    """GraphQL mutations (write operations)."""
    
    @strawberry.mutation
    async def create_user(self, input: CreateUserInput) -> User:
        """Create a new user."""
        from graphql_api.resolvers import create_user_resolver
        return await create_user_resolver(input)
    
    @strawberry.mutation
    async def create_message(self, input: CreateMessageInput, info: strawberry.Info) -> Message:
        """Create a new message."""
        from graphql_api.resolvers import create_message_resolver
        # Get current user from context
        current_user = info.context.get("current_user")
        return await create_message_resolver(input, current_user)
    
    @strawberry.mutation
    async def update_ticket(self, id: int, input: UpdateTicketInput) -> Ticket:
        """Update an existing ticket."""
        from graphql_api.resolvers import update_ticket_resolver
        return await update_ticket_resolver(id, input)
    
    @strawberry.mutation
    async def delete_ticket(self, id: int) -> bool:
        """Delete a ticket."""
        from graphql_api.resolvers import delete_ticket_resolver
        return await delete_ticket_resolver(id)


@strawberry.type
class Subscription:
    """GraphQL subscriptions (real-time updates)."""
    
    @strawberry.subscription
    async def message_added(self) -> Message:
        """Subscribe to new messages."""
        from graphql_api.resolvers import message_stream
        async for message in message_stream():
            yield message
    
    @strawberry.subscription
    async def ticket_updated(self, project_id: int) -> Ticket:
        """Subscribe to ticket updates for a project."""
        from graphql_api.resolvers import ticket_update_stream
        async for ticket in ticket_update_stream(project_id):
            yield ticket


# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
```

### 3. Resolvers Implementation

**File:** `graphql_api/resolvers.py`

```python
"""GraphQL resolvers - connect schema to data sources."""
from typing import List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from database.session import SessionLocal
from database.models import User as UserModel, Message as MessageModel
from database.models import Project as ProjectModel, Ticket as TicketModel
from graphql_api.schema import (
    User, Message, Project, Ticket,
    CreateUserInput, CreateMessageInput, UpdateTicketInput
)
from core.auth import get_password_hash
import asyncio


# Helper to get database session
def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Context manager will close


# User Resolvers
async def get_users(limit: int, offset: int) -> List[User]:
    """Get list of users."""
    db = get_db()
    users = db.query(UserModel).offset(offset).limit(limit).all()
    return [
        User(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role,
            created_at=u.created_at,
            is_active=u.is_active
        )
        for u in users
    ]


async def get_user(user_id: int) -> Optional[User]:
    """Get user by ID."""
    db = get_db()
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        return None
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        is_active=user.is_active
    )


async def create_user_resolver(input: CreateUserInput) -> User:
    """Create a new user."""
    db = get_db()
    user = UserModel(
        username=input.username,
        email=input.email,
        password_hash=get_password_hash(input.password),
        role=input.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        is_active=user.is_active
    )


# Message Resolvers
async def get_messages(
    limit: int,
    offset: int,
    username: Optional[str] = None
) -> List[Message]:
    """Get messages with optional filtering."""
    db = get_db()
    query = db.query(MessageModel)
    if username:
        query = query.filter(MessageModel.username == username)
    messages = query.order_by(MessageModel.timestamp.desc()).offset(offset).limit(limit).all()
    return [
        Message(
            id=m.id,
            content=m.content,
            username=m.username,
            timestamp=m.timestamp,
            message_type=m.message_type
        )
        for m in messages
    ]


async def create_message_resolver(
    input: CreateMessageInput,
    current_user: Optional[dict]
) -> Message:
    """Create a new message."""
    if not current_user:
        raise ValueError("Authentication required")
    
    db = get_db()
    message = MessageModel(
        content=input.content,
        username=current_user["username"],
        message_type=input.message_type
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return Message(
        id=message.id,
        content=message.content,
        username=message.username,
        timestamp=message.timestamp,
        message_type=message.message_type
    )


# Project Resolvers
async def get_projects(limit: int, offset: int) -> List[Project]:
    """Get list of projects."""
    db = get_db()
    projects = db.query(ProjectModel).offset(offset).limit(limit).all()
    return [
        Project(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            owner_id=p.owner_id,
            created_at=p.created_at
        )
        for p in projects
    ]


async def get_project(project_id: int) -> Optional[Project]:
    """Get project by ID."""
    db = get_db()
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        return None
    return Project(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        owner_id=project.owner_id,
        created_at=project.created_at
    )


# Ticket Resolvers
async def get_tickets(
    project_id: Optional[int],
    status: Optional[str],
    limit: int,
    offset: int
) -> List[Ticket]:
    """Get tickets with optional filtering."""
    db = get_db()
    query = db.query(TicketModel)
    if project_id:
        query = query.filter(TicketModel.project_id == project_id)
    if status:
        query = query.filter(TicketModel.status == status)
    tickets = query.offset(offset).limit(limit).all()
    return [
        Ticket(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            project_id=t.project_id,
            assigned_to=t.assigned_to,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in tickets
    ]


async def update_ticket_resolver(ticket_id: int, input: UpdateTicketInput) -> Ticket:
    """Update a ticket."""
    db = get_db()
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")
    
    if input.title is not None:
        ticket.title = input.title
    if input.description is not None:
        ticket.description = input.description
    if input.status is not None:
        ticket.status = input.status
    if input.priority is not None:
        ticket.priority = input.priority
    if input.assigned_to is not None:
        ticket.assigned_to = input.assigned_to
    
    db.commit()
    db.refresh(ticket)
    return Ticket(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        project_id=ticket.project_id,
        assigned_to=ticket.assigned_to,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )


async def delete_ticket_resolver(ticket_id: int) -> bool:
    """Delete a ticket."""
    db = get_db()
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if not ticket:
        return False
    db.delete(ticket)
    db.commit()
    return True


# Subscription Resolvers
async def message_stream() -> AsyncGenerator[Message, None]:
    """Stream new messages (placeholder - integrate with WebSocket)."""
    # In real implementation, connect to WebSocket broadcast or Redis Pub/Sub
    while True:
        await asyncio.sleep(1)
        # Yield new messages as they arrive
        yield Message(
            id=0,
            content="Sample message",
            username="system",
            timestamp=datetime.now(),
            message_type="text"
        )


async def ticket_update_stream(project_id: int) -> AsyncGenerator[Ticket, None]:
    """Stream ticket updates for a project."""
    # In real implementation, connect to event stream
    while True:
        await asyncio.sleep(1)
        # Yield ticket updates as they occur
        yield Ticket(
            id=0,
            title="Sample ticket",
            description="",
            status="open",
            priority="medium",
            project_id=project_id,
            assigned_to=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
```

### 4. DataLoader for N+1 Query Optimization

**File:** `graphql_api/dataloaders.py`

```python
"""DataLoaders to solve N+1 query problem."""
from strawberry.dataloader import DataLoader
from typing import List
from database.session import SessionLocal
from database.models import User as UserModel, Project as ProjectModel


async def load_users(keys: List[int]) -> List[UserModel]:
    """Batch load users by IDs."""
    db = SessionLocal()
    users = db.query(UserModel).filter(UserModel.id.in_(keys)).all()
    user_map = {user.id: user for user in users}
    return [user_map.get(key) for key in keys]


async def load_projects(keys: List[int]) -> List[ProjectModel]:
    """Batch load projects by IDs."""
    db = SessionLocal()
    projects = db.query(ProjectModel).filter(ProjectModel.id.in_(keys)).all()
    project_map = {project.id: project for project in projects}
    return [project_map.get(key) for key in keys]


# Create DataLoader instances
user_loader = DataLoader(load_fn=load_users)
project_loader = DataLoader(load_fn=load_projects)
```

### 5. FastAPI Integration

**File:** `main.py` (add to existing file)

```python
from strawberry.fastapi import GraphQLRouter
from graphql_api.schema import schema
from config.settings import api_config

# GraphQL endpoint
if api_config.graphql_enabled:
    graphql_app = GraphQLRouter(
        schema,
        graphiql=api_config.graphql_playground_enabled,
        context_getter=lambda: {"current_user": None}  # Add auth context
    )
    app.include_router(graphql_app, prefix="/graphql")
```

### 6. Authentication Integration

```python
from core.auth import get_current_user_optional

async def get_context(request):
    """Build GraphQL context with authentication."""
    user = await get_current_user_optional(request)
    return {
        "current_user": user,
        "request": request,
        "user_loader": user_loader,
        "project_loader": project_loader
    }

# Update GraphQL router
graphql_app = GraphQLRouter(
    schema,
    graphiql=api_config.graphql_playground_enabled,
    context_getter=get_context
)
```

## Usage Examples

### Query Examples

```graphql
# Get users
query GetUsers {
  users(limit: 10, offset: 0) {
    id
    username
    email
    role
    createdAt
  }
}

# Get messages with user information
query GetMessages {
  messages(limit: 20) {
    id
    content
    timestamp
    user {
      username
      email
    }
  }
}

# Get project with tickets
query GetProjectWithTickets {
  project(id: 1) {
    id
    name
    description
    owner {
      username
    }
  }
  tickets(projectId: 1) {
    id
    title
    status
    priority
    assignee {
      username
    }
  }
}

# Complex nested query
query ComplexQuery {
  projects(limit: 5) {
    id
    name
    owner {
      username
      email
    }
  }
  users(limit: 10) {
    id
    username
  }
}
```

### Mutation Examples

```graphql
# Create user
mutation CreateUser {
  createUser(input: {
    username: "johndoe"
    email: "john@example.com"
    password: "secure_password"
    role: "user"
  }) {
    id
    username
    email
  }
}

# Create message
mutation CreateMessage {
  createMessage(input: {
    content: "Hello, GraphQL!"
    messageType: "text"
  }) {
    id
    content
    timestamp
  }
}

# Update ticket
mutation UpdateTicket {
  updateTicket(
    id: 1
    input: {
      status: "in_progress"
      priority: "high"
      assignedTo: 5
    }
  ) {
    id
    title
    status
    priority
  }
}
```

### Subscription Examples

```graphql
# Subscribe to new messages
subscription NewMessages {
  messageAdded {
    id
    content
    username
    timestamp
  }
}

# Subscribe to ticket updates
subscription TicketUpdates {
  ticketUpdated(projectId: 1) {
    id
    title
    status
    updatedAt
  }
}
```

## Security

### Query Complexity Limits

```python
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=10),
    ]
)
```

### Authentication

```python
from strawberry.permission import BasePermission

class IsAuthenticated(BasePermission):
    """Require authentication."""
    message = "User is not authenticated"
    
    async def has_permission(self, source, info, **kwargs) -> bool:
        return info.context.get("current_user") is not None


# Apply to field
@strawberry.field(permission_classes=[IsAuthenticated])
async def sensitive_data(self) -> str:
    return "Secret data"
```

## Performance Optimization

### Caching

```python
from strawberry.extensions import AddValidationRules
from graphql import ValidationRule

# Add caching layer
@strawberry.field
@cache(ttl=300)  # Cache for 5 minutes
async def expensive_query(self) -> List[User]:
    # Expensive operation
    return await get_all_users()
```

### Query Batching

Enable query batching in GraphQL Playground to reduce HTTP requests.

## Monitoring

### Metrics

```python
from prometheus_client import Counter, Histogram

graphql_queries = Counter('graphql_queries_total', 'Total GraphQL queries', ['operation'])
graphql_duration = Histogram('graphql_query_duration_seconds', 'GraphQL query duration')
```

## Migration from REST to GraphQL

### Gradual Migration Strategy

1. **Phase 1**: Implement GraphQL parallel to REST (current approach)
2. **Phase 2**: Migrate read operations to GraphQL
3. **Phase 3**: Migrate write operations to GraphQL
4. **Phase 4**: Deprecate REST endpoints (optional)

### Benefits of GraphQL

1. **Flexible queries**: Clients request exactly what they need
2. **Single endpoint**: No need for multiple REST endpoints
3. **Strong typing**: Schema provides type safety
4. **Real-time**: Subscriptions for live updates
5. **Better mobile**: Reduced bandwidth usage

## Testing

### Unit Tests

```python
import pytest
from graphql_api.schema import schema

@pytest.mark.asyncio
async def test_get_users():
    query = """
        query {
            users(limit: 10) {
                id
                username
            }
        }
    """
    result = await schema.execute(query)
    assert result.errors is None
    assert len(result.data["users"]) <= 10
```

## References

- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [API Examples](docs/API_EXAMPLES.md)
- [ADR-014: GraphQL API Strategy](adr/ADR-014-graphql-api-strategy.md)
