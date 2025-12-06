# Distributed Tracing Configuration

## Overview

This document describes how to configure distributed tracing for the Chat System using Jaeger, Zipkin, or OpenTelemetry. The system provides graceful fallback when tracing is disabled or unavailable.

## Configuration

### Environment Variables

```bash
# Distributed Tracing
TRACING_ENABLED=false  # Enable distributed tracing
TRACING_PROVIDER=jaeger  # Options: jaeger, zipkin, otlp
TRACING_ENDPOINT=http://localhost:14268/api/traces  # Tracing backend endpoint
TRACING_SAMPLE_RATE=0.1  # Sample 10% of requests (0.0-1.0)
```

### Settings in Code

```python
from config.settings import monitoring_config

# Check if tracing is enabled
if monitoring_config.tracing_enabled:
    provider = monitoring_config.tracing_provider
    endpoint = monitoring_config.tracing_endpoint
    sample_rate = monitoring_config.tracing_sample_rate
```

## Fallback Behavior

When tracing is disabled or unavailable:
- **No Performance Impact:** Zero overhead when disabled
- **No Errors:** System continues normally
- **Graceful Degradation:** Tracing calls become no-ops
- **Request Logging:** Basic request logging still available

## Supported Tracing Providers

### 1. Jaeger (Recommended)

**Features:**
- Native OpenTelemetry support
- Excellent UI for trace visualization
- Service dependency graphs
- Performance analysis

**Setup:**
```bash
# Using Docker
docker run -d \
  --name jaeger \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest

# Configuration
TRACING_ENABLED=true
TRACING_PROVIDER=jaeger
TRACING_ENDPOINT=http://localhost:14268/api/traces
```

**UI Access:** http://localhost:16686

### 2. Zipkin

**Features:**
- Simple setup
- Good visualization
- Lightweight

**Setup:**
```bash
# Using Docker
docker run -d \
  --name zipkin \
  -p 9411:9411 \
  openzipkin/zipkin

# Configuration
TRACING_ENABLED=true
TRACING_PROVIDER=zipkin
TRACING_ENDPOINT=http://localhost:9411/api/v2/spans
```

**UI Access:** http://localhost:9411

### 3. OpenTelemetry (OTLP)

**Features:**
- Vendor-neutral
- Flexible backends
- Future-proof

**Setup:**
```bash
# Using OpenTelemetry Collector
docker run -d \
  --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  otel/opentelemetry-collector

# Configuration
TRACING_ENABLED=true
TRACING_PROVIDER=otlp
TRACING_ENDPOINT=http://localhost:4317
```

## Implementation

### Tracing Decorator

Use the tracing decorator for automatic instrumentation:

```python
from utils.tracing import trace_function

@trace_function(name="process_message")
async def process_message(message: str):
    # Function automatically traced
    result = await some_operation(message)
    return result
```

### Manual Tracing

For fine-grained control:

```python
from utils.tracing import get_tracer

tracer = get_tracer(__name__)

async def complex_operation():
    with tracer.start_as_current_span("database_query") as span:
        # Add attributes
        span.set_attribute("query.type", "SELECT")
        span.set_attribute("query.table", "messages")
        
        # Execute operation
        result = await db.execute(query)
        
        # Add events
        span.add_event("query_completed", {
            "rows_returned": len(result)
        })
        
        return result
```

### Trace Context Propagation

```python
from utils.tracing import inject_trace_context, extract_trace_context

# In HTTP requests
async def make_request():
    headers = {}
    inject_trace_context(headers)
    
    response = await http_client.get(url, headers=headers)
    return response

# In message handlers
async def handle_message(message, context):
    # Extract trace context from message
    with extract_trace_context(context):
        await process_message(message)
```

## Trace Attributes

### Standard Attributes

```python
span.set_attribute("http.method", "POST")
span.set_attribute("http.url", "/api/messages")
span.set_attribute("http.status_code", 200)
span.set_attribute("user.id", user_id)
span.set_attribute("service.name", "chat-system")
```

### Custom Attributes

```python
span.set_attribute("chat.room_id", room_id)
span.set_attribute("chat.message_type", "text")
span.set_attribute("ai.model", "llama2")
span.set_attribute("rag.enabled", True)
```

## Sampling Strategies

### Probabilistic Sampling

```bash
# Sample 10% of requests
TRACING_SAMPLE_RATE=0.1
```

### Conditional Sampling

```python
from utils.tracing import should_sample_trace

# Custom sampling logic
def should_sample(request):
    # Always sample errors
    if request.status_code >= 500:
        return True
    
    # Sample slow requests
    if request.duration > 1.0:
        return True
    
    # Otherwise use default rate
    return should_sample_trace()
```

### Dynamic Sampling

```python
# Adjust sampling based on load
if high_traffic:
    tracer.set_sample_rate(0.01)  # 1% during high traffic
else:
    tracer.set_sample_rate(0.1)   # 10% during normal traffic
```

