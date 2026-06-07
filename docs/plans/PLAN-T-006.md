# T-006 Course Catalog And Metadata Plan

## Summary
Implement `T-006` in `course-service` as the first real course-domain workflow. Add course catalog models, metadata management, catalog/search APIs, lifecycle workflows, Redis catalog caching, and structured course event emission. Real Kafka transport remains deferred to `T-020`; T-006 will add a local publisher abstraction that emits structured events and is testable.

## Key Changes
- Add `course-service` models and migration for the T-006 subset of `course_db`:
  - `Course` from `DB-COURSE-001`.
  - `CourseCategory` from `DB-COURSE-002`.
  - `CourseTag` from `DB-COURSE-003`.
  - `CourseCategoryLink` from `DB-COURSE-004`.
  - `CourseTagLink` from `DB-COURSE-005`.
  - `CoursePrerequisite` from `DB-COURSE-006`.
  - `LearningOutcome` from `DB-COURSE-010`.
- Do not implement modules, lessons, topics, or course revisions in T-006; those stay for T-007.
- Use explicit UUID primary keys, documented indexes/unique constraints, lifecycle enums, and soft-delete fields matching `DATABASE_SCHEMA.md`.
- Add serializers, selectors, and services for:
  - Course create/update/list/detail.
  - Category and tag CRUD/search.
  - Metadata assignment through course payloads: `category_ids`, `tag_ids`, `prerequisite_course_ids`, and ordered `learning_outcomes`.
  - Lifecycle actions: publish, archive, and soft-delete.
- Add Redis course catalog cache:
  - Cache published catalog list/detail reads with `COURSE_CATALOG_CACHE_TTL_SECONDS`, default `300`.
  - Bypass cache for management/non-published reads.
  - Invalidate course catalog cache after course, category, tag, prerequisite, or learning outcome writes.
  - Fall back to database reads when Redis is unavailable.
- Add structured event publisher abstraction in `course-service`:
  - Emit `CourseCreated`, `CoursePublished`, and `CourseArchived`.
  - Event payload includes `event_id`, `event_type`, `aggregate_id`, `producer_service`, `timestamp`, `version`, `correlation_id`, and `payload`.
  - Implementation logs/emits locally for now; Kafka transport is future `T-020`.

## API Interfaces
- Mount course routes under `/api/courses/`.
- Course APIs:
  - `GET /api/courses/`
  - `POST /api/courses/`
  - `GET /api/courses/<uuid>/`
  - `PATCH /api/courses/<uuid>/`
  - `POST /api/courses/<uuid>/publish/`
  - `POST /api/courses/<uuid>/archive/`
  - `DELETE /api/courses/<uuid>/`
- Category APIs:
  - `GET /api/courses/categories/`
  - `POST /api/courses/categories/`
  - `GET /api/courses/categories/<uuid>/`
  - `PATCH /api/courses/categories/<uuid>/`
  - `DELETE /api/courses/categories/<uuid>/`
- Tag APIs:
  - `GET /api/courses/tags/`
  - `POST /api/courses/tags/`
  - `GET /api/courses/tags/<uuid>/`
  - `PATCH /api/courses/tags/<uuid>/`
  - `DELETE /api/courses/tags/<uuid>/`
- Course create/update request accepts:
  - `institution_id`, `owner_profile_id`, `title`, optional `slug`, `description`, `difficulty_level`, `thumbnail_asset_id`.
  - Optional metadata arrays: `category_ids`, `tag_ids`, `prerequisite_course_ids`, `learning_outcomes`.
  - `slug` is generated from `title` when omitted and normalized to lowercase URL slug.
- List filters:
  - Courses: `institution_id`, `owner_profile_id`, `status`, `difficulty_level`, `category_id`, `tag_id`, `q`, `sort`, `page`, `page_size`.
  - Categories/tags: `institution_id`, `q`, `sort`, `page`, `page_size`.
- Authorization:
  - Create/update/publish/archive/delete require `course.manage` at course/request `institution_id`.
  - Category/tag writes require `course.manage`; institution-scoped records use institution scope, global records use platform scope.
  - Published course list/detail requires `course.view`.
  - Draft, archived, and deleted course reads require `course.manage`.
  - Student discovery hides archived/deleted courses and only returns published courses.

## Documentation Updates
- Update `docs/DEVELOPMENT.md` with T-006 endpoints, filters, payload fields, authorization rules, cache behavior, and event behavior.
- Add implemented design docs:
  - `docs/db-design/DBD-006-course-catalog-metadata.md`
  - `docs/api-design/API-006-course-catalog-metadata.md`
- Update `docs/db-design/README.md`, `docs/api-design/README.md`, `docs/DB_STRUCTURE.md`, and `docs/API_STRUCTURE.md`.
- Update `docs/LIVING_DOCUMENT.md` and `docs/CHANGELOG.md`.
- Mark `T-006.01` through `T-006.08` complete only after verification passes.

## Test Plan
- Course-service API tests:
  - Permitted instructor/admin can create a draft course.
  - Unauthorized user cannot create/update/publish/archive/delete.
  - Published courses appear in `course.view` catalog results.
  - Draft, archived, and deleted courses are hidden from normal discovery.
  - Manage users can read/manage draft and archived courses.
  - Course update can replace categories, tags, prerequisites, and learning outcomes.
  - Category and tag CRUD/search works and normalizes slugs.
  - Prerequisite validation rejects self-prerequisites and cross-institution prerequisites.
  - Redis cache is used for published catalog reads and invalidated after writes.
  - Redis failure falls back to database reads.
  - `CourseCreated`, `CoursePublished`, and `CourseArchived` publisher calls occur.
  - Catalog selectors use `select_related`/`prefetch_related`; add a focused query-count test for list results with metadata.
- Verification commands for `course-service`:
  - `poetry run ruff check .`
  - `poetry run python manage.py check`
  - `poetry run python manage.py makemigrations --check --dry-run`
  - `poetry run pytest`

## Assumptions
- No auth-service changes are required because `course.view` and `course.manage` already exist in the RBAC catalog.
- T-006 implements course catalog metadata only; course structure/versioning remains T-007.
- Real Kafka publishing remains T-020; T-006 adds a stable publisher abstraction and structured event payloads.
- Object storage validation for `thumbnail_asset_id` remains future content-service scope; T-006 stores it as a cross-service UUID reference.
- Existing `pnpm dev` stack should be restarted after implementation so `course-service` loads the new routes and migrations.
