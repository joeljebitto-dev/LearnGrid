# DBD-007 Course Structure And Versioning

Related task: [T-007](../tasks/T-007-course-structure-versioning.md)  
Related spec: [SPEC-007](../specs/007-course-structure-versioning.md)  
Canonical schema: [course_db](../DATABASE_SCHEMA.md#course_db)  
Aggregate structure: [DB_STRUCTURE.md](../DB_STRUCTURE.md#course_db)

## DBD-007-001 Scope
`course-service` owns ordered course structure and lightweight revision snapshots in
`course_db`. This design extends [DBD-006](DBD-006-course-catalog-metadata.md) with
modules, lessons, topics, and course revision records.

## DBD-007-002 Implemented Tables
| Table ID | Table | Purpose | Implemented in T-007 |
| --- | --- | --- | --- |
| `DB-COURSE-007` | `course_modules` | Ordered modules inside a course | Yes |
| `DB-COURSE-008` | `lessons` | Ordered lessons inside modules | Yes |
| `DB-COURSE-009` | `topics` | Ordered lesson topics | Yes |
| `DB-COURSE-011` | `course_revisions` | Course structure snapshot history | Yes |

## DBD-007-003 Ordering
Modules, lessons, and topics use deterministic integer `position` values. Reorder
operations are transactional and renumber active records to `1..n`. Soft-archived
modules and lessons are moved out of the active ordering range before `deleted_at`
is set so the documented unique constraints remain valid.

## DBD-007-004 Lifecycle
- `course_modules.status`: `draft`, `published`, `archived`.
- `lessons.status`: `draft`, `published`, `archived`.
- `lessons.published_at` is set on first publish.
- `topics` do not have a lifecycle status in the canonical schema.
- Draft lessons are excluded from published structure reads.

## DBD-007-005 Relationships
- `course_modules.course_id` references `courses.id`.
- `lessons.course_id` references `courses.id`.
- `lessons.module_id` references `course_modules.id`.
- `topics.lesson_id` references `lessons.id`.
- `course_revisions.course_id` references `courses.id`.
- `lessons.content_asset_id` and `topics.content_asset_id` are cross-service UUID references to content assets without database-level foreign keys.
- `course_revisions.created_by_profile_id` is a cross-service UUID reference.

## DBD-007-006 Indexes And Constraints
- `course_modules`: unique `uq_course_modules_course_position`; index `idx_modules_course_status`.
- `lessons`: unique `uq_lessons_module_position`; indexes `idx_lessons_course_status` and `idx_lessons_module_id`.
- `topics`: unique `uq_topics_lesson_position`; index `idx_topics_lesson_id`.
- `course_revisions`: unique `uq_course_revisions_course_version`; index `idx_course_revisions_course`.

## DBD-007-007 Cache And Events
Course structure writes invalidate course catalog cache keys so published structure reads do
not serve stale data. Publishing a lesson emits a structured local `LessonPublished` event
using the shared Kafka-capable event envelope documented in
[EVT-020](../event-design/EVT-020-kafka-eventing.md).
