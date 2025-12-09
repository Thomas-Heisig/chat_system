# ADR-017: Multi-Tenancy Strategy

**Status:** Accepted  
**Date:** 2025-12-09  
**Decision Makers:** Product Team, Architecture Team, Business Team  
**Tags:** #multi-tenancy #saas #isolation #scalability

---

## Context

The chat system is evolving from a single-organization deployment to a multi-tenant SaaS platform. This transformation requires careful consideration of data isolation, security, scalability, and customization. Current challenges:

1. **Single Tenant Model:** Each customer requires separate deployment
2. **Resource Inefficiency:** Under-utilized servers, high operational costs
3. **Maintenance Burden:** Updates must be deployed to each customer separately
4. **Scaling Difficulty:** Can't efficiently share resources across customers
5. **Pricing Limitations:** Can't offer different service tiers easily
6. **Data Isolation:** Need strong guarantees tenants can't access each other's data
7. **Customization:** Different tenants need different features/configurations

### Current Architecture

```
Customer A → Deployment A → Database A
Customer B → Deployment B → Database B
Customer C → Deployment C → Database C
```

**Problems:**
- 3x infrastructure cost
- 3x maintenance effort
- Slow onboarding (new deployment per customer)
- Resource waste (each instance over-provisioned)

### Requirements

1. **Strong Isolation:** Tenants cannot access each other's data
2. **Performance:** No cross-tenant performance impact
3. **Scalability:** Support 1000+ tenants efficiently
4. **Compliance:** Meet data residency and security requirements
5. **Customization:** Per-tenant configuration and features
6. **Cost Efficiency:** Shared infrastructure where possible
7. **Operational Simplicity:** Single deployment to maintain
8. **Data Migration:** Easy tenant onboarding and offboarding

---

## Decision

We will implement **Schema-per-Tenant Multi-Tenancy** as the primary isolation strategy, with support for Database-per-Tenant for enterprise customers requiring maximum isolation.

### 1. Hybrid Isolation Strategy

**Three Isolation Levels:**

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Tenant Context Middleware      │  │
│  └──────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│Shared DB│  │Schema   │  │Dedicated │
│(Small)  │  │Per-Tenant│ │Database  │
│         │  │(Standard)│  │(Enterprise)│
└─────────┘  └─────────┘  └──────────┘
```

**Level 1: Shared Database (Small Tenants)**
- Single database, tenant_id column
- Lowest cost, highest density
- For: Free/trial accounts, small teams (< 10 users)
- ~1000 tenants per database

**Level 2: Schema-per-Tenant (Standard)**
- Dedicated PostgreSQL schema per tenant
- Good isolation, moderate cost
- For: Standard customers (10-100 users)
- ~100 schemas per database

**Level 3: Database-per-Tenant (Enterprise)**
- Completely separate database
- Maximum isolation and control
- For: Enterprise customers, compliance requirements
- One database per tenant

### 2. Tenant Identification

**Subdomain-based (Primary):**
```
https://acme.chat-system.com  → Tenant: acme
https://widgets.chat-system.com → Tenant: widgets
```

**Header-based (Alternative):**
```http
X-Tenant-ID: acme-corp
```

**Path-based (Fallback):**
```
https://chat-system.com/t/acme/messages
```

### 3. Tenant Context Management

**Middleware Implementation:**
```python
class TenantContextMiddleware:
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from subdomain
        host = request.headers.get("host", "")
        subdomain = host.split(".")[0]
        
        # Load tenant configuration
        tenant = await tenant_repository.get_by_subdomain(subdomain)
        if not tenant:
            raise TenantNotFound()
        
        # Validate tenant status
        if tenant.status != "active":
            raise TenantSuspended()
        
        # Set tenant context
        request.state.tenant = tenant
        
        # Set database schema/connection
        if tenant.isolation_level == "schema":
            await set_schema(tenant.schema_name)
        elif tenant.isolation_level == "database":
            await set_database(tenant.database_url)
        
        response = await call_next(request)
        return response
```

### 4. Database Schema Design

**Shared Schema Model:**
```sql
-- All tables have tenant_id
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    content TEXT,
    created_at TIMESTAMP,
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Compound index for tenant queries
CREATE INDEX idx_messages_tenant ON messages(tenant_id, created_at);

