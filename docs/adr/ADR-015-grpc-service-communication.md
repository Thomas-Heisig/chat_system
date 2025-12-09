# ADR-015: gRPC Service Communication

**Status:** Accepted  
**Date:** 2025-12-09  
**Decision Makers:** Architecture Team, Backend Team, DevOps Team  
**Tags:** #microservices #grpc #performance #internal-communication

---

## Context

As the chat system evolves toward a microservices architecture, internal service-to-service communication has become a performance bottleneck. Current challenges:

1. **HTTP/JSON Overhead:** Text-based JSON adds significant serialization/parsing overhead
2. **Network Latency:** Multiple HTTP round-trips for complex operations
3. **Service Coupling:** REST APIs designed for external clients, not internal services
4. **Type Safety:** JSON lacks compile-time type checking between services
5. **Bandwidth Usage:** JSON is verbose, consuming significant network bandwidth
6. **API Evolution:** Breaking changes difficult to manage across services

### Current Architecture

```
┌─────────────┐      HTTP/JSON      ┌─────────────┐
│  Message    │ ───────────────────► │     AI      │
│  Service    │                      │   Service   │
└─────────────┘                      └─────────────┘
     │                                      │
     │          HTTP/JSON                   │
     └──────────────────────────────────────┘
```

**Problems:**
- Each request: TCP handshake + HTTP headers + JSON encoding
- No connection reuse between services
- Error handling inconsistent
- No automatic retry logic
- Difficult to version APIs

### Requirements

1. **High Performance:** Low latency internal communication
2. **Type Safety:** Strongly typed contracts between services
3. **Efficient:** Binary protocol with minimal overhead
4. **Bidirectional Streaming:** Support real-time data flows
5. **External Compatibility:** Keep REST/GraphQL for external clients
6. **Developer Experience:** Code generation from interface definitions
7. **Backward Compatibility:** Support API versioning

---

## Decision

We will implement **gRPC for internal service-to-service communication** using Protocol Buffers, while maintaining HTTP/JSON REST and GraphQL APIs for external clients.

### 1. Communication Pattern

**Two-Tier API Architecture:**

```
┌─────────────────┐
│  External Client│
│   (REST/HTTP)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Gateway   │  ← External: HTTP/JSON REST + GraphQL
│  (FastAPI)      │  ← Internal: gRPC
└────────┬────────┘
         │
         ├──────► HTTP/JSON (External)
         │
         └──────► gRPC (Internal)
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│ Message Service │   │  AI Service     │
│     (gRPC)      │   │    (gRPC)       │
└─────────────────┘   └─────────────────┘
```

**Rationale:**
- External clients: Human-friendly REST/GraphQL (ease of use)
- Internal services: High-performance gRPC (efficiency)
- Best of both worlds

### 2. Technology Stack

**Core Components:**
- **gRPC:** Latest stable version (1.59+)
- **Protocol Buffers:** proto3 syntax
- **Python gRPC:** grpcio, grpcio-tools
- **Reflection:** grpcio-reflection for debugging

**Why gRPC:**
- HTTP/2 based (multiplexing, header compression)
- Binary protocol (smaller, faster than JSON)
- Built-in code generation
- Strong ecosystem and tooling
- Streaming support (unary, server, client, bidirectional)

### 3. Protocol Buffer Schema

**Service Definitions in `.proto` Files:**

```protobuf
syntax = "proto3";

package chat.v1;

service MessageService {
  // Unary RPC
  rpc GetMessage(GetMessageRequest) returns (MessageResponse);
  
  // Server streaming
  rpc StreamMessages(StreamRequest) returns (stream MessageResponse);
  
  // Client streaming
  rpc SendMessages(stream MessageRequest) returns (SendResponse);
  
  // Bidirectional streaming
  rpc ChatStream(stream ChatMessage) returns (stream ChatMessage);
}

message GetMessageRequest {
  string message_id = 1;
  bool include_user = 2;
  bool include_files = 3;
}

message MessageResponse {
  string id = 1;
  string content = 2;
  int64 created_at = 3;
  User user = 4;
  repeated File files = 5;
}
```

**Benefits:**
- Single source of truth
- Versioned contracts
- Automatic validation
- Cross-language support

### 4. Service Implementation Pattern

**Service Class:**
```python
from grpc_services.protos import message_pb2_grpc
from grpc_services.protos import message_pb2

class MessageServiceImpl(message_pb2_grpc.MessageServiceServicer):
    def __init__(self):
        self.service = get_message_service()
    
    async def GetMessage(self, request, context):
        try:
            message = await self.service.get_by_id(request.message_id)
            return message_pb2.MessageResponse(
                id=message.id,
                content=message.content,
                created_at=int(message.created_at.timestamp())
            )
        except NotFound:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Message not found')
            raise
```

