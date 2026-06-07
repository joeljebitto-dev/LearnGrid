# DBD-006 Course Catalog And Metadata

Related task: [T-006](../tasks/T-006-course-catalog-metadata.md)  
Related spec: [SPEC-006](../specs/006-course-catalog-metadata.md)  
Canonical schema: [course_db](../DATABASE_SCHEMA.md#course_db)  
Aggregate structure: [DB_STRUCTURE.md](../DB_STRUCTURE.md#course_db)

## DBD-006-001 Scope
`course-service` owns the T-006 course catalog metadata subset in `course_db`.
This implemented design covers catalog records, categories, tags, category/tag links,
prerequisites, and ordered learning outcomes. Course modules, lessons, topics, and
course revisions are covered by [DBD-007](DBD-007-course-structure-versioning.md).

## DBD-006-002 Implemented Tables
| Table ID | Table | Purpose | Implemented in T-006 |
| --- | --- | --- | --- |
| `DB-COURSE-001` | `courses` | Course catalog and lifecycle record | Yes |
| `DB-COURSE-002` | `course_categories` | Global or institution-scoped taxonomy | Yes |
| `DB-COURSE-003` | `course_tags` | Global or institution-scoped discovery tags | Yes |
| `DB-COURSE-004` | `course_category_links` | Course-to-category many-to-many links | Yes |
| `DB-COURSE-005` | `course_tag_links` | Course-to-tag many-to-many links | Yes |
| `DB-COURSE-006` | `course_prerequisites` | Course prerequisite relationships | Yes |
| `DB-COURSE-010` | `learning_outcomes` | Ordered course learning outcomes | Yes |

## DBD-006-003 Course Lifecycle
`courses.status` uses `draft`, `published`, `archived`, and `deleted`.
`deleted` is a soft-delete state and also sets `deleted_at`. Published courses set
`published_at` on first publish. Course slugs are normalized with URL-safe lowercase
slug rules and are unique per institution.

## DBD-006-004 Relationships
- `course_category_links.course_id` and `course_tag_links.course_id` reference `courses.id`.
- `course_category_links.category_id` references `course_categories.id`.
- `course_tag_links.tag_id` references `course_tags.id`.
- `course_prerequisites.course_id` and `course_prerequisites.prerequisite_course_id` reference `courses.id`.
- `learning_outcomes.course_id` references `courses.id`.
- `course_categories.parent_category_id` is a nullable self-reference.
- `institution_id`, `owner_profile_id`, and `thumbnail_asset_id` are cross-service UUID references without database-level foreign keys.

## DBD-006-005 Indexes And Constraints
- `courses`: unique `uq_courses_institution_slug`; indexes on institution/status and owner profile.
- `course_categories`: scoped unique slug constraints for institution and global categories; parent and scope/slug indexes.
- `course_tags`: scoped unique slug constraints for institution and global tags; scope/slug index.
- `course_category_links`: unique course/category pair and category lookup index.
- `course_tag_links`: unique course/tag pair and tag lookup index.
- `course_prerequisites`: unique course/prerequisite pair and prerequisite lookup index.
- `learning_outcomes`: unique course/position pair and course lookup index.

## DBD-006-006 Cache And Events
Published catalog list/detail reads are cached in Redis with
`COURSE_CATALOG_CACHE_TTL_SECONDS`, default `300`. Management reads and non-published
records bypass cache. Course, category, tag, prerequisite, and learning outcome writes
invalidate catalog cache keys.

`course-service` emits structured local events for `CourseCreated`, `CoursePublished`,
and `CourseArchived`. The payload is intentionally transport-neutral; Kafka transport
remains future [T-020](../tasks/T-020-kafka-eventing.md) scope.