-- Row-level security
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON messages
    USING (tenant_id = current_setting('app.tenant_id')::VARCHAR);
```

**Schema-per-Tenant Model:**
```sql
-- Create schema for each tenant
CREATE SCHEMA tenant_acme;
CREATE SCHEMA tenant_widgets;

-- Each schema has full table set
CREATE TABLE tenant_acme.messages (
    id UUID PRIMARY KEY,
    content TEXT,
    created_at TIMESTAMP
);

-- Set search_path per request
SET search_path TO tenant_acme;
```

### 5. Tenant Data Model

```python
class Tenant(Base):
    """Tenant/Organization model."""
    __tablename__ = "tenants"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    
    # Isolation configuration
    isolation_level = Column(Enum("shared", "schema", "database"))
    database_url = Column(String(500))  # For database-per-tenant
    schema_name = Column(String(100))   # For schema-per-tenant
    
    # Subscription details
    plan = Column(String(50))  # free, standard, enterprise
    status = Column(String(20))  # active, suspended, trial
    max_users = Column(Integer)
    max_storage_gb = Column(Integer)
    
    # Features
    features = Column(JSON)  # {"ai_enabled": true, "rag_enabled": false}
    settings = Column(JSON)  # Tenant-specific configuration
    
    # Metadata
    created_at = Column(DateTime)
    subscription_expires_at = Column(DateTime)
```

### 6. Tenant Provisioning

**Automated Onboarding:**
```python
class TenantProvisioningService:
    async def create_tenant(
        self,
        name: str,
        subdomain: str,
        plan: str = "free"
    ) -> Tenant:
        # 1. Create tenant record
        tenant = Tenant(
            id=generate_tenant_id(),
            name=name,
            subdomain=subdomain,
            plan=plan,
            status="trial"
        )
        
        # 2. Determine isolation level
        if plan == "enterprise":
            tenant.isolation_level = "database"
            await self.provision_database(tenant)
        elif plan in ["standard", "pro"]:
            tenant.isolation_level = "schema"
            await self.provision_schema(tenant)
        else:
            tenant.isolation_level = "shared"
        
        # 3. Create admin user
        admin_user = await self.create_admin_user(tenant)
        
        # 4. Send welcome email
        await self.send_welcome_email(admin_user)
        
        return tenant
    
    async def provision_schema(self, tenant: Tenant):
        schema_name = f"tenant_{tenant.id}"
        tenant.schema_name = schema_name
        
        # Create schema
        await db.execute(f"CREATE SCHEMA {schema_name}")
        
        # Run migrations for schema
        await run_migrations(schema_name)
        
        # Grant permissions
        await db.execute(
            f"GRANT ALL ON SCHEMA {schema_name} TO app_user"
        )
