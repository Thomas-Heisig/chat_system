# Multi-Tenancy Support

## Overview

This document describes the multi-tenancy implementation for the Chat System, enabling a single application instance to serve multiple isolated tenants (organizations, companies, or user groups). Multi-tenancy provides data isolation, customization per tenant, and efficient resource utilization.

## Configuration

### Environment Variables

```bash
# Multi-Tenancy Configuration
MULTI_TENANCY_ENABLED=false  # Enable multi-tenancy support
TENANT_ISOLATION_STRATEGY=schema  # schema, database, or shared
TENANT_ID_SOURCE=subdomain  # subdomain, header, or path

# Tenant Database Settings
TENANT_DATABASE_PREFIX=tenant_  # Prefix for tenant databases/schemas
TENANT_AUTO_PROVISION=true  # Automatically provision new tenants
TENANT_DEFAULT_PLAN=free  # Default plan for new tenants

# Tenant Limits
TENANT_MAX_USERS=100  # Maximum users per tenant (varies by plan)
TENANT_MAX_STORAGE_GB=10  # Maximum storage per tenant
TENANT_MAX_MESSAGES_PER_DAY=1000  # Rate limit per tenant
```

### Settings in Code

```python
from config.settings import tenant_config

# Check multi-tenancy status
if tenant_config.enabled:
    strategy = tenant_config.isolation_strategy
    id_source = tenant_config.id_source
```

## Architecture

### Isolation Strategies

#### 1. Shared Database with Tenant Discriminator (Simple)
- Single database, tenant_id column in all tables
- Easiest to implement and maintain
- Best for: Small to medium scale, similar tenants

#### 2. Schema per Tenant (Recommended)
- Separate schema for each tenant in same database
- Good isolation, moderate complexity
- Best for: Medium to large scale, regulatory compliance

#### 3. Database per Tenant (Maximum Isolation)
- Completely separate database for each tenant
- Highest isolation, highest cost
- Best for: Enterprise customers, strict data sovereignty

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Tenant Context Middleware      │  │
│  └──────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐
│Tenant A│  │Tenant B│  │Tenant C│
│Schema  │  │Schema  │  │Schema  │
└────────┘  └────────┘  └────────┘
    │             │             │
    └─────────────┴─────────────┘
              │
         ┌────▼─────┐
         │PostgreSQL│
         └──────────┘
```

## Implementation

### 1. Tenant Model

**File:** `database/models.py` (add to existing file)

```python
"""Tenant models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from datetime import datetime
from database.session import Base


class Tenant(Base):
    """Tenant/Organization model."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, index=True)
    
    # Plan and limits
    plan = Column(String(50), default="free")  # free, pro, enterprise
    max_users = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=5)
    max_messages_per_day = Column(Integer, default=1000)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration
    settings = Column(JSON, default={})
    
    # Database connection (for database-per-tenant strategy)
    database_url = Column(String(500), nullable=True)


class TenantUser(Base):
    """User membership in tenant."""
    __tablename__ = "tenant_users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    role = Column(String(50), default="member")  # owner, admin, member
    joined_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Tenant Context Middleware

**File:** `middleware/tenant_middleware.py`

```python
"""Multi-tenancy middleware for tenant context."""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from database.session import SessionLocal
from database.models import Tenant

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context."""
    
    async def dispatch(self, request: Request, call_next):
        """Extract tenant context from request."""
        tenant_id = self._extract_tenant_id(request)
        
        if tenant_id:
            # Validate and load tenant
            tenant = self._load_tenant(tenant_id)
            if not tenant:
                return HTTPException(status_code=404, detail="Tenant not found")
            
            if not tenant.is_active or tenant.is_suspended:
                return HTTPException(status_code=403, detail="Tenant suspended")
            
            # Set tenant context
            request.state.tenant_id = tenant_id
            request.state.tenant = tenant
        else:
            request.state.tenant_id = None
            request.state.tenant = None
        
        response = await call_next(request)
        return response
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request."""
        # Strategy 1: Subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "admin"]:
                return self._get_tenant_by_subdomain(subdomain)
        
        # Strategy 2: Custom header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # Strategy 3: Path parameter
        path = request.url.path
        if path.startswith("/tenant/"):
            parts = path.split("/")
            if len(parts) > 2:
                return parts[2]
        
        return None
    
    def _get_tenant_by_subdomain(self, subdomain: str) -> Optional[str]:
        """Get tenant ID by subdomain."""
        db = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
            return tenant.tenant_id if tenant else None
        finally:
            db.close()
    
    def _load_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Load tenant from database."""
        db = SessionLocal()
        try:
            return db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        finally:
            db.close()
```

### 3. Schema-per-Tenant Implementation

