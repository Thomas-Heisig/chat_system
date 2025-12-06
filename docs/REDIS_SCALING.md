# Redis Pub/Sub for WebSocket Scaling

## Overview

This document describes how to configure Redis Pub/Sub for scaling WebSocket connections across multiple server instances. The system provides graceful fallback to single-instance mode when Redis is unavailable.

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_ENABLED=false  # Enable Redis
REDIS_URL=redis://localhost:6379/0  # Redis connection URL
REDIS_PUBSUB_ENABLED=false  # Enable Pub/Sub for WebSocket scaling

# Connection Pool Settings
REDIS_POOL_SIZE=10
REDIS_SOCKET_TIMEOUT=5
REDIS_MAX_CONNECTIONS=50

# Pub/Sub Configuration
REDIS_CHANNEL_PREFIX=chat_system  # Prefix for pub/sub channels
REDIS_RETRY_ON_TIMEOUT=true
REDIS_RETRY_ATTEMPTS=3
```

### Settings in Code

```python
from config.settings import infrastructure_config

# Check if Redis is enabled
if infrastructure_config.redis_enabled:
    redis_url = infrastructure_config.redis_url
    pubsub_enabled = infrastructure_config.redis_pubsub_enabled
```

## Fallback Behavior

When Redis is disabled or unavailable:
- **Single Instance Mode:** WebSocket broadcasting works within single server
- **No Errors:** System continues normally
- **Automatic Degradation:** Pub/Sub calls become local broadcasts
- **No Data Loss:** Messages delivered to connections on same instance

## Architecture

### Single Instance (Default)

```
┌─────────────────┐
│   Web Server    │
│  ┌───────────┐  │
│  │ WebSocket │  │
│  │ Manager   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Client1  │  │
│  │  Client2  │  │
│  │  Client3  │  │
│  └───────────┘  │
└─────────────────┘
```

### Multi-Instance with Redis Pub/Sub

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Instance 1  │    │  Instance 2  │    │  Instance 3  │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │WebSocket │ │    │ │WebSocket │ │    │ │WebSocket │ │
│ │ Manager  │ │    │ │ Manager  │ │    │ │ Manager  │ │
│ └────┬─────┘ │    │ └────┬─────┘ │    │ └────┬─────┘ │
│      │       │    │      │       │    │      │       │
│ ┌────▼────┐  │    │ ┌────▼────┐  │    │ ┌────▼────┐  │
│ │Client1  │  │    │ │Client4  │  │    │ │Client7  │  │
│ │Client2  │  │    │ │Client5  │  │    │ │Client8  │  │
│ │Client3  │  │    │ │Client6  │  │    │ │Client9  │  │
│ └─────────┘  │    │ └─────────┘  │    │ └─────────┘  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │   Pub/Sub   │
                    └─────────────┘
```

## Implementation

### WebSocket Manager with Redis

```python
# websocket/redis_manager.py
import redis.asyncio as redis
from typing import Optional, Set
import json

class RedisWebSocketManager:
    """WebSocket manager with Redis Pub/Sub for multi-instance scaling"""
    
    def __init__(self):
        from config.settings import infrastructure_config
        
        self.enabled = infrastructure_config.redis_pubsub_enabled
        self.channel_prefix = "chat_system"
        self.local_connections: Set[WebSocket] = set()
        
        if self.enabled:
            self.redis_client = redis.from_url(
                infrastructure_config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            self._start_subscriber()
        else:
            self.redis_client = None
            self.pubsub = None
    
    async def connect(self, websocket: WebSocket):
        """Add WebSocket connection"""
        await websocket.accept()
        self.local_connections.add(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.local_connections.discard(websocket)
    
    async def broadcast(self, message: dict, room: Optional[str] = None):
        """
        Broadcast message to all connected clients.
        
        With Redis: Publishes to all instances
        Without Redis: Broadcasts locally only
        """
        channel = f"{self.channel_prefix}:{room}" if room else self.channel_prefix
        
        if self.enabled and self.redis_client:
            # Publish to Redis for multi-instance distribution
            await self.redis_client.publish(
                channel,
                json.dumps(message)
            )
        else:
            # Local broadcast only (fallback mode)
            await self._broadcast_local(message)
    
    async def _broadcast_local(self, message: dict):
        """Broadcast to local connections only"""
        disconnected = set()
        
        for websocket in self.local_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        self.local_connections -= disconnected
    
    async def _start_subscriber(self):
        """Start Redis subscriber (background task)"""
        if not self.enabled:
            return
        
        await self.pubsub.subscribe(f"{self.channel_prefix}:*")
        
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await self._broadcast_local(data)
    
    def get_status(self) -> dict:
        """Get manager status"""
        return {
            "redis_enabled": self.enabled,
            "local_connections": len(self.local_connections),
            "fallback_mode": not self.enabled,
            "configuration": {
                "REDIS_ENABLED": self.enabled,
                "REDIS_PUBSUB_ENABLED": self.enabled,
                "REDIS_URL": "configured" if self.redis_client else "not configured",
            }
        }
```

