# LearnGrid LMS Agent Guide

Source: [SRD.pdf](SRD.pdf)

## Purpose
This file defines how implementation agents should use the LearnGrid LMS documentation set.
The documentation is the project source of truth until application code, migrations, and tests
exist.

## Required Reading Order
1. [SPECIFICATION.md](SPECIFICATION.md) for the master feature index.
2. [ARCHITECTURE.md](ARCHITECTURE.md) for system boundaries and service ownership.
3. [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) before creating models or migrations.
4. [TASKS.md](TASKS.md) for implementation checklists.
5. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) before choosing any unresolved technology option.

## Documentation Rules
- Every feature requirement must keep its stable requirement ID.
- Every task must remain a Markdown checklist item until implemented.
- Cross-service references must use UUID values and service APIs/events, not database joins.
- Open decisions must remain unresolved until an explicit architectural decision is made.
- Future-release items from the SRD are in scope for documentation and backlog tracking.

## Implementation Rules
- Backend services use Django and Django REST Framework.
- Frontend uses React, TypeScript, Tailwind CSS, React Router, TanStack Query, Axios, React Hook Form, and Zod.
- PostgreSQL is the transactional database system.
- Redis is used for cache, rate limiting, token blacklist, OTPs, WebSocket channel layer, and locks.
- Kafka is used for asynchronous workflows and analytics events.
- Selenium covers browser-based end-to-end journeys.

## Completion Rules
- A task can be marked complete only after implementation and relevant verification are complete.
- Schema-related tasks require migrations and tests before completion.
- Security-sensitive tasks require authorization and negative-path tests.
- Deployment tasks require staging verification before production completion.