```

---

## Consequences

### Positive

1. **Cost Efficiency:** 10x more tenants per server
2. **Fast Onboarding:** New tenants in seconds, not hours
3. **Simplified Operations:** Single deployment to maintain
4. **Better Resource Utilization:** Shared infrastructure
5. **Flexible Pricing:** Different tiers with different features
6. **Easier Updates:** Deploy once for all tenants
7. **Scalability:** Can serve thousands of tenants
8. **Data Isolation:** Strong guarantees with schema/database isolation
9. **Customization:** Per-tenant features and configuration
10. **Geographic Distribution:** Can place tenants in specific regions

### Negative

1. **Complexity:** More complex than single-tenant
2. **Cross-Tenant Bugs:** Bug in one tenant affects all
3. **Performance Variance:** Noisy neighbor problem possible
4. **Testing Complexity:** Must test multi-tenant scenarios
5. **Migration Effort:** Existing single-tenant customers need migration
6. **Schema Changes:** Migrations affect all tenants
7. **Monitoring Complexity:** Per-tenant metrics needed
8. **Backup Strategy:** More complex backup/restore

### Neutral

1. **Tenant Limits:** Need to enforce resource quotas
2. **Compliance:** May need data residency per region
3. **Customization Limits:** Can't customize everything per tenant
4. **Database Connections:** Need connection pooling strategy

---

## Alternatives Considered

### Alternative 1: Shared Database Only

**Approach:** All tenants in single database with tenant_id

**Pros:**
- Simplest to implement
- Maximum resource sharing
- Lowest cost

**Cons:**
- Weak isolation
- Performance interference
- Compliance challenges
- Single point of failure

**Decision:** Rejected as sole strategy - use for free tier only

---

### Alternative 2: Database-per-Tenant Only

**Approach:** Every tenant gets separate database

**Pros:**
- Maximum isolation
- No performance interference
- Easy to backup/restore per tenant
- Can customize schema per tenant

**Cons:**
- High cost
- Poor resource utilization
- Complex to maintain
- Connection pool limitations

**Decision:** Rejected as sole strategy - use for enterprise only

---

### Alternative 3: Shard by Tenant

**Approach:** Distribute tenants across database shards

**Pros:**
- Good scalability
- Distributes load

**Cons:**
- Very complex
- Cross-shard queries difficult
- Rebalancing complexity

**Decision:** Rejected - over-engineered for current needs

---

### Alternative 4: Kubernetes Namespace per Tenant

**Approach:** Deploy separate pod per tenant

**Pros:**
- Strong isolation
- Easy to scale per tenant
- Resource limits per tenant

**Cons:**
- High resource overhead
- Complex orchestration
- Slower than shared application

**Decision:** Rejected - too resource intensive

---

## Implementation

### Phase 1: Foundation (Estimated: 16 hours)

1. **Tenant Model & Repository:**
   - Create tenant table
   - Implement tenant CRUD
   - Add tenant caching

2. **Tenant Context Middleware:**
   - Subdomain extraction
   - Tenant loading
   - Schema switching
   - Error handling

3. **Provisioning Service:**
   - Tenant creation
   - Schema provisioning
   - Admin user creation

### Phase 2: Schema Isolation (Estimated: 12 hours)

1. **Schema Management:**
   - Schema creation automation
   - Migration runner for schemas
   - Schema cleanup on tenant delete

2. **Connection Management:**
   - Schema-aware connection factory
   - Connection pooling per schema
   - Query routing

3. **Testing:**
   - Multi-tenant test framework
   - Schema isolation tests
   - Performance tests

### Phase 3: Features & Limits (Estimated: 12 hours)

1. **Resource Quotas:**
   - User limits enforcement
   - Storage limits
   - Rate limiting per tenant

2. **Feature Flags:**
   - Per-tenant feature configuration
   - Feature access control
   - Usage tracking

3. **Billing Integration:**
   - Usage metering
   - Subscription management
   - Plan upgrades/downgrades

---

## Security Considerations

### 1. Data Isolation

**Row-Level Security (Shared DB):**
```sql
CREATE POLICY tenant_isolation ON messages
USING (tenant_id = current_setting('app.tenant_id')::VARCHAR);
```

**Schema Isolation (Schema-per-Tenant):**
```python
# Set schema before each query
await connection.execute(f"SET search_path TO {tenant.schema_name}")
```

**Database Isolation (Database-per-Tenant):**
```python
# Use separate connection pool per tenant
connection = tenant_connection_pools[tenant.id].get_connection()
```

### 2. Subdomain Validation

```python
def validate_subdomain(subdomain: str) -> bool:
    # Alphanumeric and hyphens only
    if not re.match(r'^[a-z0-9-]+$', subdomain):
        return False
    
    # Reserved subdomains
    if subdomain in ['www', 'api', 'admin', 'app']:
        return False
    
    # Check availability
    return not tenant_repository.exists(subdomain)
```

### 3. Cross-Tenant Prevention

**All queries must include tenant context:**
```python
# ❌ BAD - no tenant filter
messages = await db.query(Message).all()

# ✅ GOOD - tenant filtered
messages = await db.query(Message).filter(
    Message.tenant_id == current_tenant.id
).all()
```

**Automated checks:**
```python
@enforce_tenant_isolation
async def get_messages():
    # Decorator ensures tenant_id filter
    return await message_service.get_all()
```

---

## Monitoring and Observability

### Key Metrics

1. **Per-Tenant Metrics:**
   - Active users per tenant
   - Storage usage per tenant
   - API requests per tenant
   - Error rate per tenant

2. **System Metrics:**
   - Total tenants
   - Tenants per isolation level
   - Schema count
   - Connection pool usage

3. **Performance Metrics:**
   - Schema switching time
   - Query latency per tenant
   - Cross-tenant performance variance

### Alerting

- Critical: Cross-tenant data leak detected
- Warning: Tenant over quota
- Warning: Tenant approaching limits
- Info: New tenant provisioned

---

## Compliance and Data Residency

### GDPR Compliance

**Data Location:**
```python
class Tenant(Base):
    data_region = Column(String(50))  # eu-west, us-east, asia
    
    # Can route to region-specific database
    @property
    def database_url(self):
        return REGIONAL_DATABASES[self.data_region]