**Client Usage:**
```python
async with grpc.aio.insecure_channel('message-service:50051') as channel:
    stub = message_pb2_grpc.MessageServiceStub(channel)
    response = await stub.GetMessage(
        message_pb2.GetMessageRequest(message_id="123")
    )
```

### 5. Connection Management

**Connection Pooling:**
- Persistent connections between services
- HTTP/2 multiplexing for concurrent requests
- Automatic reconnection on failure
- Load balancing support

**Health Checking:**
```python
# Built-in gRPC health checking
from grpc_health.v1 import health_pb2_grpc

health_servicer = health.HealthServicer()
health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
```

### 6. Security

**TLS/mTLS for Production:**
```python
# Server with TLS
server_credentials = grpc.ssl_server_credentials(
    private_key_certificate_chain_pairs=[
        (private_key, certificate_chain)
    ]
)
server.add_secure_port('[::]:50051', server_credentials)

# Client with TLS
channel_credentials = grpc.ssl_channel_credentials(root_certificates)
channel = grpc.aio.secure_channel('service:50051', channel_credentials)
```

**Service Authentication:**
- Mutual TLS (mTLS) for service identity
- Token-based authentication as backup
- Network policies for additional security

---

## Consequences

### Positive

1. **Performance Improvement:** 3-5x faster than JSON/HTTP
2. **Reduced Latency:** HTTP/2 multiplexing eliminates head-of-line blocking
3. **Bandwidth Savings:** 30-50% reduction vs JSON
4. **Type Safety:** Compile-time checking prevents integration errors
5. **Streaming:** Native support for real-time data flows
6. **Code Generation:** Auto-generated client/server code
7. **Backward Compatibility:** Protobuf versioning supports evolution
8. **Error Handling:** Rich status codes and error details
9. **Tooling:** Excellent debugging and monitoring tools
10. **Cross-Language:** Easy to add services in other languages

### Negative

1. **Learning Curve:** Team needs to learn Protocol Buffers and gRPC
2. **Debugging Complexity:** Binary protocol harder to inspect than JSON
3. **Tooling Requirements:** Need protoc compiler and plugins
4. **Browser Support:** Limited direct browser support (needs proxy)
5. **Infrastructure:** Additional ports and network configuration
6. **Schema Management:** Proto files need version control
7. **Testing Complexity:** Need gRPC-specific testing tools
8. **Operational Overhead:** More services to monitor

### Neutral

1. **Dual Protocol Maintenance:** Both HTTP/JSON and gRPC
2. **Schema Definitions:** Proto files as additional artifact
3. **Code Generation:** Build process more complex
4. **Service Discovery:** Need service registry or DNS

---

## Alternatives Considered

### Alternative 1: Stick with REST/HTTP/JSON

**Pros:**
- No new technology
- Familiar to team
- Easy debugging
- Universal support

**Cons:**
- Performance overhead
- No type safety
- Verbose protocol
- Poor streaming support

**Decision:** Rejected - performance critical for internal services

---

### Alternative 2: Apache Thrift

**Pros:**
- Binary protocol
- Code generation
- Multi-language support

**Cons:**
- Smaller ecosystem than gRPC
- Less active development
- Limited streaming
- Complex setup

**Decision:** Rejected - gRPC has better ecosystem and HTTP/2

---

### Alternative 3: MessageQueue (RabbitMQ/Kafka)

**Pros:**
- Decoupled services
- Async by default
- Excellent for events

**Cons:**
- Higher latency (async)
- Not suitable for request-response
- Additional infrastructure
- More complex

**Decision:** Complementary - use for events, not request-response

---

### Alternative 4: GraphQL Federation

**Pros:**
- Unified schema
- Good for external APIs
- Type-safe

**Cons:**
- Text-based (slower than binary)
- Complex federation setup
- Overhead for simple calls
- Learning curve

**Decision:** Rejected - use GraphQL for external API only

---

## Implementation

### Phase 1: Foundation (Estimated: 8 hours)

1. **Setup Infrastructure:**
   ```bash
   pip install grpcio==1.59.0 grpcio-tools==1.59.0
   ```

2. **Define Proto Files:**
   - Create `grpc_services/protos/` directory
   - Define core service interfaces
   - Version services (e.g., `chat.v1`)

3. **Code Generation:**
   ```bash
   python -m grpc_tools.protoc \
     --proto_path=grpc_services/protos \
     --python_out=. \
     --grpc_python_out=. \
     grpc_services/protos/*.proto
   ```

4. **Build Integration:**
   - Add to CI/CD pipeline
   - Automate code generation
   - Version control generated files

### Phase 2: First Service (Estimated: 8 hours)

