# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the Universal Chat System.

## What are ADRs?

Architecture Decision Records document important architectural decisions made in the project, including the context, the decision itself, and the consequences. They help new team members understand why certain technical choices were made.

## Format

Each ADR follows this structure:

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue we're facing? What factors are driving this decision?

## Decision
What did we decide to do?

## Consequences
What are the positive and negative outcomes of this decision?

## Alternatives Considered
What other options did we evaluate?
```

## Index

- [ADR-001: Choice of FastAPI as Web Framework](ADR-001-fastapi-framework.md)
- [ADR-002: SQLAlchemy ORM for Database Abstraction](ADR-002-sqlalchemy-orm.md)
- [ADR-003: JWT for Authentication](ADR-003-jwt-authentication.md)
- [ADR-004: WebSocket for Real-Time Communication](ADR-004-websocket-realtime.md)

## Creating a New ADR

1. Copy the template from `ADR-000-template.md`
2. Number it sequentially (check existing ADRs)
3. Give it a descriptive filename
4. Fill in all sections
5. Update this index
6. Submit for review
