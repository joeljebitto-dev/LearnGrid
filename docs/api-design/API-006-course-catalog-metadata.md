# API-006 Course Catalog And Metadata

Related task: [T-006](../tasks/T-006-course-catalog-metadata.md)  
Related spec: [SPEC-006](../specs/006-course-catalog-metadata.md)  
Related database design: [DBD-006](../db-design/DBD-006-course-catalog-metadata.md)  
Development reference: [DEVELOPMENT.md](../DEVELOPMENT.md#course-catalog-and-metadata)

## API-006-001 Scope
`course-service` exposes the implemented T-006 APIs under `/api/courses/`.
All endpoints require a bearer access token. Authorization is checked remotely through
`auth-service` using `course.view` or `course.manage` at institution or platform scope.

## API-006-002 Course Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/` | Search catalog courses | `course.view` or `course.manage` |
| `POST` | `/api/courses/` | Create draft course with metadata | `course.manage` at request `institution_id` |
| `GET` | `/api/courses/<uuid>/` | Read one course | `course.view` for published; `course.manage` for draft/archived/deleted |
| `PATCH` | `/api/courses/<uuid>/` | Update course fields and replace supplied metadata arrays | `course.manage` |
| `POST` | `/api/courses/<uuid>/publish/` | Publish course | `course.manage` |
| `POST` | `/api/courses/<uuid>/archive/` | Archive course | `course.manage` |
| `DELETE` | `/api/courses/<uuid>/` | Soft-delete course | `course.manage` |

Create/update body parameters: `institution_id`, `owner_profile_id`, `title`, `slug`,
`description`, `difficulty_level`, `thumbnail_asset_id`, `category_ids`, `tag_ids`,
`prerequisite_course_ids`, and `learning_outcomes`. `slug` is generated from `title`
when omitted. `learning_outcomes` accepts ordered objects with `description` and
optional `position`.

List query parameters: `institution_id`, `owner_profile_id`, `status`,
`difficulty_level`, `category_id`, `tag_id`, `q`, `sort`, `page`, and `page_size`.
Viewer discovery returns published courses only. Management users may list draft,
published, archived, and deleted courses by status.

## API-006-003 Category Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/categories/` | Search categories | `course.view` or `course.manage` |
| `POST` | `/api/courses/categories/` | Create global or institution category | `course.manage` |
| `GET` | `/api/courses/categories/<uuid>/` | Read category | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/categories/<uuid>/` | Update category name, slug, or parent | `course.manage` |
| `DELETE` | `/api/courses/categories/<uuid>/` | Delete category and links | `course.manage` |

Request body parameters: `institution_id`, `name`, optional `slug`, and optional
`parent_category_id`. Category slugs are normalized and unique within the global or
institution scope.

Query parameters: `institution_id`, `q`, `sort`, `page`, and `page_size`.

## API-006-004 Tag Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/tags/` | Search tags | `course.view` or `course.manage` |
| `POST` | `/api/courses/tags/` | Create global or institution tag | `course.manage` |
| `GET` | `/api/courses/tags/<uuid>/` | Read tag | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/tags/<uuid>/` | Update tag name or slug | `course.manage` |
| `DELETE` | `/api/courses/tags/<uuid>/` | Delete tag and links | `course.manage` |

Request body parameters: `institution_id`, `name`, and optional `slug`.
Query parameters: `institution_id`, `q`, `sort`, `page`, and `page_size`.

## API-006-005 Failure Behavior
- Missing or invalid JWTs return authentication errors.
- Auth-service denial or network failure denies authorization.
- Duplicate slugs, invalid metadata IDs, self-prerequisites, cross-institution prerequisites, and duplicate learning outcome positions return validation errors.
- Redis failures do not fail catalog reads; the database is used as fallback.

## API-006-006 Tests
Implemented tests cover course creation, metadata replacement, lifecycle visibility,
category/tag CRUD, prerequisite validation, Redis cache use and fallback, event publisher
calls, authorization denial, and list query-count behavior.