1. **Message Service:**
   - Implement gRPC server
   - Migrate from REST to gRPC internally
   - Add health checks
   - Add metrics

2. **Client Library:**
   - Create Python client wrapper
   - Add connection pooling
   - Add retry logic
   - Add timeout handling

3. **Testing:**
   - Unit tests for service
   - Integration tests
   - Load testing

### Phase 3: Additional Services (Estimated: 8 hours)

1. **AI Service:**
   - Streaming support for long responses
   - Async processing

2. **RAG Service:**
   - Document processing
   - Vector search

3. **Plugin Service:**
   - Plugin communication
   - Event streaming

---

## Security Considerations

### 1. Network Isolation

Internal gRPC services should NOT be exposed to public internet:
```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: grpc-internal-only
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              tier: backend
```

### 2. Authentication

**Mutual TLS (Recommended):**
- Each service has certificate
- Mutual authentication
- Encrypted communication

**Token-Based (Alternative):**
```python
class AuthInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get('authorization')
        if not validate_token(token):
            raise grpc.RpcError(grpc.StatusCode.UNAUTHENTICATED)
        return await continuation(handler_call_details)
```

### 3. Rate Limiting

Apply rate limits per service:
```python
@with_rate_limit(requests_per_second=1000)
async def GetMessage(self, request, context):
    pass
```

---

## Monitoring and Observability

### Key Metrics

1. **RPC Metrics:**
   - Requests per second
   - Latency (p50, p95, p99)
   - Error rate
   - Active connections

2. **Stream Metrics:**
   - Stream duration
   - Messages per stream
   - Stream errors

3. **Service Health:**
   - Connection pool status
   - Service availability
   - Retry counts

### Integration

Add to Prometheus:
```python
from prometheus_client import Histogram, Counter

grpc_request_duration = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request duration',
    ['service', 'method']
)

grpc_requests_total = Counter(
    'grpc_requests_total',
    'Total gRPC requests',
    ['service', 'method', 'status']
)
```

### Distributed Tracing

Integrate with OpenTelemetry:
```python
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
GrpcInstrumentorClient().instrument()
```

---

## Testing Strategy

### 1. Unit Tests
```python
@pytest.mark.asyncio
async def test_get_message():
    servicer = MessageServiceImpl()
    request = message_pb2.GetMessageRequest(message_id="123")
    response = await servicer.GetMessage(request, mock_context)
    assert response.id == "123"
```

### 2. Integration Tests
```python
@pytest.mark.asyncio
async def test_grpc_client():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = MessageServiceStub(channel)
        response = await stub.GetMessage(GetMessageRequest(message_id="123"))
        assert response.content is not None
```

### 3. Load Tests
Use ghz (gRPC load testing tool):
```bash
ghz --insecure \
  --proto grpc_services/protos/message.proto \
  --call chat.v1.MessageService/GetMessage \
  -d '{"message_id":"123"}' \
  -n 10000 -c 100 \
  localhost:50051
```

---

## Migration Path

### Phase 1: Parallel Operation (Week 1-2)
- Deploy gRPC alongside REST
- No services use gRPC yet
- Test infrastructure

### Phase 2: Internal Migration (Week 3-4)
- Migrate Message Service communication
- Monitor performance
- Gather feedback

### Phase 3: Full Adoption (Week 5-6)
- Migrate all internal services
- Optimize performance
- Document patterns

### Phase 4: Optimization (Ongoing)
- Profile slow RPCs
- Add caching where appropriate
- Tune connection pools

---

## Success Criteria

1. **Performance:** 50%+ reduction in service-to-service latency
2. **Reliability:** 99.9% RPC success rate
3. **Bandwidth:** 30%+ reduction in network traffic
4. **Developer Experience:** Positive team feedback
5. **Type Safety:** Zero runtime type errors between services
6. **Monitoring:** Full observability of gRPC calls

---

## Approval

**Approved By:**
- Lead Backend Engineer
- DevOps Team Lead
- System Architect

**Date:** 2025-12-09

---

## References

- [gRPC Official Documentation](https://grpc.io/docs/)
- [Protocol Buffers Documentation](https://protobuf.dev/)
- [GRPC_SERVICES.md](../GRPC_SERVICES.md) - Implementation Guide
- Implementation: `grpc_services/`, `grpc_services/protos/`

---

## Related ADRs

- ADR-010: Dependency Injection Pattern (for gRPC service dependencies)
- ADR-014: GraphQL API Strategy (external API, complements gRPC)
- Future: Service mesh decision (Istio/Linkerd) - will be evaluated in 2026 Q4 when scaling to 50+ microservices

---

**Last Updated:** 2025-12-09  
**Next Review:** Q3 2026 (after 6 months in production)
