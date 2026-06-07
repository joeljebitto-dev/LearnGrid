# API-007 Course Structure And Versioning

Related task: [T-007](../tasks/T-007-course-structure-versioning.md)  
Related spec: [SPEC-007](../specs/007-course-structure-versioning.md)  
Related database design: [DBD-007](../db-design/DBD-007-course-structure-versioning.md)  
Development reference: [DEVELOPMENT.md](../DEVELOPMENT.md#course-structure-and-versioning)

## API-007-001 Scope
`course-service` exposes ordered course structure APIs under `/api/courses/`.
All endpoints require a bearer access token. Management operations require
`course.manage` at the course institution scope. Published structure reads require
`course.view`; draft, archived, and deleted structure reads require `course.manage`.

## API-007-002 Structure Read
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/<uuid>/structure/` | Read nested course modules, lessons, and topics | `course.view` for published structure; `course.manage` for management structure |

Published reads include published modules and published lessons only. Management reads include
draft, published, and archived active structure records.

## API-007-003 Module Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/<uuid>/modules/` | List modules in a course | `course.view` or `course.manage` |
| `POST` | `/api/courses/<uuid>/modules/` | Create a module | `course.manage` |
| `GET` | `/api/courses/modules/<uuid>/` | Read one module | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/modules/<uuid>/` | Update module fields | `course.manage` |
| `DELETE` | `/api/courses/modules/<uuid>/` | Soft-archive a module | `course.manage` |
| `POST` | `/api/courses/<uuid>/modules/reorder/` | Transactionally reorder modules | `course.manage` |

Module create/update body fields: `title`, `description`, optional `position`, and optional
`status`. Reorder body: `module_ids`, the complete active ordered module ID list.

## API-007-004 Lesson Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/modules/<uuid>/lessons/` | List lessons in a module | `course.view` or `course.manage` |
| `POST` | `/api/courses/modules/<uuid>/lessons/` | Create a lesson | `course.manage` |
| `GET` | `/api/courses/lessons/<uuid>/` | Read one lesson | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/lessons/<uuid>/` | Update lesson fields or move inside the same course | `course.manage` |
| `DELETE` | `/api/courses/lessons/<uuid>/` | Soft-archive a lesson | `course.manage` |
| `POST` | `/api/courses/lessons/<uuid>/publish/` | Publish a lesson | `course.manage` |
| `POST` | `/api/courses/modules/<uuid>/lessons/reorder/` | Transactionally reorder lessons | `course.manage` |

Lesson create/update body fields: `module_id` on update, `title`, `summary`, optional
`position`, optional `status`, and optional `content_asset_id`. Reorder body: `lesson_ids`,
the complete active ordered lesson ID list. Publishing emits `LessonPublished`.

## API-007-005 Topic Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/lessons/<uuid>/topics/` | List topics in a lesson | `course.view` or `course.manage` |
| `POST` | `/api/courses/lessons/<uuid>/topics/` | Create a topic | `course.manage` |
| `GET` | `/api/courses/topics/<uuid>/` | Read one topic | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/topics/<uuid>/` | Update topic fields | `course.manage` |
| `DELETE` | `/api/courses/topics/<uuid>/` | Delete a topic | `course.manage` |
| `POST` | `/api/courses/lessons/<uuid>/topics/reorder/` | Transactionally reorder topics | `course.manage` |

Topic create/update body fields: `title`, optional `position`, and optional `content_asset_id`.
Reorder body: `topic_ids`, the complete ordered topic ID list.

## API-007-006 Revision Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/<uuid>/revisions/` | List course revision snapshots | `course.manage` |
| `POST` | `/api/courses/<uuid>/revisions/` | Create a structure snapshot revision | `course.manage` |
| `GET` | `/api/courses/revisions/<uuid>/` | Read one revision snapshot | `course.manage` |

Revision create body accepts optional `created_by_profile_id`; when omitted, the authenticated
token subject is used as the local fallback. Version numbers increment per course.

## API-007-007 Failure Behavior
- Auth-service denial or network failure denies access.
- Reorder payloads must include exactly the current active IDs for that scope.
- Duplicate positions, cross-course lesson moves, missing records, and invalid parent IDs return validation errors.
- Published student reads hide draft lessons and non-published modules.