**File:** `database/tenant_schema.py`

```python
"""Schema-per-tenant database management."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional
import logging

from database.session import Base, engine as default_engine
from database.models import Tenant

logger = logging.getLogger(__name__)


class TenantSchemaManager:
    """Manage schemas for multi-tenant database."""
    
    def __init__(self, base_engine=None):
        self.base_engine = base_engine or default_engine
    
    def create_tenant_schema(self, tenant_id: str) -> bool:
        """Create schema for new tenant."""
        try:
            schema_name = f"tenant_{tenant_id}"
            
            # Create schema
            with self.base_engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
            
            # Create tables in schema
            tenant_engine = self._get_tenant_engine(tenant_id)
            Base.metadata.create_all(bind=tenant_engine)
            
            logger.info(f"Created schema for tenant: {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating tenant schema: {e}")
            return False
    
    def delete_tenant_schema(self, tenant_id: str) -> bool:
        """Delete tenant schema (use with caution!)."""
        try:
            schema_name = f"tenant_{tenant_id}"
            
            with self.base_engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()
            
            logger.info(f"Deleted schema for tenant: {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting tenant schema: {e}")
            return False
    
    def _get_tenant_engine(self, tenant_id: str):
        """Get database engine for tenant schema."""
        schema_name = f"tenant_{tenant_id}"
        
        # Create engine with schema search path
        connection_string = str(self.base_engine.url)
        tenant_engine = create_engine(
            connection_string,
            connect_args={"options": f"-csearch_path={schema_name}"},
            pool_size=5,
            max_overflow=10
        )
        return tenant_engine
    
    def get_tenant_session(self, tenant_id: str) -> Session:
        """Get database session for tenant."""
        tenant_engine = self._get_tenant_engine(tenant_id)
        SessionClass = sessionmaker(bind=tenant_engine)
        return SessionClass()


# Global instance
tenant_schema_manager = TenantSchemaManager()


def get_tenant_db(tenant_id: str) -> Session:
    """Get database session for specific tenant."""
    return tenant_schema_manager.get_tenant_session(tenant_id)
```

### 4. Shared Table with Discriminator

**File:** `database/models.py` (alternative approach)

```python
"""Models with tenant discriminator column."""
from sqlalchemy import Column, String, ForeignKey, Index

# Add tenant_id to all tenant-specific tables
class Message(Base):
    """Message model with tenant isolation."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), index=True, nullable=False)  # Tenant discriminator
    content = Column(Text, nullable=False)
    username = Column(String(100), index=True)
    # ... other fields
    
    __table_args__ = (
        Index('idx_tenant_message', 'tenant_id', 'id'),
    )

# Repository with automatic tenant filtering
class MessageRepository:
    """Message repository with tenant isolation."""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def get_all(self, limit: int = 100):
        """Get all messages for tenant."""
        return self.db.query(Message).filter(
            Message.tenant_id == self.tenant_id
        ).limit(limit).all()
    
    def create(self, **kwargs):
        """Create message for tenant."""
        kwargs['tenant_id'] = self.tenant_id
        message = Message(**kwargs)
        self.db.add(message)
        self.db.commit()
        return message
```

### 5. Tenant-Aware Dependencies

**File:** `core/dependencies.py` (add to existing file)

```python
"""Tenant-aware dependency injection."""
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database.tenant_schema import get_tenant_db


def get_current_tenant(request: Request) -> dict:
    """Get current tenant from request context."""
    if not hasattr(request.state, 'tenant') or not request.state.tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    return {
        "id": request.state.tenant.tenant_id,
        "name": request.state.tenant.name,
        "plan": request.state.tenant.plan
    }


def get_tenant_db_session(request: Request) -> Session:
    """Get database session for current tenant."""
    tenant = get_current_tenant(request)
    session = get_tenant_db(tenant["id"])
    try:
        yield session
    finally:
        session.close()
```

### 6. Tenant Management Routes

**File:** `routes/tenants.py`

