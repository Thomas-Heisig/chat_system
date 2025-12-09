# ADR-014: GraphQL API Strategy

**Status:** Accepted  
**Date:** 2025-12-09  
**Decision Makers:** API Team, Frontend Team, System Architects  
**Tags:** #api #graphql #frontend #performance

---

## Context

The chat system currently exposes a comprehensive REST API for all operations. While REST has served us well, several challenges have emerged:

1. **Over-fetching:** Clients receive more data than needed (e.g., full user objects when only name needed)
2. **Under-fetching:** Multiple requests needed to assemble related data (N+1 request problem)
3. **API Versioning:** Breaking changes require new API versions
4. **Frontend Complexity:** Complex state management for data assembly
5. **Mobile Bandwidth:** Excessive data transfer on mobile networks
6. **Developer Experience:** Manual API documentation maintenance

### Current API Pattern

```
GET /api/messages/{id}          → Returns full message
GET /api/users/{userId}         → Separate request for user
GET /api/files/{fileId}         → Separate request for attachments
```

**Result:** 3+ requests to display a single message with user info and attachments.

### Requirements

1. **Flexible Queries:** Clients specify exactly what data they need
2. **Single Request:** Fetch related data in one round trip
3. **Type Safety:** Strong typing for better developer experience
4. **API Evolution:** Add fields without breaking existing clients
5. **REST Compatibility:** Maintain existing REST API (no breaking changes)
6. **Performance:** Reduce network overhead and server load
7. **Developer Tools:** Excellent introspection and playground

---

## Decision

We will implement **GraphQL API Gateway** using Strawberry GraphQL, running in parallel with the existing REST API.

### 1. Technology Choice: Strawberry GraphQL

**Why Strawberry:**
- Native Python type hints (no separate schema files)
- Excellent FastAPI integration
- Modern async/await support
- DataLoader support for N+1 prevention
- Active development and community

**Alternative Considered:** Ariadne (schema-first approach)
- Rejected: Requires separate schema files (SDL)
- Rejected: Less type-safe than Strawberry

### 2. Parallel API Strategy

**Both APIs Coexist:**
```
/api/rest/*     → REST API (existing, unchanged)
/graphql        → GraphQL API (new)
/graphql/ui     → GraphQL Playground (dev only)
```

**Benefits:**
- Gradual migration possible
- No breaking changes to existing clients
- Client can choose best API for use case
- REST remains for simple operations
- GraphQL for complex data requirements

### 3. Schema Design Pattern

**Code-First with Python Types:**
```python
@strawberry.type
class Message:
    id: strawberry.ID
    content: str
    created_at: datetime
    user: User  # Relationship
    attachments: List[File]  # Related data

@strawberry.type
class Query:
    @strawberry.field
    async def message(self, id: strawberry.ID) -> Message:
        return await get_message(id)
```

**Advantages:**
- Single source of truth (Python code)
- IDE autocomplete and type checking
- Automatic schema generation
- Refactoring safety

### 4. Resolver Architecture

**Service Layer Integration:**
```python
class QueryResolver:
    def __init__(self):
        self.message_service = get_message_service()
        self.user_service = get_user_service()
    
    async def get_message(self, id: str) -> Message:
        # Reuse existing service layer
        return await self.message_service.get_by_id(id)
```

**Benefits:**
- No business logic duplication
- Consistent behavior REST vs GraphQL
- Easy testing and maintenance

### 5. N+1 Query Prevention

**DataLoader Pattern:**
```python
class UserLoader:
    async def load_batch(self, user_ids: List[str]) -> List[User]:
        # Single database query for multiple users
        return await user_service.get_by_ids(user_ids)

loader = DataLoader(load_fn=UserLoader().load_batch)
```

**Automatic Batching:**
- Collects all user requests
- Makes single batch query
- Dramatically reduces database load

### 6. Query Complexity Limits

**Protection Against Abuse:**
- Maximum query depth: 10 levels
- Maximum complexity score: 1000
- Query timeout: 30 seconds
- Rate limiting per client

---

## Consequences

### Positive

