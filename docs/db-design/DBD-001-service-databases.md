# DBD-001 Service Databases

Related task: [T-001 Project Setup](../tasks/T-001-project-setup.md)  
Related spec: [SPEC-001 Authentication Lifecycle](../specs/001-authentication-lifecycle.md)  
Canonical schema: [Database Ownership](../DATABASE_SCHEMA.md#database-ownership)

## Design Summary
T-001 established the service database ownership model and local database bootstrap for the LearnGrid LMS monorepo. Each backend service owns its own PostgreSQL database and does not write directly to another service database.

## Implemented Database Ownership
| Database | Owning service | Local role |
| --- | --- | --- |
| `auth_db` | `auth-service` | Authentication, tokens, RBAC, authorization |
| `user_db` | `user-service` | Profiles, institutions, departments, batches |
| `course_db` | `course-service` | Course catalog and structure |
| `content_db` | `content-service` | Content assets and access records |
| `enrollment_db` | `enrollment-service` | Enrollments and access grants |
| `progress_db` | `progress-service` | Lesson, video, assessment, and course progress |
| `assessment_db` | `assessment-service` | Question banks, quizzes, assignments, submissions |
| `grading_db` | `grading-service` | Grade records, reviews, results, certificates |
| `notification_db` | `notification-service` | Notifications, templates, preferences, delivery attempts |
| `analytics_db` | `analytics-service` | Event facts, aggregates, reports, usage metrics |

## Local Infrastructure
- `docker-compose.yml` starts PostgreSQL on `5432` and Redis on `6379`.
- PostgreSQL init SQL creates all service databases from `auth_db` through `analytics_db`.
- `scripts/run-dev.sh` also ensures these databases exist when an existing Docker volume skipped initialization.
- Backend service `.env.example` files define each service `DATABASE_URL`.

## Relationships And Boundaries
- In-service relationships use normal Django/PostgreSQL foreign keys.
- Cross-service relationships use UUID reference fields and are not database-level foreign keys.
- Redis is shared local infrastructure for token blacklist and authorization cache behavior introduced by later tasks.

## Verification
T-001 verification covered local service health checks, backend checks/tests, frontend checks/tests/build, and documented Docker API socket limitations in [T-001](../tasks/T-001-project-setup.md).