### Using the Manager

```python
# main.py or websocket handler
from websocket.redis_manager import RedisWebSocketManager

# Initialize manager
ws_manager = RedisWebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Broadcast to all instances
            await ws_manager.broadcast({
                "type": "message",
                "content": data["content"],
                "user": data["user"]
            })
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
```

## Redis Setup

### Using Docker

```bash
# Start Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:alpine

# With persistence
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:alpine redis-server --appendonly yes
```

### Using Docker Compose

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis-data:
```

### Redis Sentinel (High Availability)

```yaml
services:
  redis-master:
    image: redis:alpine
    command: redis-server --appendonly yes
  
  redis-sentinel:
    image: redis:alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./sentinel.conf:/etc/redis/sentinel.conf
```

**sentinel.conf:**
```
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
```

## Load Balancing

### Nginx Configuration

```nginx
upstream chat_backend {
    # Sticky sessions for WebSocket
    ip_hash;
    
    server instance1:8000;
    server instance2:8000;
    server instance3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://chat_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Kubernetes Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: chat-system
spec:
  type: LoadBalancer
  selector:
    app: chat-system
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  sessionAffinity: ClientIP  # Sticky sessions
```

## Monitoring

### Redis Metrics

```python
async def get_redis_stats():
    """Get Redis statistics"""
    if not ws_manager.enabled:
        return {"status": "disabled"}
    
    info = await ws_manager.redis_client.info()
    
    return {
        "connected_clients": info["connected_clients"],
        "used_memory": info["used_memory_human"],
        "pubsub_channels": info["pubsub_channels"],
        "pubsub_patterns": info["pubsub_patterns"],
        "total_commands_processed": info["total_commands_processed"],
    }
```

### Health Check

```python
@app.get("/health/redis")
async def redis_health():
    """Check Redis connection health"""
    if not ws_manager.enabled:
        return {
            "status": "disabled",
            "fallback_mode": True,
            "message": "Redis is disabled, using single-instance mode"
        }
    
    try:
        await ws_manager.redis_client.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "fallback_mode": True
        }
```

## Performance Tuning

### Connection Pool

```python
redis_client = redis.from_url(
    redis_url,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)
```

### Message Batching

```python
async def broadcast_batch(messages: list):
    """Broadcast multiple messages efficiently"""
    pipeline = ws_manager.redis_client.pipeline()
    
    for msg in messages:
        pipeline.publish(channel, json.dumps(msg))
    
    await pipeline.execute()
```

## Troubleshooting

### Redis Connection Failed

**Problem:** Cannot connect to Redis

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify REDIS_URL in configuration
3. Check network connectivity
4. Verify firewall rules

**Fallback:** System automatically uses single-instance mode

### High Memory Usage

**Problem:** Redis using too much memory

**Solutions:**
1. Configure maxmemory: `redis-cli CONFIG SET maxmemory 1gb`
2. Set eviction policy: `redis-cli CONFIG SET maxmemory-policy allkeys-lru`
3. Monitor with: `redis-cli INFO memory`

### Message Delivery Issues

**Problem:** Messages not reaching all instances

**Solutions:**
1. Verify all instances connected to same Redis
2. Check pub/sub channels: `redis-cli PUBSUB CHANNELS`
3. Monitor subscribers: `redis-cli PUBSUB NUMSUB channel_name`
4. Check network connectivity between instances

## Best Practices

1. **Enable for Production:** Use Redis Pub/Sub in multi-instance deployments
2. **Monitor Performance:** Track Redis metrics
3. **Use Connection Pool:** Configure appropriate pool size
4. **Handle Reconnection:** Implement retry logic
5. **Test Fallback:** Verify system works without Redis
6. **Secure Redis:** Use password authentication
7. **Regular Backups:** If using persistence

## Related Documentation

- [WebSocket Documentation](docs/WEBSOCKET.md)
- [Performance Monitoring](PERFORMANCE.md)
- [Deployment Guide](DEPLOYMENT.md)

**Note:** Redis is optional. Set `REDIS_ENABLED=false` to use single-instance mode without any loss of core functionality.