```

**Data Export:**
```python
async def export_tenant_data(tenant_id: str) -> bytes:
    """Export all tenant data for GDPR compliance."""
    data = {
        "messages": await export_messages(tenant_id),
        "users": await export_users(tenant_id),
        "files": await export_files(tenant_id)
    }
    return json.dumps(data).encode()
```

**Data Deletion:**
```python
async def delete_tenant_data(tenant_id: str):
    """Complete tenant data deletion."""
    if tenant.isolation_level == "database":
        await drop_database(tenant.database_name)
    elif tenant.isolation_level == "schema":
        await drop_schema(tenant.schema_name)
    else:
        await delete_all_rows(tenant_id)
```

---

## Testing Strategy

### 1. Isolation Tests
```python
async def test_tenant_isolation():
    """Ensure tenant A cannot access tenant B data."""
    tenant_a = await create_test_tenant("tenant-a")
    tenant_b = await create_test_tenant("tenant-b")
    
    # Create message in tenant A
    async with tenant_context(tenant_a):
        msg = await create_message("secret")
    
    # Try to access from tenant B
    async with tenant_context(tenant_b):
        messages = await get_all_messages()
        assert len(messages) == 0  # Cannot see tenant A's data
```

### 2. Performance Tests
```python
async def test_multi_tenant_performance():
    """Verify no cross-tenant performance impact."""
    tenants = [await create_test_tenant(f"t{i}") for i in range(10)]
    
    # Heavy load on tenant 1
    async with tenant_context(tenants[0]):
        await heavy_load()
    
    # Verify tenant 2 performance unchanged
    async with tenant_context(tenants[1]):
        latency = await measure_query_latency()
        assert latency < 100  # ms
```

### 3. Migration Tests
```python
async def test_tenant_migration():
    """Test moving tenant between isolation levels."""
    tenant = await create_tenant(isolation_level="shared")
    
    # Migrate to schema
    await migrate_to_schema(tenant)
    
    # Verify data intact
    assert await verify_data_integrity(tenant)
```

---

## Migration Path

### Phase 1: Infrastructure (Month 1)
- Deploy multi-tenant capable code
- No tenants using it yet
- Test with synthetic tenants

### Phase 2: New Tenants (Month 2)
- All new sign-ups are tenants
- Existing customers still single-tenant
- Monitor and optimize

### Phase 3: Existing Customer Migration (Month 3-6)
- Migrate willing customers
- Offer incentives (cost savings)
- Keep option for dedicated deployment

### Phase 4: Full Multi-Tenant (Month 6+)
- All customers on multi-tenant platform
- Retire single-tenant deployments
- Optimize for scale

---

## Success Criteria

1. **Density:** Support 100+ tenants per database server
2. **Isolation:** Zero cross-tenant data leaks
3. **Performance:** < 10ms overhead for tenant context
4. **Onboarding:** New tenant ready in < 30 seconds
5. **Cost:** 70% reduction in infrastructure cost per customer
6. **Compliance:** Pass security audit

---

## Approval

**Approved By:**
- Chief Technology Officer
- VP of Product
- Head of Security
- VP of Engineering

**Date:** 2025-12-09

---

## References

- [Multi-Tenancy Patterns - Microsoft](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [SaaS Tenant Isolation - AWS](https://aws.amazon.com/blogs/apn/saas-tenant-isolation-strategies/)
- [MULTI_TENANCY.md](../MULTI_TENANCY.md) - Implementation Guide
- Implementation: `core/tenant_context.py`, `middleware/tenant_middleware.py`

---

## Related ADRs

- ADR-013: Database Read Replicas (scales multi-tenant reads)
- ADR-010: Dependency Injection (tenant context injection)
- ADR-016: Event Sourcing (per-tenant event streams)

---

**Last Updated:** 2025-12-09  
**Next Review:** Q3 2026 (after 6 months in production)
