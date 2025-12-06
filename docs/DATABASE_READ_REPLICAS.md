# Database Read Replicas

## Overview

This document describes the database read replica configuration for the Chat System, enabling horizontal scaling of database reads through PostgreSQL replication. Read replicas improve performance by distributing read queries across multiple database instances while maintaining a single primary for writes.

## Configuration

### Environment Variables

```bash
# Read Replica Configuration
DB_READ_REPLICAS_ENABLED=false  # Enable read replica support
DB_PRIMARY_URL=postgresql://user:pass@primary-host:5432/chatdb  # Primary (write) database
DB_READ_REPLICA_URLS=postgresql://user:pass@replica1:5432/chatdb,postgresql://user:pass@replica2:5432/chatdb  # Comma-separated read replicas

# Load Balancing Strategy
DB_READ_REPLICA_STRATEGY=round_robin  # round_robin, random, least_connections
DB_READ_REPLICA_FALLBACK=true  # Fall back to primary if replicas unavailable
DB_READ_REPLICA_HEALTH_CHECK_INTERVAL=30  # Health check interval in seconds

# Replication Lag Handling
DB_MAX_REPLICATION_LAG_MS=1000  # Maximum acceptable replication lag (milliseconds)
DB_LAG_CHECK_ENABLED=true  # Check replication lag before routing queries
```

### Settings in Code

```python
from config.settings import database_config

# Check read replica status
if database_config.read_replicas_enabled:
    replicas = database_config.read_replica_urls
    strategy = database_config.read_replica_strategy
```

## Architecture

### Components

1. **Primary Database**: Handles all write operations and provides consistency
2. **Read Replicas**: Handle read-only queries, reduce load on primary
3. **Connection Router**: Routes queries to appropriate database based on operation type
4. **Health Monitor**: Tracks replica availability and replication lag

### Read/Write Splitting

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Connection Router│
└────┬────────┬────┘
     │        │
     │ Write  │ Read
     ▼        ▼
┌─────────┐  ┌──────────────┐
│ Primary │  │ Read Replicas│
│ (Write) │  │  (Read-Only) │
└────┬────┘  └──────────────┘
     │
     │ Replication
     └──────────────────────►
```

## Implementation

### 1. Database Connection Manager

**File:** `database/replica_manager.py`

```python
"""Database read replica management with connection routing."""
import random
import time
from typing import List, Optional, Literal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)


class ReplicaHealthStatus:
    """Track health status of a replica."""
    
    def __init__(self, url: str):
        self.url = url
        self.is_healthy = True
        self.last_check = time.time()
        self.consecutive_failures = 0
        self.replication_lag_ms = 0