1. **Better Client Experience:** Clients request exactly what they need
2. **Reduced Network Traffic:** 60-80% fewer bytes transferred
3. **Single Round Trip:** Related data fetched together
4. **Strong Typing:** Compile-time type checking
5. **Self-Documenting:** Introspection provides live documentation
6. **API Evolution:** Add fields without versioning
7. **Developer Productivity:** GraphQL Playground for testing
8. **Mobile Optimized:** Reduces bandwidth on mobile devices
9. **Gradual Adoption:** Can migrate incrementally
10. **No Breaking Changes:** REST API unchanged

### Negative

1. **Learning Curve:** Team needs GraphQL knowledge
2. **Query Complexity:** Need monitoring and limits
3. **Caching Challenges:** More complex than REST caching
4. **Infrastructure Overhead:** Additional endpoint to maintain
5. **Testing Complexity:** More query variations to test
6. **Security Considerations:** Query depth limits required
7. **Monitoring:** Need GraphQL-specific metrics

### Neutral

1. **Dual API Maintenance:** Both REST and GraphQL to support
2. **Documentation:** Need docs for both APIs
3. **Client Libraries:** Different libraries for GraphQL
4. **Tooling:** Additional tools for GraphQL development

---

## Alternatives Considered

### Alternative 1: REST API with Field Selection

**Approach:** Add `?fields=id,name,email` parameter to REST

**Pros:**
- No new technology
- Simple to implement
- Familiar to developers

**Cons:**
- Doesn't solve related data fetching
- Still requires multiple requests
- Limited flexibility
- No strong typing

**Decision:** Rejected - doesn't solve core problems

---

### Alternative 2: JSON:API Specification

**Approach:** Adopt JSON:API standard for REST

**Pros:**
- Standardized approach
- Includes relationships
- Pagination standards

**Cons:**
- Verbose responses
- Complex to implement
- Still multiple requests for deep nesting
- Limited adoption

**Decision:** Rejected - complexity without GraphQL benefits

---

### Alternative 3: gRPC for All Clients

**Approach:** Replace REST with gRPC

**Pros:**
- High performance
- Strong typing
- Efficient binary protocol

**Cons:**
- Poor browser support
- Not web-friendly
- Breaking change for clients
- Complex for simple queries

**Decision:** Rejected - not suitable for web/mobile clients

---

### Alternative 4: BFF (Backend for Frontend) Pattern

**Approach:** Custom API per client type

**Pros:**
- Optimized for each client
- Full control over responses

**Cons:**
- Massive duplication
- Hard to maintain
- Doesn't scale with clients
- High development cost

**Decision:** Rejected - too much maintenance overhead

---

## Implementation

### Phase 1: Foundation (Estimated: 8 hours)

1. **Install Dependencies:**
   ```bash
   pip install strawberry-graphql[fastapi]
   ```

2. **Create Schema Types:**
   - Define GraphQL types for core entities
   - Map to existing database models
   - Add relationships

3. **Setup GraphQL Endpoint:**
   - Configure Strawberry with FastAPI
   - Add to main application
   - Enable playground for development

### Phase 2: Core Queries (Estimated: 6 hours)

1. **Implement Query Resolvers:**
   - Messages (list, single)
   - Users (list, single)
   - Projects (list, single)
   - Search functionality

2. **Add DataLoaders:**
   - User loader
   - File loader
   - Related data loaders

3. **Add Pagination:**
   - Cursor-based pagination
   - Limit/offset support

### Phase 3: Mutations (Estimated: 4 hours)

1. **Write Operations:**
   - Create message
   - Update message
   - Delete message

2. **Authentication Integration:**
   - JWT token validation
   - Permission checking
   - User context

### Phase 4: Advanced Features (Estimated: 2 hours)

1. **Subscriptions (Optional):**
   - Real-time message updates
   - WebSocket integration

2. **Query Optimization:**
   - Complexity analysis
   - Depth limiting
   - Performance monitoring

---

## Security Considerations

### 1. Query Depth Limiting
```python
GRAPHQL_QUERY_DEPTH_LIMIT = 10
```
Prevents deeply nested queries that could DOS the server.