## Trace Visualization

### Service Map

View service dependencies and call patterns:

1. Open Jaeger UI: http://localhost:16686
2. Click "System Architecture"
3. View service dependency graph

### Trace Timeline

Analyze request flow:

1. Search for traces by service or operation
2. Click on a trace
3. View waterfall timeline of spans
4. Analyze bottlenecks

### Performance Analysis

```
Trace: POST /api/messages (1.2s total)
├─ HTTP Handler (50ms)
├─ AI Processing (800ms) ← Bottleneck
│  ├─ Ollama Request (750ms)
│  └─ Result Processing (50ms)
├─ Database Insert (100ms)
└─ WebSocket Broadcast (250ms)
```

## Monitoring Integration

### Grafana Integration

Connect traces to metrics:

```json
{
  "datasources": [
    {
      "name": "Jaeger",
      "type": "jaeger",
      "url": "http://localhost:16686"
    }
  ]
}
```

### Linking Metrics to Traces

```python
# Add trace_id to logs
logger.info(
    "Request processed",
    extra={
        "trace_id": get_current_trace_id(),
        "span_id": get_current_span_id()
    }
)
```

## Best Practices

### 1. Meaningful Span Names

```python
# Good
with tracer.start_span("user.authenticate")
with tracer.start_span("database.query.users")

# Bad
with tracer.start_span("function1")
with tracer.start_span("do_stuff")
```

### 2. Add Context

```python
span.set_attribute("user.id", user_id)
span.set_attribute("operation.type", "create")
span.set_attribute("resource.id", resource_id)
```

### 3. Handle Errors

```python
try:
    result = await operation()
except Exception as e:
    span.set_status(Status(StatusCode.ERROR))
    span.record_exception(e)
    raise
```

### 4. Appropriate Sampling

```python
# Production: Low sampling for cost
TRACING_SAMPLE_RATE=0.01  # 1%

# Staging: Higher sampling for testing
TRACING_SAMPLE_RATE=0.5   # 50%

# Development: Full sampling
TRACING_SAMPLE_RATE=1.0   # 100%
```

### 5. Trace Important Operations

Priority for tracing:
1. ✅ API endpoints
2. ✅ Database queries
3. ✅ External service calls
4. ✅ AI/RAG operations
5. ❌ Internal utility functions (unless slow)

## Performance Considerations

### Overhead

- **Disabled:** 0% overhead
- **Enabled (1% sampling):** < 0.1% overhead
- **Enabled (100% sampling):** ~1-2% overhead

### Optimization

```python
# Use async tracing to avoid blocking
tracer = get_async_tracer()

# Batch span exports
tracer.set_batch_size(100)
tracer.set_batch_timeout(5)

# Filter out noisy spans
def span_filter(span):
    return span.duration > 0.1  # Only export spans > 100ms
```

## Troubleshooting

### No Traces Appearing

**Problem:** Traces not showing in UI

**Solutions:**
1. Verify tracing is enabled: `TRACING_ENABLED=true`
2. Check tracer connectivity: `curl http://localhost:14268/api/traces`
3. Verify sample rate: `TRACING_SAMPLE_RATE > 0`
4. Check application logs for tracing errors
5. Generate traffic to trigger sampling

**Fallback:** If no traces, system continues normally

### High Overhead

**Problem:** Tracing causing performance issues

**Solutions:**
1. Reduce sample rate: `TRACING_SAMPLE_RATE=0.01`
2. Enable async export
3. Increase batch size
4. Filter out fast operations

### Connection Errors

**Problem:** Cannot connect to tracing backend

**Solutions:**
1. Verify backend is running: `docker ps | grep jaeger`
2. Check endpoint URL in configuration
3. Verify network connectivity
4. Check firewall rules

**Fallback:** Tracing automatically disabled, no errors

## Testing

### Test Tracing Setup

```python
from utils.tracing import get_tracer

async def test_tracing():
    tracer = get_tracer("test")
    
    with tracer.start_as_current_span("test_operation") as span:
        span.set_attribute("test", "value")
        await asyncio.sleep(0.1)
    
    # Verify span was created
    assert span.is_recording()
```

### Generate Test Traces

```bash
# Script to generate test traffic
python scripts/generate_test_traces.py \
  --requests 100 \
  --concurrency 10
```

## Related Documentation

- [Performance Monitoring](PERFORMANCE.md)
- [Grafana Dashboards](GRAFANA_DASHBOARDS.md)
- [Error Tracking](docs/ERROR_TRACKING.md)

## Support

For tracing issues:
1. Check application logs
2. Verify backend is running
3. Test with curl: `curl http://localhost:14268/api/traces`
4. Review OpenTelemetry documentation

**Note:** Tracing is completely optional. Set `TRACING_ENABLED=false` to disable without any impact on functionality.