class ReadReplicaManager:
    """Manage read replica connections with automatic failover."""
    
    def __init__(
        self,
        primary_url: str,
        replica_urls: List[str],
        strategy: Literal["round_robin", "random", "least_connections"] = "round_robin",
        max_lag_ms: int = 1000,
        health_check_interval: int = 30,
        fallback_to_primary: bool = True
    ):
        self.primary_url = primary_url
        self.replica_urls = replica_urls
        self.strategy = strategy
        self.max_lag_ms = max_lag_ms
        self.health_check_interval = health_check_interval
        self.fallback_to_primary = fallback_to_primary
        
        # Create engine for primary
        self.primary_engine = create_engine(
            primary_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        
        # Create engines for replicas
        self.replica_engines = {
            url: create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            for url in replica_urls
        }
        
        # Health tracking
        self.replica_health = {
            url: ReplicaHealthStatus(url)
            for url in replica_urls
        }
        
        # Round-robin counter
        self._round_robin_index = 0
        
        logger.info(
            f"Initialized ReadReplicaManager: 1 primary, {len(replica_urls)} replicas"
        )
    
    def get_write_session(self) -> Session:
        """Get session for write operations (always uses primary)."""
        SessionClass = sessionmaker(bind=self.primary_engine)
        return SessionClass()
    
    def get_read_session(self) -> Session:
        """Get session for read operations (uses replicas if available)."""
        # Try to get a healthy replica
        replica_engine = self._select_replica()
        
        if replica_engine:
            SessionClass = sessionmaker(bind=replica_engine)
            return SessionClass()
        
        # Fallback to primary if configured
        if self.fallback_to_primary:
            logger.warning("No healthy replicas available, falling back to primary")
            return self.get_write_session()
        
        raise RuntimeError("No healthy read replicas available and fallback disabled")
    
    def _select_replica(self) -> Optional[object]:
        """Select a healthy replica based on configured strategy."""
        healthy_replicas = [
            (url, engine)
            for url, engine in self.replica_engines.items()
            if self._is_replica_healthy(url)
        ]
        
        if not healthy_replicas:
            return None
        
        if self.strategy == "random":
            return random.choice(healthy_replicas)[1]
        elif self.strategy == "round_robin":
            self._round_robin_index = (self._round_robin_index + 1) % len(healthy_replicas)
            return healthy_replicas[self._round_robin_index][1]
        elif self.strategy == "least_connections":
            # For simplicity, use random; actual implementation would track connections
            return random.choice(healthy_replicas)[1]
        
        return healthy_replicas[0][1]
    
    def _is_replica_healthy(self, url: str) -> bool:
        """Check if replica is healthy (with caching)."""
        status = self.replica_health[url]
        
        # Use cached status if recent
        now = time.time()
        if now - status.last_check < self.health_check_interval:
            return status.is_healthy
        
        # Perform health check
        try:
            engine = self.replica_engines[url]
            with engine.connect() as conn:
                # Check database connectivity
                conn.execute(text("SELECT 1"))
                
                # Check replication lag (PostgreSQL specific)
                result = conn.execute(text(
                    "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) * 1000 AS lag_ms"
                ))
                lag_ms = result.scalar()
                
                status.replication_lag_ms = lag_ms or 0
                status.is_healthy = status.replication_lag_ms <= self.max_lag_ms
                status.consecutive_failures = 0
                
                logger.debug(f"Replica {url} health check: lag={lag_ms}ms, healthy={status.is_healthy}")
        except Exception as e:
            status.is_healthy = False
            status.consecutive_failures += 1
            logger.error(f"Replica {url} health check failed: {e}")
        
        status.last_check = now
        return status.is_healthy
    
    def get_replica_status(self) -> dict:
        """Get current status of all replicas."""
        return {
            url: {
                "healthy": status.is_healthy,
                "lag_ms": status.replication_lag_ms,
                "last_check": status.last_check,
                "consecutive_failures": status.consecutive_failures
            }
            for url, status in self.replica_health.items()
        }


# Global instance (initialized in main.py)
replica_manager: Optional[ReadReplicaManager] = None


def init_replica_manager(
    primary_url: str,
    replica_urls: List[str],
    **kwargs
):
    """Initialize global replica manager."""
    global replica_manager
    replica_manager = ReadReplicaManager(primary_url, replica_urls, **kwargs)
    logger.info("Read replica manager initialized")


def get_write_session() -> Session:
    """Get database session for write operations."""
    if replica_manager:
        return replica_manager.get_write_session()
    # Fallback to single database
    from database.session import SessionLocal
    return SessionLocal()


def get_read_session() -> Session:
    """Get database session for read operations."""
    if replica_manager:
        return replica_manager.get_read_session()
    # Fallback to single database
    from database.session import SessionLocal
    return SessionLocal()
```

### 2. FastAPI Dependency Integration

**File:** `core/dependencies.py` (add to existing file)

```python
from database.replica_manager import get_write_session, get_read_session
from sqlalchemy.orm import Session

# Write session dependency
def get_db_write() -> Session:
    """Database session for write operations."""
    session = get_write_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Read session dependency
def get_db_read() -> Session:
    """Database session for read operations."""
    session = get_read_session()
    try:
        yield session
    finally:
        session.close()
```

### 3. Usage in Routes

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db_read, get_db_write

router = APIRouter()

# Read operation - uses replica
@router.get("/messages")
async def get_messages(db: Session = Depends(get_db_read)):
    messages = db.query(Message).all()
    return messages

# Write operation - uses primary
@router.post("/messages")
async def create_message(
    data: MessageCreate,
    db: Session = Depends(get_db_write)
):
    message = Message(**data.dict())
    db.add(message)
    db.commit()
    return message
```

## PostgreSQL Replication Setup

### Streaming Replication (Recommended)

#### 1. Configure Primary Server

**File:** `postgresql.conf` (on primary)

```conf
# Replication settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
```

**File:** `pg_hba.conf` (on primary)

```conf
# Allow replication connections
host replication replicator replica_ip/32 md5
```

#### 2. Create Replication User

```sql
-- On primary database
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'secure_password';
```

#### 3. Set Up Replica

```bash
# On replica server - initial setup
pg_basebackup -h primary_host -D /var/lib/postgresql/data -U replicator -P -v -R -X stream -C -S replica_slot_1

# Start replica
pg_ctl start
```

**File:** `postgresql.conf` (on replica)

```conf
hot_standby = on
```

### Logical Replication (Advanced)

For selective table replication:

```sql
-- On primary
CREATE PUBLICATION chat_pub FOR ALL TABLES;

-- On replica
CREATE SUBSCRIPTION chat_sub 
CONNECTION 'host=primary_host dbname=chatdb user=replicator password=xxx' 
PUBLICATION chat_pub;
```

## Monitoring and Health Checks

### Health Check Endpoint

```python
@router.get("/health/database")
async def database_health():
    """Check database and replica health."""
    if not replica_manager:
        return {"status": "single_database", "replicas": 0}
    
    status = replica_manager.get_replica_status()
    healthy_count = sum(1 for s in status.values() if s["healthy"])
    
    return {
        "status": "healthy" if healthy_count > 0 else "degraded",
        "replicas": {
            "total": len(status),
            "healthy": healthy_count,
            "unhealthy": len(status) - healthy_count
        },
        "details": status
    }
```

### Monitoring Metrics

```python
from prometheus_client import Gauge, Counter

# Metrics
replica_lag_gauge = Gauge('db_replica_lag_seconds', 'Replication lag in seconds', ['replica'])
replica_health_gauge = Gauge('db_replica_health', 'Replica health status (1=healthy, 0=unhealthy)', ['replica'])
replica_queries_counter = Counter('db_replica_queries_total', 'Total queries to replicas', ['replica'])
```

## Failover and Recovery

### Automatic Failover

The `ReadReplicaManager` automatically handles replica failures:

1. **Health checks** continuously monitor replicas
2. **Automatic removal** of unhealthy replicas from rotation
3. **Fallback to primary** if all replicas are down (configurable)
4. **Automatic recovery** when replicas become healthy again

### Manual Promotion

If primary fails, promote a replica to primary:

```bash
# On replica to be promoted
pg_ctl promote
```

Update configuration:

```bash
# Update application configuration
DB_PRIMARY_URL=postgresql://user:pass@new-primary:5432/chatdb
DB_READ_REPLICA_URLS=postgresql://user:pass@replica2:5432/chatdb
```

## Performance Considerations

### Query Optimization

1. **Read-heavy workloads**: Most benefit from read replicas
2. **Replication lag**: Monitor and alert on excessive lag
3. **Connection pooling**: Adjust pool sizes based on load
4. **Query routing**: Ensure proper read/write classification

### Benchmarking

```bash
# Test read performance with replicas
ab -n 1000 -c 10 http://localhost:8000/api/messages

# Compare with single database
# Typically see 2-3x improvement with 2 replicas
```

## Troubleshooting

### Common Issues

1. **High replication lag**
   - Check network latency between primary and replicas
   - Review write load on primary
   - Consider increasing `max_wal_senders` and network bandwidth

2. **Replica connection failures**
   - Verify `pg_hba.conf` allows replication connections
   - Check firewall rules between servers
   - Verify replication user credentials

3. **Stale data on replicas**
   - Monitor `pg_last_xact_replay_timestamp()`
   - Implement application-level consistency checks
   - Consider using synchronous replication for critical data

### Diagnostic Queries

```sql
-- Check replication status (on primary)
SELECT * FROM pg_stat_replication;

-- Check replication lag (on replica)
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;

-- Check replica status (on replica)
SELECT pg_is_in_recovery();
```

## Best Practices

1. **Monitor replication lag**: Set alerts for lag > 5 seconds
2. **Use connection pooling**: Efficiently manage database connections
3. **Classify queries correctly**: Ensure writes go to primary
4. **Test failover procedures**: Regularly practice replica promotion
5. **Consider synchronous replication**: For critical consistency requirements
6. **Implement read-after-write consistency**: Use primary for immediate reads after writes
7. **Geographic distribution**: Place replicas near users for low latency

## Configuration Examples

### Development (Single Database)

```bash
DB_READ_REPLICAS_ENABLED=false
DB_URL=postgresql://user:pass@localhost:5432/chatdb
```

### Production (Primary + 2 Replicas)

```bash
DB_READ_REPLICAS_ENABLED=true
DB_PRIMARY_URL=postgresql://user:pass@primary.example.com:5432/chatdb
DB_READ_REPLICA_URLS=postgresql://user:pass@replica1.example.com:5432/chatdb,postgresql://user:pass@replica2.example.com:5432/chatdb
DB_READ_REPLICA_STRATEGY=round_robin
DB_MAX_REPLICATION_LAG_MS=2000
DB_LAG_CHECK_ENABLED=true
```

## Migration Guide

### From Single Database to Read Replicas

1. **Set up replicas** using `pg_basebackup`
2. **Test replica health** before enabling in application
3. **Update configuration** with replica URLs
4. **Enable read replicas** in configuration
5. **Monitor performance** and replication lag
6. **Adjust pool sizes** based on load distribution

## References

- [PostgreSQL Replication Documentation](https://www.postgresql.org/docs/current/high-availability.html)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Performance Guide](06-operations/PERFORMANCE.md)
- [ADR-013: Database Read Replica Strategy](adr/ADR-013-database-read-replicas.md)
