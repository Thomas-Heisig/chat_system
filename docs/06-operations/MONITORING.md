# Monitoring and Observability Guide

This guide covers monitoring, metrics, and observability features for the Universal Chat System.

## Overview

Monitoring is essential for understanding system health, performance, and debugging issues in production. This document covers:

- Prometheus metrics export
- Distributed tracing
- Log aggregation
- Performance monitoring
- Alert configuration

## Prometheus Metrics (Planned)

### Setup

The system is designed to support Prometheus metrics export using `prometheus-fastapi-instrumentator`.

#### Installation

```bash
pip install prometheus-fastapi-instrumentator
```

#### Configuration

Add to `main.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    excluded_handlers=["/metrics", "/health"],
)

# Instrument the FastAPI app
instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

### Available Metrics

Once implemented, the following metrics will be available:

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_request_size_bytes` - Request body size
- `http_response_size_bytes` - Response body size

#### Application Metrics
- `websocket_connections_active` - Current WebSocket connections
- `websocket_messages_total` - Total WebSocket messages sent/received
- `database_queries_total` - Total database queries
- `database_query_duration_seconds` - Database query duration
- `ai_requests_total` - Total AI API requests
- `ai_response_duration_seconds` - AI response time
- `rag_queries_total` - Total RAG queries
- `cache_hits_total` - Cache hit rate
- `file_uploads_total` - Total file uploads
- `file_upload_size_bytes` - File upload sizes

#### System Metrics
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `process_open_fds` - Open file descriptors

### Custom Metrics

Add custom business metrics:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define custom metrics
chat_messages_sent = Counter(
    'chat_messages_sent_total',
    'Total chat messages sent',
    ['user_role', 'message_type']
)

ai_model_usage = Counter(
    'ai_model_usage_total',
    'AI model usage by provider',
    ['provider', 'model']
)

active_users = Gauge(
    'active_users',
    'Currently active users'
)

# Use in code
chat_messages_sent.labels(user_role='user', message_type='text').inc()
ai_model_usage.labels(provider='ollama', model='llama3').inc()
active_users.set(len(active_websocket_connections))
```

### Prometheus Configuration

Example `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'chat_system'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import the pre-built dashboard from `monitoring/grafana-dashboard.json` or create custom dashboards:

- Request rate and latency
- Error rates by endpoint
- WebSocket connection count
- AI response times
- Database query performance
- System resources (CPU, memory)

## Distributed Tracing (Planned)

### OpenTelemetry Integration

For distributed tracing across services, implement OpenTelemetry:

#### Installation

```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-exporter-jaeger  # or zipkin
```

#### Configuration

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

#### Custom Spans

Add custom tracing to critical paths:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_ai_request(prompt: str):
    with tracer.start_as_current_span("ai_request") as span:
        span.set_attribute("prompt.length", len(prompt))
        
        # Process request
        result = await ai_service.generate(prompt)
        
        span.set_attribute("response.length", len(result))
        return result
```

### Jaeger Setup

Run Jaeger all-in-one:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

Access Jaeger UI at http://localhost:16686

## Log Aggregation

### Structured Logging

The system uses structured logging for better log analysis:

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "message_sent",
    user_id=user.id,
    message_length=len(message),
    channel_id=channel.id
)
```

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical issues requiring immediate attention

### ELK Stack Integration

For production log aggregation, integrate with ELK (Elasticsearch, Logstash, Kibana):

1. **Logstash Configuration**:
```
input {
  file {
    path => "/var/log/chat_system/*.log"
    type => "chat_system"
    codec => json
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "chat_system-%{+YYYY.MM.dd}"
  }
}
```

2. **Log Format**: JSON structured logs
3. **Kibana Dashboards**: Pre-built dashboards for common queries

## Performance Monitoring

### Database Query Performance

Monitor slow queries:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log queries slower than 100ms
        logger.warning("slow_query", duration=total, query=statement)
```

### API Response Times

Monitor endpoint performance:

```python
from fastapi import Request
import time

@app.middleware("http")
async def track_response_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    response.headers["X-Response-Time"] = str(duration)
    
    if duration > 1.0:  # Log slow requests
        logger.warning(
            "slow_request",
            path=request.url.path,
            method=request.method,
            duration=duration
        )
    
    return response
```

## Health Checks

### Endpoints

- `/health` - Basic health check
- `/health/ready` - Readiness probe (for K8s)
- `/health/live` - Liveness probe (for K8s)

### Implementation

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }

@app.get("/health/ready")
async def readiness_check():
    # Check dependencies
    db_ok = await check_database()
    redis_ok = await check_redis()
    
    if db_ok and redis_ok:
        return {"status": "ready"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "details": {
                "database": db_ok,
                "redis": redis_ok
            }}
        )
```

## Alerting

### Recommended Alerts

Configure alerts for:

1. **High Error Rate**: Error rate > 5% for 5 minutes
2. **High Latency**: P95 latency > 2s for 5 minutes
3. **Database Issues**: Connection pool exhaustion
4. **Memory Usage**: Memory usage > 90%
5. **Disk Space**: Disk usage > 85%
6. **WebSocket Failures**: Connection failure rate > 10%
7. **AI Service Down**: AI service unavailable for 2 minutes

### Prometheus Alert Rules

Example `alert_rules.yml`:

```yaml
groups:
  - name: chat_system_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: Error rate is {{ $value }} over the last 5 minutes

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High request latency
          description: P95 latency is {{ $value }}s
```

## Best Practices

1. **Metric Naming**: Use consistent naming conventions
2. **Label Cardinality**: Keep label combinations reasonable (< 1000)
3. **Sampling**: Sample traces in high-traffic environments
4. **Log Rotation**: Implement log rotation to manage disk space
5. **Dashboard Organization**: Create role-specific dashboards
6. **Alert Fatigue**: Tune alerts to reduce false positives
7. **Documentation**: Document what each metric means
8. **Testing**: Test monitoring in staging before production

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [ELK Stack Guide](https://www.elastic.co/what-is/elk-stack)
