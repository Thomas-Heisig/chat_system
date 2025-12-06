# ADR-007: Multi-Database Support Strategy

## Status
Accepted

## Date
2025-12-06

## Context
The Universal Chat System needs to support different deployment scenarios with varying requirements:
- **Development**: Quick setup, minimal dependencies, easy debugging
- **Small Deployments**: Low resource usage, simple maintenance
- **Enterprise**: High performance, scalability, ACID guarantees
- **Document-Oriented Workloads**: Flexible schema, JSON-native operations

Different users have different preferences and existing infrastructure. Supporting multiple databases improves adoption by allowing users to choose technology that fits their environment.

## Decision
We decided to support **three database types** through a unified repository pattern:
1. **SQLite** - Default for development and small deployments
2. **PostgreSQL** - For production and high-performance deployments
3. **MongoDB** - For document-oriented workloads and flexible schema

Implementation approach:
- **Repository Pattern**: Abstract data access behind repository interfaces
- **SQLAlchemy ORM**: For relational databases (SQLite, PostgreSQL)
- **Motor/PyMongo**: For MongoDB
- **Database Adapters**: `database/adapters/` for database-specific implementations
- **Unified Models**: `database/models/` with database-agnostic logic where possible
- **Configuration**: Environment variable `DATABASE_TYPE` controls the active database

## Consequences

### Positive
- **Flexibility**: Users choose the database that fits their needs
- **Low Barrier to Entry**: SQLite works out-of-the-box with zero setup
- **Production Ready**: PostgreSQL provides enterprise-grade features
- **Schema Flexibility**: MongoDB supports document-based use cases
- **Migration Path**: Easy to start with SQLite and migrate to PostgreSQL
- **No Vendor Lock-In**: Can switch databases without rewriting application code

### Negative
- **Increased Complexity**: Multiple database implementations to maintain
- **Testing Overhead**: Must test all database types
- **Feature Parity Challenges**: Some features may not work identically across databases
- **Performance Tuning**: Need database-specific optimizations
- **Migration Tools**: Complex to migrate data between different database types

### Neutral
- **Connection Configuration**: Different connection strings and setup per database
- **Schema Management**: Alembic migrations for SQL, version control for MongoDB
- **Query Optimization**: Different indexing and query strategies per database

## Alternatives Considered

### Alternative 1: PostgreSQL Only
- **Description**: Support only PostgreSQL for all deployments
- **Pros**: 
  - Simpler implementation
  - Consistent behavior
  - Best performance
  - Full feature set
- **Cons**: 
  - Requires PostgreSQL setup for development
  - Overkill for small deployments
  - More complex for beginners
- **Why Rejected**: Too high barrier to entry for development and small deployments

### Alternative 2: SQLite Only
- **Description**: Use SQLite for all scenarios
- **Pros**: 
  - Zero setup
  - Very simple
  - Single file database
  - No external dependencies
- **Cons**: 
  - Limited concurrency
  - No client-server architecture
  - Poor performance at scale
  - Limited for production
- **Why Rejected**: Insufficient for production deployments

### Alternative 3: PostgreSQL + SQLite (No MongoDB)
- **Description**: Support only relational databases
- **Pros**: 
  - Simpler than three databases
  - SQLAlchemy handles both
  - Consistent data model
- **Cons**: 
  - No document-oriented option
  - Less flexible schema
- **Why Rejected**: Some users prefer/need document databases

### Alternative 4: Database-Agnostic ORM Only
- **Description**: Use only SQLAlchemy and let it handle all database differences
- **Pros**: 
  - Simplest implementation
  - Automatic query translation
  - Wide database support
- **Cons**: 
  - Limits to SQL databases only
  - Can't leverage database-specific features
  - Lowest common denominator approach
  - MongoDB not supported
- **Why Rejected**: Too limiting and doesn't support MongoDB

### Alternative 5: Microservices with Different Databases
- **Description**: Split system into microservices, each with its own database choice
- **Pros**: 
  - Each service optimized for its workload
  - True polyglot persistence
- **Cons**: 
  - Much more complex architecture
  - Distributed transactions issues
  - Higher operational overhead
  - Overkill for the current scale
- **Why Rejected**: Too complex for current requirements

## References
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- Database models: `database/models/`
- Database repositories: `database/repositories/`
- Database adapters: `database/adapters/`
- Configuration: `.env.example` and `config/settings.py`
- Setup guide: `SETUP.md`