### 2. Query Complexity Scoring
```python
GRAPHQL_COMPLEXITY_LIMIT = 1000
```
Each field has cost, total must not exceed limit.

### 3. Rate Limiting
Apply same rate limits as REST API per authenticated user.

### 4. Authentication
```python
@strawberry.field
async def current_user(self, info) -> User:
    user = info.context.user  # From JWT token
    if not user:
        raise Unauthorized()
    return user
```

### 5. Authorization
Check permissions in resolvers, same as REST API.

---

## Performance Optimization

### 1. DataLoader Pattern
Batch and cache database queries automatically.

### 2. Query Caching
Cache results of expensive queries:
```python
@cached(ttl=300)
async def get_messages():
    return await fetch_messages()
```

### 3. Persisted Queries
Pre-approved query hashes for production:
- Reduces bandwidth
- Improves security
- Enables caching

### 4. Response Compression
Apply compression middleware (already implemented).

---

## Monitoring and Observability

### Key Metrics

1. **Query Metrics:**
   - Query execution time (p50, p95, p99)
   - Query complexity scores
   - Most expensive queries

2. **Resolver Performance:**
   - Slowest resolvers
   - Most called resolvers
   - N+1 query detection

3. **Error Rates:**
   - GraphQL errors by type
   - Failed queries
   - Validation errors

4. **Usage Patterns:**
   - Most used queries
   - Query depth distribution
   - Field usage statistics

### Integration

Add to existing Prometheus metrics:
```python
graphql_query_duration = Histogram(
    'graphql_query_duration_seconds',
    'GraphQL query execution time'
)
```

---

## Testing Strategy

### 1. Schema Testing
```python
def test_schema_validity():
    schema = strawberry.Schema(query=Query)
    assert schema is not None
```

### 2. Resolver Testing
```python
async def test_message_query():
    result = await execute_query("""
        query {
            message(id: "123") {
                id
                content
            }
        }
    """)
    assert result.data['message']['id'] == '123'
```

### 3. Integration Testing
Test complete queries with authentication and database.

### 4. Performance Testing
Measure N+1 query prevention effectiveness.

---

## Migration Path

### Phase 1: Internal Testing (Week 1)
- Deploy GraphQL endpoint
- Enable only in development
- Team testing and feedback

### Phase 2: Beta Release (Week 2-3)
- Enable for beta testers
- Monitor performance and errors
- Gather feedback

### Phase 3: Gradual Rollout (Week 4)
- Enable for all users
- Document GraphQL API
- Create client examples

### Phase 4: Optimization (Week 5+)
- Monitor usage patterns
- Optimize slow queries
- Add missing features

---

## Documentation Requirements

1. **GraphQL Schema Documentation:**
   - Auto-generated from schema
   - Available via introspection
   - GraphQL Playground

2. **Query Examples:**
   - Common query patterns
   - Pagination examples
   - Authentication examples

3. **Migration Guide:**
   - REST to GraphQL equivalents
   - Best practices
   - Performance tips

4. **Client Integration:**
   - JavaScript/TypeScript example
   - Python client example
   - Mobile app example

---

## Success Criteria

1. **Performance:** 50% reduction in client-side requests
2. **Bandwidth:** 30-40% reduction in data transfer
3. **Developer Experience:** Positive feedback from team
4. **Adoption:** 20% of API traffic via GraphQL within 3 months
5. **Stability:** No increase in error rates
6. **Documentation:** Complete GraphQL docs available

---

## Approval

**Approved By:**
- Lead Backend Engineer
- Frontend Team Lead
- Mobile Team Lead
- API Product Manager

**Date:** 2025-12-09

---

## References

- [GraphQL Official Documentation](https://graphql.org/)
- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [GRAPHQL_API.md](../GRAPHQL_API.md) - Implementation Guide
- Implementation: `graphql_api/schema.py`, `graphql_api/resolvers.py`

---

## Related ADRs

- ADR-010: Dependency Injection Pattern (for resolver dependencies)
- ADR-012: Error Handling Centralization (for GraphQL errors)
- ADR-015: gRPC Service Communication (for internal service communication)

---

**Last Updated:** 2025-12-09  
**Next Review:** Q2 2026 (after 6 months in production)
