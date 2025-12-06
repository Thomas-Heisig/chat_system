# Performance Optimization Guide

**Universal Chat System**  
**Version:** 2.0.0  
**Last Updated:** 2025-12-06

## Overview

This document provides comprehensive guidelines for optimizing the performance of the Universal Chat System. It covers database optimization, caching strategies, response compression, and performance monitoring.

---

## Table of Contents

1. [Database Performance](#database-performance)
2. [Caching Strategies](#caching-strategies)
3. [Response Optimization](#response-optimization)
4. [WebSocket Performance](#websocket-performance)
5. [Performance Monitoring](#performance-monitoring)
6. [Best Practices](#best-practices)

---

## Database Performance

### Query Optimization

#### Slow Query Logging

Monitor and identify slow queries using SQLAlchemy events:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
from config.settings import logger

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Log queries taking more than 100ms
    if total > 0.1:
        logger.warning(
            "slow_query",
            duration=total,
            query=statement[:200],
            params=str(parameters)[:100]
        )
```

**Configuration** (`config/settings.py`):

```python
# Slow query threshold in seconds
SLOW_QUERY_THRESHOLD = float(os.getenv("SLOW_QUERY_THRESHOLD", "0.1"))

# Enable query logging
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
```

#### N+1 Query Prevention

Use eager loading to prevent N+1 query problems:

```python
from sqlalchemy.orm import joinedload, selectinload

# ❌ BAD - N+1 queries
messages = session.query(Message).all()
for message in messages:
    print(message.user.username)  # Separate query for each user

# ✅ GOOD - Single query with join
messages = session.query(Message).options(
    joinedload(Message.user)
).all()

# ✅ GOOD - Two queries total (better for large collections)
messages = session.query(Message).options(
    selectinload(Message.user)
).all()
```

#### Query Analysis (PostgreSQL)

Enable and use `pg_stat_statements`:

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT 
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    substring(query, 1, 100) as query_preview
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

### Database Indexing

#### Common Query Patterns

Add indexes for frequently queried fields:

```python
# In database/models.py

from sqlalchemy import Index

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # For queries filtering by user and date
        Index('idx_message_user_created', 'user_id', 'created_at'),
        
        # For queries filtering by project and date
        Index('idx_message_project_created', 'project_id', 'created_at'),
        
        # For full-text search (PostgreSQL)
        # Index('idx_message_content_fulltext', 
        #       func.to_tsvector('english', 'content'),
        #       postgresql_using='gin'),
    )

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), index=True)  # For name searches
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True, index=True)  # For filtering active projects
    
    __table_args__ = (
        Index('idx_project_owner_active', 'owner_id', 'is_active'),
    )

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, index=True)  # For login
    email = Column(String(200), unique=True, index=True)  # For email lookup
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, index=True)  # For activity tracking
```

#### Index Migration

Create a migration for adding indexes:

```python
"""Add performance indexes

Revision ID: 001_add_indexes
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add composite indexes
    op.create_index(
        'idx_message_user_created',
        'messages',
        ['user_id', 'created_at']
    )
    
    op.create_index(
        'idx_message_project_created',
        'messages',
        ['project_id', 'created_at']
    )
    
    op.create_index(
        'idx_project_owner_active',
        'projects',
        ['owner_id', 'is_active']
    )
    
    # Add single column indexes if not already present
    op.create_index(
        'idx_user_last_login',
        'users',
        ['last_login']
    )

def downgrade():
    op.drop_index('idx_message_user_created', 'messages')
    op.drop_index('idx_message_project_created', 'messages')
    op.drop_index('idx_project_owner_active', 'projects')
    op.drop_index('idx_user_last_login', 'users')
```

#### Index Monitoring

Check index usage (PostgreSQL):

```sql
-- Find unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename, indexname;

-- Find missing indexes (queries not using indexes)
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan as avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;
```

### Connection Pooling

Configure optimal connection pool settings:

```python
# config/settings.py

# Database connection pool configuration
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# In database/connection.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before use
)
```

**Recommended Settings:**

| Environment | pool_size | max_overflow | Notes |
|-------------|-----------|--------------|-------|
| Development | 5 | 10 | Lower resource usage |
| Production | 10 | 20 | Handle concurrent requests |
| High Traffic | 20 | 40 | Scale with load |

---

## Caching Strategies

### Redis Caching

Implement caching for frequently accessed data:

```python
import redis
import json
from functools import wraps
from config.settings import REDIS_URL, logger

# Initialize Redis
redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None

def cache_result(ttl: int = 300):
    """
    Cache decorator for functions
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Cache read error: {e}")
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            try:
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result)
                )
            except Exception as e:
                logger.error(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator
```

**Usage Example:**

```python
from services.cache_decorator import cache_result

class MessageService:
    
    @cache_result(ttl=60)  # Cache for 1 minute
    async def get_recent_messages(self, project_id: int, limit: int = 50):
        """Get recent messages (cached)"""
        messages = await self.repository.get_messages(
            project_id=project_id,
            limit=limit
        )
        return messages
    
    async def create_message(self, message_data: dict):
        """Invalidate cache when creating message"""
        message = await self.repository.create(message_data)
        
        # Invalidate cache
        cache_key = f"get_recent_messages:{message.project_id}:*"
        redis_client.delete(*redis_client.keys(cache_key))
        
        return message
```

### In-Memory Caching

For single-instance deployments, use in-memory caching:

```python
from functools import lru_cache
from typing import Optional

class ConfigService:
    
    @lru_cache(maxsize=128)
    def get_config(self, key: str) -> Optional[str]:
        """Get configuration value (cached)"""
        # Expensive operation cached in memory
        return self.repository.get_config(key)
```

---

## Response Optimization

### Response Compression

Enable Gzip/Brotli compression for API responses:

```python
# In main.py
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add GZIP compression middleware
app.add_middleware(
    GZIPMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
    compresslevel=5     # Balance between speed and compression ratio
)
```

**Brotli Compression** (better compression than Gzip):

```bash
pip install brotli-asgi
```

```python
from brotli_asgi import BrotliMiddleware

app.add_middleware(
    BrotliMiddleware,
    minimum_size=1000,
    quality=4  # 0-11, higher = better compression but slower
)
```

### Static Asset Optimization

Configure static file caching:

```python
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

class CachedStaticFiles(StaticFiles):
    """Static files with cache headers"""
    
    def __init__(self, *args, max_age: int = 3600, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_age = max_age
    
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        
        # Add cache headers
        response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
        
        return response

# Mount with caching
app.mount(
    "/static",
    CachedStaticFiles(directory="static", max_age=86400),  # 24 hours
    name="static"
)
```

### JSON Response Optimization

Optimize JSON serialization:

```python
import orjson
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)

# orjson is 2-3x faster than standard json library
# Install: pip install orjson
```

### Pagination

Implement efficient pagination:

```python
from typing import List, Optional
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

@app.get("/api/messages")
async def get_messages(
    page: int = 1,
    per_page: int = 50,
    project_id: Optional[int] = None
):
    """Get paginated messages"""
    
    # Validate parameters
    per_page = min(per_page, 100)  # Max 100 items per page
    offset = (page - 1) * per_page
    
    # Get total count (cached)
    total = await message_service.count_messages(project_id=project_id)
    
    # Get page of items
    messages = await message_service.get_messages(
        project_id=project_id,
        limit=per_page,
        offset=offset
    )
    
    return PaginatedResponse(
        items=messages,
        total=total,
        page=page,
        per_page=per_page,
        has_next=(offset + per_page) < total,
        has_prev=page > 1
    )
```

---

## WebSocket Performance

### Connection Management

Optimize WebSocket connection handling:

```python
class OptimizedWebSocketManager:
    """WebSocket manager with performance optimizations"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_lock = asyncio.Lock()
        self.broadcast_queue = asyncio.Queue()
        
        # Start broadcast worker
        asyncio.create_task(self._broadcast_worker())
    
    async def _broadcast_worker(self):
        """Background worker for efficient broadcasting"""
        while True:
            message = await self.broadcast_queue.get()
            
            # Send to all connections concurrently
            tasks = [
                self._send_safe(ws, message)
                for ws in self.active_connections.values()
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_safe(self, websocket: WebSocket, message: dict):
        """Send message with error handling"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            # Remove dead connection
            await self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Queue message for broadcasting"""
        await self.broadcast_queue.put(message)
```

### Message Batching

Batch multiple messages to reduce overhead:

```python
class MessageBatcher:
    """Batch messages for efficient delivery"""
    
    def __init__(self, max_batch_size: int = 10, max_wait_ms: int = 100):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.pending_messages: List[dict] = []
        self.last_flush = time.time()
    
    async def add_message(self, message: dict):
        """Add message to batch"""
        self.pending_messages.append(message)
        
        # Flush if batch is full or timeout reached
        if (len(self.pending_messages) >= self.max_batch_size or
            (time.time() - self.last_flush) * 1000 >= self.max_wait_ms):
            await self.flush()
    
    async def flush(self):
        """Send batched messages"""
        if not self.pending_messages:
            return
        
        # Send batch
        await websocket_manager.broadcast({
            "type": "message_batch",
            "messages": self.pending_messages
        })
        
        self.pending_messages = []
        self.last_flush = time.time()
```

---

## Performance Monitoring

### Metrics Collection

Track key performance metrics:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Middleware for tracking
@app.middleware("http")
async def track_performance(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### Performance Profiling

Profile slow endpoints:

```python
import cProfile
import pstats
import io

def profile_endpoint(func):
    """Decorator to profile endpoint performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = await func(*args, **kwargs)
        
        profiler.disable()
        
        # Print stats if slow
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions
        
        logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")
        
        return result
    
    return wrapper
```

---

## Best Practices

### Performance Checklist

- [x] Enable slow query logging
- [x] Add database indexes for common queries
- [x] Use eager loading to prevent N+1 queries
- [x] Configure connection pooling
- [x] Implement caching (Redis or in-memory)
- [x] Enable response compression (Gzip/Brotli)
- [x] Optimize static asset delivery
- [x] Implement pagination for large result sets
- [x] Use efficient JSON serialization (orjson)
- [x] Optimize WebSocket broadcasting
- [x] Monitor performance metrics
- [ ] Profile slow endpoints regularly
- [ ] Regular performance testing
- [ ] Database query analysis

### Performance Testing

Use locust for load testing:

```python
# locustfile.py
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login on start"""
        self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    @task(3)
    def get_messages(self):
        """Get messages (most common)"""
        self.client.get("/api/messages?page=1&per_page=50")
    
    @task(2)
    def get_projects(self):
        """Get projects"""
        self.client.get("/api/projects")
    
    @task(1)
    def send_message(self):
        """Send message (less common)"""
        self.client.post("/api/messages", json={
            "content": "Test message",
            "project_id": 1
        })
```

**Run load test:**

```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

### Optimization Priorities

1. **High Impact, Low Effort:**
   - Enable response compression
   - Add database indexes
   - Configure connection pooling

2. **High Impact, Medium Effort:**
   - Implement Redis caching
   - Optimize slow queries
   - Add pagination

3. **Medium Impact, Low Effort:**
   - Use orjson for JSON
   - Optimize static assets
   - Enable query logging

4. **Medium Impact, High Effort:**
   - Implement message batching
   - Advanced caching strategies
   - Database sharding

---

## Environment Variables

Add to `.env`:

```bash
# Database Performance
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
SLOW_QUERY_THRESHOLD=0.1
SQLALCHEMY_ECHO=false

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Compression
ENABLE_COMPRESSION=true
COMPRESSION_LEVEL=5

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

---

## Performance Targets

### Response Time Goals

| Endpoint Type | Target (p95) | Current | Status |
|--------------|--------------|---------|--------|
| Simple GET | < 50ms | TBD | 📊 |
| Complex GET | < 200ms | TBD | 📊 |
| POST/PUT | < 100ms | TBD | 📊 |
| WebSocket | < 50ms | TBD | 📊 |

### Throughput Goals

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Requests/sec | > 1000 | TBD | 📊 |
| Concurrent Users | > 500 | TBD | 📊 |
| Messages/sec | > 100 | TBD | 📊 |

---

## References

- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)
- [FastAPI Performance](https://fastapi.tiangolo.com/advanced/performance/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Web Performance Best Practices](https://web.dev/performance/)

---

**Last Updated:** 2025-12-06  
**Version:** 2.0.0

For implementation support, see:
- [TODO.md](../TODO.md) - Performance tasks
- [MONITORING.md](MONITORING.md) - Metrics and observability
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Performance issues
