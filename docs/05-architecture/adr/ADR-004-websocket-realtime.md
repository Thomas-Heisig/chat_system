# ADR-004: WebSocket for Real-Time Communication

## Status
Accepted

## Date
2024-12-01

## Context
The Universal Chat System required real-time bidirectional communication for:
- Instant message delivery
- User presence updates
- Live notifications
- Real-time collaboration features
- Low-latency interactions

We needed a technology that provides:
- Full-duplex communication
- Low overhead
- Native browser support
- Good mobile compatibility
- Integration with FastAPI

## Decision
We chose **WebSocket** protocol for real-time communication, implemented using FastAPI's native WebSocket support.

## Consequences

### Positive
- **True bidirectional**: Server can push to clients without polling
- **Low latency**: Persistent connection eliminates handshake overhead
- **Efficient**: Less overhead than HTTP long-polling
- **Native support**: Built into all modern browsers
- **Standardized**: IETF standard (RFC 6455)
- **FastAPI integration**: First-class WebSocket support in FastAPI
- **Connection state**: Easy to track online users
- **Event-driven**: Natural fit for real-time events

### Negative
- **Stateful connections**: Requires maintaining open connections
- **Scaling complexity**: Need to handle connection distribution (sticky sessions or message queue)
- **Resource usage**: Each connection consumes server resources
- **Proxy compatibility**: Some proxies/firewalls may block WebSockets
- **Reconnection logic**: Need client-side reconnection handling
- **Load balancing**: Requires WebSocket-aware load balancers

### Neutral
- **Connection lifecycle**: Must handle connection drops gracefully
- **Authentication**: Need to authenticate WebSocket connections
- **Message format**: Requires choosing message serialization format (JSON)

## Alternatives Considered

### Alternative 1: Server-Sent Events (SSE)
- **Description**: HTTP-based server-to-client streaming
- **Pros**:
  - Simpler than WebSockets
  - Built on HTTP (better proxy compatibility)
  - Automatic reconnection
  - Good browser support
- **Cons**:
  - Uni-directional (server to client only)
  - Client still needs HTTP POST for messages
  - Connection limit per domain
  - Less efficient than WebSockets
- **Why rejected**: Uni-directional nature requires separate HTTP channel for client messages

### Alternative 2: HTTP Long-Polling
- **Description**: Client repeatedly requests updates from server
- **Pros**:
  - Works everywhere (HTTP only)
  - No special server requirements
  - Simple to implement
- **Cons**:
  - High overhead (repeated HTTP handshakes)
  - Higher latency
  - More server resources
  - Complex state management
- **Why rejected**: Inefficient, high latency, poor user experience

### Alternative 3: Socket.IO
- **Description**: Library that provides real-time capabilities with fallbacks
- **Pros**:
  - Automatic fallback to polling
  - Better cross-browser compatibility
  - Built-in rooms and namespaces
  - Reconnection logic included
- **Cons**:
  - Additional abstraction layer
  - Larger client library
  - Custom protocol (not standard WebSocket)
  - More complexity
  - Less control
- **Why rejected**: Unnecessary abstraction, modern browsers support WebSockets natively

### Alternative 4: WebRTC Data Channels
- **Description**: Peer-to-peer data channels
- **Pros**:
  - Peer-to-peer (can reduce server load)
  - Very low latency
  - Encryption built-in
- **Cons**:
  - Complex setup (signaling server still needed)
  - NAT traversal issues
  - Overkill for simple chat
  - Not suitable for group communication
  - Browser support varies
- **Why rejected**: Overly complex for centralized chat, better for P2P scenarios

### Alternative 5: GraphQL Subscriptions
- **Description**: GraphQL support for real-time updates
- **Pros**:
  - Unified API (queries, mutations, subscriptions)
  - Strong typing
  - Selective data fetching
- **Cons**:
  - Requires GraphQL infrastructure
  - More complexity
  - Still uses WebSockets underneath
  - Overkill for simple messaging
- **Why rejected**: Unnecessary complexity, WebSockets more direct

### Alternative 6: gRPC Streaming
- **Description**: Bidirectional streaming with gRPC
- **Pros**:
  - Efficient binary protocol (Protocol Buffers)
  - Strong typing
  - Multiple language support
- **Cons**:
  - Requires HTTP/2
  - Limited browser support (needs gRPC-Web)
  - More complex setup
  - Overkill for chat messages
- **Why rejected**: Poor browser support, unnecessary complexity for text messaging

## Implementation Details

### Connection Management
- Connection pooling with user session tracking
- Heartbeat/ping-pong for connection health
- Automatic reconnection on client side
- Graceful degradation for connection failures

### Message Format
- JSON-serialized messages for simplicity
- Structured message types (user_message, system_message, notification, etc.)
- Message compression for large payloads

### Scaling Strategy
- Redis pub/sub for multi-server message distribution
- Sticky sessions or consistent hashing for connection routing
- Horizontal scaling with shared message queue

### Authentication
- JWT token validation on WebSocket connection
- Token sent during WebSocket handshake
- Re-authentication on token expiration

## References
- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [WebSocket vs HTTP/2](https://ably.com/topic/websockets-vs-http2)
