# SPEC-006 Course Catalog And Metadata

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-006](../tasks/T-006-course-catalog-metadata.md)  
Related schema: [course_db](../DATABASE_SCHEMA.md#course_db)

## Functional Requirements
- SPEC-006-FR-001 Instructors and admins shall create courses.
- SPEC-006-FR-002 Instructors and admins shall update courses.
- SPEC-006-FR-003 Instructors and admins shall publish courses.
- SPEC-006-FR-004 Instructors and admins shall archive courses.
- SPEC-006-FR-005 Instructors and admins shall delete courses.
- SPEC-006-FR-006 Courses shall support categories, tags, difficulty levels, prerequisites, descriptions, thumbnails, and learning outcomes.
- SPEC-006-FR-007 Course lifecycle shall support draft, published, archived, and deleted states.

## Non-Functional Requirements
- SPEC-006-NFR-001 Course catalog data may be cached in Redis.
- SPEC-006-NFR-002 Course list APIs shall support pagination, filtering, and sorting.
- SPEC-006-NFR-003 Catalog queries shall avoid N+1 query patterns.

## Acceptance Criteria
- SPEC-006-AC-001 A permitted instructor can create a draft course.
- SPEC-006-AC-002 Published courses appear in permitted catalog views.
- SPEC-006-AC-003 Archived or deleted courses are hidden from normal student discovery.
- SPEC-006-AC-004 Course category, tag, prerequisite, and outcome metadata can be managed and queried.
