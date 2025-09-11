# Telemedicine Application Constitution

## Core Principles

### I. Library-First Architecture

Every feature starts as a standalone library within the modular monolith architecture. Libraries must be self-contained, independently testable, and documented. Clear purpose required - no organizational-only libraries. Each service module (auth_service, medical_records, appointments, messaging, notifications) functions as an independent library with well-defined interfaces.

### II. CLI Interface

Every library exposes functionality via CLI commands for development and operational tasks. Text in/out protocol: stdin/args → stdout, errors → stderr. Support both JSON and human-readable formats. Each module includes management commands with --help/--version/--format options for database operations, data migrations, and administrative tasks.

### III. Test-First Development (NON-NEGOTIABLE)

TDD mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced. Order: Contract→Integration→E2E→Unit tests strictly followed. Real dependencies used (actual PostgreSQL for integration tests). FORBIDDEN: Implementation before test, skipping RED phase.

### IV. Medical Data Integrity

All medical data operations must maintain immutable audit trails. Versioned medical records create new versions on updates while preserving complete history. Patient-entered data cannot be modified by doctors - only consultation notes can be added. Data retention respects user preferences while maintaining minimum 8-week requirement for medical continuity.

### V. Security & Privacy First

HIPAA-compliant data handling patterns mandatory. JWT authentication with role-based access control (patients access own data, doctors access assigned patients only). All medical data access logged with user attribution. Encrypted data transmission and storage. Input validation on all medical data with Pydantic/Zod schemas.

### VI. Observability & Audit

Structured JSON logging with correlation IDs for request tracing. All medical record changes logged with user attribution and timestamps. Frontend errors sent to backend logging service. Performance metrics collection for API response times and database queries. Comprehensive error context with request IDs and user context.

### VII. Versioning & Breaking Changes

MAJOR.MINOR.BUILD format with automated BUILD increments on every change. API versioning strategy for future compatibility. Database migrations with validation and rollback procedures. Breaking changes require parallel support and migration plan. All changes maintain backward compatibility within major versions.

## Medical Domain Requirements

### Data Model Standards

SQLAlchemy models with comprehensive type hints and relationships. Pydantic schemas for API serialization with medical-specific validation. Versioned entities maintain chronological access patterns. Foreign key constraints enforce referential integrity for patient-doctor relationships.

### Authentication Patterns

Dual authentication flows: patients use email + username, doctors use email + pre-assigned doctor ID. JWT tokens with 15-minute access tokens and 7-day refresh tokens. Session invalidation on role changes. Password hashing with bcrypt minimum 12 rounds.

### API Design Consistency

RESTful endpoints following OpenAPI 3.0 specifications. Standard HTTP status codes with consistent error response format. Pagination for large datasets with offset/limit patterns. WebSocket endpoints for real-time messaging between patients and doctors.

## Technology Standards

### Backend Requirements

Python 3.11+ with comprehensive type hints. FastAPI with async/await patterns for all I/O operations. SQLAlchemy 2.0+ with async sessions and relationship loading. Alembic for database migrations with validation scripts.

### Frontend Requirements

TypeScript with strict mode enabled. Next.js 14+ with App Router for modern React patterns. shadcn/ui components with Tailwind CSS for consistent styling. React Hook Form with Zod validation for medical questionnaires.

### Infrastructure Standards

Docker containers for all services with multi-stage builds. PostgreSQL with proper indexing for medical record queries. Environment-based configuration with .env files. Health checks and graceful shutdown patterns.

## Development Workflow

### Code Quality Gates

All code must pass type checking (pyright for Python, TypeScript strict mode). Integration tests must use real database connections. Code coverage minimum 80% for medical data operations. Linting and formatting enforced (ruff, prettier, eslint).

### Review Process

All PRs must include tests that initially fail (RED phase demonstration). Medical data changes require additional security review. API contract changes require OpenAPI specification updates. Performance impact assessment for database schema changes.

### Deployment Standards

Blue-green deployment with health checks. Database migrations validated in staging environment. Rollback procedures tested and documented. Container security scanning before production deployment.

## Governance

Constitution supersedes all other development practices. Amendments require documentation, approval from project maintainers, and migration plan. All PRs and code reviews must verify constitutional compliance. Complexity deviations must be justified with simpler alternative rejection rationale.

Use `.github/copilot-instructions.md` for runtime development guidance and domain-specific patterns. Regular constitutional review scheduled quarterly to ensure principles remain aligned with project evolution.

**Version**: 1.0.0 | **Ratified**: September 10, 2025 | **Last Amended**: September 10, 2025
