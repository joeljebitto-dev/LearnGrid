# SPEC-019 API Gateway

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-019](../tasks/T-019-api-gateway.md)  
Resolved decision: [OD-001 API Gateway Selection](../KNOWN_ISSUES.md#od-001-api-gateway-selection)

## Functional Requirements
- SPEC-019-FR-001 The system shall use an API Gateway such as Kong, Nginx, Traefik, or equivalent.
- SPEC-019-FR-002 The gateway shall terminate TLS.
- SPEC-019-FR-003 The gateway shall route requests to microservices.
- SPEC-019-FR-004 The gateway shall support rate limiting.
- SPEC-019-FR-005 The gateway shall support request logging.
- SPEC-019-FR-006 The gateway shall enforce CORS control.
- SPEC-019-FR-007 The gateway shall support authentication middleware where applicable.
- SPEC-019-FR-008 The gateway shall support API versioning.
- SPEC-019-FR-009 The gateway shall enforce request size limits.

## Routes
- SPEC-019-FR-010 `/api/auth/*` routes to auth-service.
- SPEC-019-FR-011 `/api/users/*` routes to user-service.
- SPEC-019-FR-012 `/api/courses/*` routes to course-service.
- SPEC-019-FR-013 `/api/content/*` routes to content-service.
- SPEC-019-FR-014 `/api/enrollments/*` routes to enrollment-service.
- SPEC-019-FR-015 `/api/progress/*` routes to progress-service.
- SPEC-019-FR-016 `/api/assessments/*` routes to assessment-service.
- SPEC-019-FR-017 `/api/grades/*` routes to grading-service.
- SPEC-019-FR-018 `/api/notifications/*` routes to notification-service.
- SPEC-019-FR-019 `/api/analytics/*` routes to analytics-service.

## Acceptance Criteria
- SPEC-019-AC-001 All documented routes reach their intended service.
- SPEC-019-AC-002 Oversized requests are rejected at the gateway.
- SPEC-019-AC-003 CORS restrictions are enforced consistently.
- SPEC-019-AC-004 Gateway request logs are available to observability tooling.