```python
"""Tenant management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.dependencies import get_db_write, get_current_user
from database.models import Tenant, TenantUser
from database.tenant_schema import tenant_schema_manager
import uuid

router = APIRouter(prefix="/admin/tenants", tags=["Tenants"])


class TenantCreate(BaseModel):
    name: str
    subdomain: str
    plan: str = "free"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    max_users: Optional[int] = None
    is_active: Optional[bool] = None


@router.post("/")
async def create_tenant(
    data: TenantCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_write)
):
    """Create a new tenant."""
    # Check if subdomain is available
    existing = db.query(Tenant).filter(Tenant.subdomain == data.subdomain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")
    
    # Create tenant
    tenant_id = str(uuid.uuid4())[:8]
    tenant = Tenant(
        tenant_id=tenant_id,
        name=data.name,
        subdomain=data.subdomain,
        plan=data.plan
    )
    db.add(tenant)
    db.commit()
    
    # Create schema
    if tenant_config.isolation_strategy == "schema":
        tenant_schema_manager.create_tenant_schema(tenant_id)
    
    # Add creator as owner
    tenant_user = TenantUser(
        tenant_id=tenant_id,
        user_id=current_user["id"],
        role="owner"
    )
    db.add(tenant_user)
    db.commit()
    
    return {
        "tenant_id": tenant_id,
        "name": tenant.name,
        "subdomain": tenant.subdomain,
        "url": f"https://{tenant.subdomain}.example.com"
    }


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_write)
):
    """Get tenant details."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "subdomain": tenant.subdomain,
        "plan": tenant.plan,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at
    }


@router.patch("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_write)
):
    """Update tenant settings."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update fields
    if data.name:
        tenant.name = data.name
    if data.plan:
        tenant.plan = data.plan
    if data.max_users is not None:
        tenant.max_users = data.max_users
    if data.is_active is not None:
        tenant.is_active = data.is_active
    
    db.commit()
    return {"success": True, "tenant_id": tenant_id}


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_write)
):
    """Delete tenant (dangerous!)."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Delete schema
    if tenant_config.isolation_strategy == "schema":
        tenant_schema_manager.delete_tenant_schema(tenant_id)
    
    # Delete tenant record
    db.delete(tenant)
    db.commit()
    
    return {"success": True, "message": "Tenant deleted"}
```

### 7. Usage in Application Routes

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from core.dependencies import get_current_tenant, get_tenant_db_session

router = APIRouter()

@router.get("/messages")
async def get_messages(
    request: Request,
    tenant: dict = Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db_session)
):
    """Get messages for current tenant."""
    # DB session is automatically scoped to tenant schema
    messages = db.query(Message).all()
    return {
        "tenant": tenant["name"],
        "messages": messages
    }
```

## Tenant Provisioning

### Automatic Tenant Onboarding

```python
@router.post("/signup")
async def tenant_signup(data: TenantCreate):
    """Self-service tenant signup."""
    # Validate subdomain
    if not re.match(r'^[a-z0-9-]+$', data.subdomain):
        raise HTTPException(status_code=400, detail="Invalid subdomain")
    
    # Create tenant
    tenant = await create_tenant(data)
    
    # Send welcome email
    # Set up default data
    # Notify admin
    
    return {
        "message": "Tenant created successfully",
        "login_url": f"https://{data.subdomain}.example.com/login"
    }
```

## Resource Limits and Quotas

### Enforce Tenant Limits

```python
class TenantLimitMiddleware(BaseHTTPMiddleware):
    """Enforce tenant resource limits."""
    
    async def dispatch(self, request: Request, call_next):
        tenant = getattr(request.state, 'tenant', None)
        if tenant:
            # Check daily message limit
            if self._check_message_limit_exceeded(tenant):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Daily message limit exceeded"}
                )
        
        response = await call_next(request)
        return response
    
    def _check_message_limit_exceeded(self, tenant: Tenant) -> bool:
        """Check if tenant exceeded daily message limit."""
        # Query message count for today
        # Compare with tenant.max_messages_per_day
        return False  # Simplified
```

## Monitoring

### Tenant Metrics

```python
from prometheus_client import Counter, Gauge

tenant_requests = Counter('tenant_requests_total', 'Requests per tenant', ['tenant_id'])
tenant_storage = Gauge('tenant_storage_bytes', 'Storage per tenant', ['tenant_id'])
tenant_users = Gauge('tenant_users_count', 'Users per tenant', ['tenant_id'])
```

## Best Practices

1. **Data Isolation**: Never leak data across tenants
2. **Performance**: Index tenant_id columns, use connection pooling
3. **Security**: Validate tenant context in all operations
4. **Scalability**: Consider sharding for very large deployments
5. **Backup**: Per-tenant backup strategies
6. **Testing**: Test multi-tenant scenarios thoroughly
7. **Monitoring**: Track per-tenant metrics and costs
8. **Compliance**: Support data residency requirements

## Migration Strategy

### From Single Tenant to Multi-Tenant

1. **Add tenant_id columns** to all tables
2. **Create tenant records** for existing data
3. **Update queries** to filter by tenant_id
4. **Test isolation** thoroughly
5. **Deploy with feature flag**
6. **Monitor for data leaks**

## References

- [Multi-Tenancy Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/)
- [SaaS Architecture](https://martinfowler.com/articles/patterns-of-distributed-systems/)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [ADR-017: Multi-Tenancy Strategy](adr/ADR-017-multi-tenancy-strategy.md)
