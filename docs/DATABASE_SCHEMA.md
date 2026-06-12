# LearnGrid LMS Database Schema

Source: [SRD.pdf](SRD.pdf)  
Related index: [SPECIFICATION.md](SPECIFICATION.md)  
Related tasks: [TASKS.md](TASKS.md)

## DB-000 Schema Rules
- Production uses PostgreSQL with database-per-service ownership.
- Services do not directly query another service database.
- In-service relationships use database foreign keys.
- Cross-service references are stored as UUID values without database foreign keys.
- Public identifiers use UUIDs.
- All schema changes use migrations.
- Index foreign keys, lookup fields, status fields, and frequent filters.
- Use soft delete with `deleted_at TIMESTAMPTZ` where history must be preserved.
- Prefer structured columns for searchable business data.
- Use `JSONB` only for flexible metadata, settings, snapshots, or event payloads.

## DB-001 Standard Fields
Unless explicitly stated otherwise, service tables use these standard fields:

| Field | PostgreSQL datatype | Nullable | Default | Notes |
| --- | --- | --- | --- | --- |
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Updated by application or trigger |
| `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete where required |

## Database Ownership
| Database | Service | Related specs |
| --- | --- | --- |
| `auth_db` | auth-service | [SPEC-001](specs/001-authentication-lifecycle.md), [SPEC-002](specs/002-token-session-security.md), [SPEC-003](specs/003-rbac-object-authorization.md) |
| `user_db` | user-service | [SPEC-004](specs/004-user-profile-management.md), [SPEC-005](specs/005-institution-batch-department-management.md) |
| `course_db` | course-service | [SPEC-006](specs/006-course-catalog-metadata.md), [SPEC-007](specs/007-course-structure-versioning.md) |
| `content_db` | content-service | [SPEC-008](specs/008-content-upload-storage-access.md) |
| `enrollment_db` | enrollment-service | [SPEC-009](specs/009-enrollment-access-management.md) |
| `progress_db` | progress-service | [SPEC-010](specs/010-learning-progress-tracking.md) |
| `assessment_db` | assessment-service | [SPEC-012](specs/012-assessment-authoring.md), [SPEC-013](specs/013-quiz-attempts-exams.md), [SPEC-014](specs/014-assignment-submissions.md) |
| `grading_db` | grading-service | [SPEC-015](specs/015-grading-results-audit.md), [SPEC-016](specs/016-certificates.md) |
| `notification_db` | notification-service | [SPEC-017](specs/017-notifications.md) |
| `analytics_db` | analytics-service | [SPEC-011](specs/011-dashboards-portals.md), [SPEC-018](specs/018-search-reporting-analytics.md), [SPEC-020](specs/020-kafka-eventing.md) |

## auth_db

### DB-AUTH-001 `accounts`
Purpose: Authentication account record linked to profile data by UUID.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-001-F002 | `email` | `CITEXT` | No | None | Unique, normalized login identifier |
| DB-AUTH-001-F003 | `phone` | `VARCHAR(32)` | Yes | None | Unique where not null |
| DB-AUTH-001-F004 | `status` | `VARCHAR(24)` | No | `'pending'` | Enum: `pending`, `active`, `locked`, `disabled`, `deactivated` |
| DB-AUTH-001-F005 | `is_staff` | `BOOLEAN` | No | `false` | Administrative login marker |
| DB-AUTH-001-F006 | `last_login_at` | `TIMESTAMPTZ` | Yes | None | Login audit summary |
| DB-AUTH-001-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-AUTH-001-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-AUTH-001-F009 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_accounts_status`, `idx_accounts_deleted_at`, unique `uq_accounts_email`, partial unique `uq_accounts_phone_not_null`.

### DB-AUTH-002 `credentials`
Purpose: Secure credential material for an account.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-002-F002 | `account_id` | `UUID` | No | None | FK to `accounts.id`, unique |
| DB-AUTH-002-F003 | `password_hash` | `TEXT` | No | None | Secure password hash |
| DB-AUTH-002-F004 | `password_changed_at` | `TIMESTAMPTZ` | Yes | None | Used for token invalidation |
| DB-AUTH-002-F005 | `must_change_password` | `BOOLEAN` | No | `false` | Enforced after admin reset/import |
| DB-AUTH-002-F006 | `failed_attempt_count` | `INTEGER` | No | `0` | Lockout input |
| DB-AUTH-002-F007 | `locked_until` | `TIMESTAMPTZ` | Yes | None | Temporary lockout timestamp |
| DB-AUTH-002-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-AUTH-002-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_credentials_locked_until`.

### DB-AUTH-003 `refresh_tokens`
Purpose: Persist refresh token lifecycle and revocation state.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-003-F002 | `account_id` | `UUID` | No | None | FK to `accounts.id` |
| DB-AUTH-003-F003 | `token_jti` | `UUID` | No | None | Unique JWT ID |
| DB-AUTH-003-F004 | `token_hash` | `TEXT` | No | None | Stored hash only |
| DB-AUTH-003-F005 | `issued_at` | `TIMESTAMPTZ` | No | `now()` | Issue timestamp |
| DB-AUTH-003-F006 | `expires_at` | `TIMESTAMPTZ` | No | None | Expiry timestamp |
| DB-AUTH-003-F007 | `revoked_at` | `TIMESTAMPTZ` | Yes | None | Revocation timestamp |
| DB-AUTH-003-F008 | `device_label` | `VARCHAR(128)` | Yes | None | Client-provided device label |
| DB-AUTH-003-F009 | `ip_address` | `INET` | Yes | None | Last issue IP |
| DB-AUTH-003-F010 | `user_agent` | `TEXT` | Yes | None | Last issue user agent |

Indexes: `idx_refresh_tokens_account_id`, `idx_refresh_tokens_expires_at`, unique `uq_refresh_tokens_token_jti`.

### DB-AUTH-004 `token_blacklist`
Purpose: Store revoked access or refresh token identifiers.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-004-F002 | `token_jti` | `UUID` | No | None | Unique token identifier |
| DB-AUTH-004-F003 | `account_id` | `UUID` | Yes | None | FK to `accounts.id` |
| DB-AUTH-004-F004 | `reason` | `VARCHAR(64)` | No | `'logout'` | Enum: `logout`, `rotation`, `admin_revoke`, `password_change`, `compromised` |
| DB-AUTH-004-F005 | `expires_at` | `TIMESTAMPTZ` | No | None | Cleanup boundary |
| DB-AUTH-004-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_token_blacklist_token_jti`, `idx_token_blacklist_expires_at`.

### DB-AUTH-005 `password_reset_tokens`
Purpose: Track password reset requests while OTP/token cache is held in Redis.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-005-F002 | `account_id` | `UUID` | No | None | FK to `accounts.id` |
| DB-AUTH-005-F003 | `token_hash` | `TEXT` | No | None | Stored hash only |
| DB-AUTH-005-F004 | `status` | `VARCHAR(24)` | No | `'pending'` | Enum: `pending`, `used`, `expired`, `revoked` |
| DB-AUTH-005-F005 | `requested_ip` | `INET` | Yes | None | Request source |
| DB-AUTH-005-F006 | `expires_at` | `TIMESTAMPTZ` | No | None | Expiry timestamp |
| DB-AUTH-005-F007 | `used_at` | `TIMESTAMPTZ` | Yes | None | Completion timestamp |
| DB-AUTH-005-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_password_reset_account_id`, `idx_password_reset_status_expires_at`.

### DB-AUTH-006 `login_audit_logs`
Purpose: Preserve login, logout, and authentication failure audit history.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-006-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-006-F002 | `account_id` | `UUID` | Yes | None | FK to `accounts.id`; nullable for unknown email failures |
| DB-AUTH-006-F003 | `email_attempted` | `CITEXT` | Yes | None | Attempted login identifier |
| DB-AUTH-006-F004 | `event_type` | `VARCHAR(40)` | No | None | Enum: `login_success`, `login_failure`, `logout`, `token_refresh`, `password_reset` |
| DB-AUTH-006-F005 | `ip_address` | `INET` | Yes | None | Request IP |
| DB-AUTH-006-F006 | `user_agent` | `TEXT` | Yes | None | Request user agent |
| DB-AUTH-006-F007 | `metadata` | `JSONB` | No | `'{}'::jsonb` | Flexible audit details |
| DB-AUTH-006-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit timestamp |

Indexes: `idx_login_audit_account_id_created_at`, `idx_login_audit_event_type`, `idx_login_audit_email_attempted`.

### DB-AUTH-007 `roles`
Purpose: Role definitions for platform and institution scopes.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-007-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-007-F002 | `code` | `VARCHAR(64)` | No | None | Unique; examples: `super_admin`, `institution_admin`, `instructor`, `teaching_assistant`, `student`, `parent_guardian` |
| DB-AUTH-007-F003 | `name` | `VARCHAR(128)` | No | None | Display name |
| DB-AUTH-007-F004 | `scope_type` | `VARCHAR(32)` | No | `'institution'` | Enum: `platform`, `institution`, `course` |
| DB-AUTH-007-F005 | `is_system` | `BOOLEAN` | No | `false` | Prevents accidental deletion |
| DB-AUTH-007-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-AUTH-007-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_roles_code`, `idx_roles_scope_type`.

### DB-AUTH-008 `permissions`
Purpose: Permission catalog used by backend authorization checks.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-008-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-008-F002 | `code` | `VARCHAR(128)` | No | None | Unique action code |
| DB-AUTH-008-F003 | `resource` | `VARCHAR(64)` | No | None | Resource name |
| DB-AUTH-008-F004 | `action` | `VARCHAR(64)` | No | None | Action name |
| DB-AUTH-008-F005 | `description` | `TEXT` | Yes | None | Human-readable purpose |
| DB-AUTH-008-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_permissions_code`, `idx_perm_resource_action`.

### DB-AUTH-009 `role_permissions`
Purpose: Many-to-many mapping from roles to permissions.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-009-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-009-F002 | `role_id` | `UUID` | No | None | FK to `roles.id` |
| DB-AUTH-009-F003 | `permission_id` | `UUID` | No | None | FK to `permissions.id` |
| DB-AUTH-009-F004 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_role_perm_role_permission`, `idx_role_perm_permission`.

### DB-AUTH-010 `role_assignments`
Purpose: Assign roles to accounts at platform, institution, course, or object scope.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-010-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-010-F002 | `account_id` | `UUID` | No | None | FK to `accounts.id` |
| DB-AUTH-010-F003 | `role_id` | `UUID` | No | None | FK to `roles.id` |
| DB-AUTH-010-F004 | `scope_type` | `VARCHAR(32)` | No | `'platform'` | Enum: `platform`, `institution`, `course`, `assessment` |
| DB-AUTH-010-F005 | `scope_id` | `UUID` | Yes | None | Cross-service UUID reference where applicable |
| DB-AUTH-010-F006 | `assigned_by_account_id` | `UUID` | Yes | None | FK to `accounts.id` |
| DB-AUTH-010-F007 | `assigned_at` | `TIMESTAMPTZ` | No | `now()` | Assignment timestamp |
| DB-AUTH-010-F008 | `revoked_at` | `TIMESTAMPTZ` | Yes | None | Revocation timestamp |

Indexes: `idx_role_assign_account`, `idx_role_assign_scope`, unique partial `uq_active_role_assign_platform`, unique partial `uq_active_role_assign_scoped`.

### DB-AUTH-011 `authorization_audit_logs`
Purpose: Preserve RBAC role assignment and role-permission change history.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-AUTH-011-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-AUTH-011-F002 | `actor_account_id` | `UUID` | Yes | None | FK to `accounts.id`; user who made the change |
| DB-AUTH-011-F003 | `target_account_id` | `UUID` | Yes | None | FK to `accounts.id`; user affected by the change |
| DB-AUTH-011-F004 | `event_type` | `VARCHAR(64)` | No | None | Enum: `role_assignment_created`, `role_assignment_revoked`, `role_permission_granted`, `role_permission_revoked` |
| DB-AUTH-011-F005 | `role_id` | `UUID` | Yes | None | FK to `roles.id` |
| DB-AUTH-011-F006 | `permission_id` | `UUID` | Yes | None | FK to `permissions.id` |
| DB-AUTH-011-F007 | `role_assignment_id` | `UUID` | Yes | None | FK to `role_assignments.id` |
| DB-AUTH-011-F008 | `scope_type` | `VARCHAR(32)` | No | `''` | Scope captured at change time |
| DB-AUTH-011-F009 | `scope_id` | `UUID` | Yes | None | Cross-service UUID reference where applicable |
| DB-AUTH-011-F010 | `ip_address` | `INET` | Yes | None | Request IP |
| DB-AUTH-011-F011 | `user_agent` | `TEXT` | Yes | None | Request user agent |
| DB-AUTH-011-F012 | `metadata` | `JSONB` | No | `'{}'::jsonb` | Flexible audit details |
| DB-AUTH-011-F013 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit timestamp |

Indexes: `idx_auth_audit_actor_created`, `idx_auth_audit_target`, `idx_auth_audit_event_type`.

## user_db

### DB-USER-001 `institutions`
Purpose: Institution tenant profile.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-001-F002 | `name` | `VARCHAR(255)` | No | None | Institution name |
| DB-USER-001-F003 | `code` | `VARCHAR(64)` | No | None | Unique institution code |
| DB-USER-001-F004 | `status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `suspended`, `archived` |
| DB-USER-001-F005 | `settings` | `JSONB` | No | `'{}'::jsonb` | Tenant settings |
| DB-USER-001-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-001-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-001-F008 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: unique `uq_institutions_code`, `idx_institutions_status`.

### DB-USER-002 `departments`
Purpose: Institution department records.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-002-F002 | `institution_id` | `UUID` | No | None | FK to `institutions.id` |
| DB-USER-002-F003 | `name` | `VARCHAR(255)` | No | None | Department name |
| DB-USER-002-F004 | `code` | `VARCHAR(64)` | No | None | Unique per institution |
| DB-USER-002-F005 | `status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `inactive`, `archived` |
| DB-USER-002-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-002-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-002-F008 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: unique `uq_departments_institution_code`, `idx_departments_institution_status`.

### DB-USER-003 `batches`
Purpose: Academic batch or cohort grouping inside an institution.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-003-F002 | `institution_id` | `UUID` | No | None | FK to `institutions.id` |
| DB-USER-003-F003 | `department_id` | `UUID` | Yes | None | FK to `departments.id` |
| DB-USER-003-F004 | `name` | `VARCHAR(255)` | No | None | Batch name |
| DB-USER-003-F005 | `start_date` | `DATE` | Yes | None | Academic start |
| DB-USER-003-F006 | `end_date` | `DATE` | Yes | None | Academic end |
| DB-USER-003-F007 | `status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `completed`, `archived` |
| DB-USER-003-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-003-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-003-F010 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_batches_institution_status`, `idx_batches_department_id`.

### DB-USER-004 `user_profiles`
Purpose: Profile record separate from authentication credentials.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-004-F002 | `auth_account_id` | `UUID` | No | None | Cross-service UUID reference to `auth_db.accounts.id`; unique |
| DB-USER-004-F003 | `institution_id` | `UUID` | Yes | None | FK to `institutions.id` |
| DB-USER-004-F004 | `first_name` | `VARCHAR(128)` | No | None | Searchable profile field |
| DB-USER-004-F005 | `last_name` | `VARCHAR(128)` | No | None | Searchable profile field |
| DB-USER-004-F006 | `display_name` | `VARCHAR(255)` | Yes | None | UI display name |
| DB-USER-004-F007 | `avatar_url` | `TEXT` | Yes | None | External or signed URL |
| DB-USER-004-F008 | `status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `inactive`, `deactivated` |
| DB-USER-004-F009 | `metadata` | `JSONB` | No | `'{}'::jsonb` | Flexible profile metadata |
| DB-USER-004-F010 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-004-F011 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-004-F012 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: unique `uq_user_profiles_auth_account_id`, `idx_user_profiles_institution_status`, `idx_user_profiles_name`.

### DB-USER-005 `student_profiles`
Purpose: Student-specific profile attributes.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-005-F002 | `user_profile_id` | `UUID` | No | None | FK to `user_profiles.id`, unique |
| DB-USER-005-F003 | `student_number` | `VARCHAR(64)` | No | None | Unique per institution |
| DB-USER-005-F004 | `batch_id` | `UUID` | Yes | None | FK to `batches.id` |
| DB-USER-005-F005 | `department_id` | `UUID` | Yes | None | FK to `departments.id` |
| DB-USER-005-F006 | `guardian_profile_id` | `UUID` | Yes | None | FK to `user_profiles.id` |
| DB-USER-005-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-005-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_student_profiles_student_number`, `idx_student_profiles_batch_id`, `idx_student_profiles_department_id`.

### DB-USER-006 `instructor_profiles`
Purpose: Instructor-specific profile attributes.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-006-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-006-F002 | `user_profile_id` | `UUID` | No | None | FK to `user_profiles.id`, unique |
| DB-USER-006-F003 | `employee_number` | `VARCHAR(64)` | Yes | None | Unique per institution where present |
| DB-USER-006-F004 | `department_id` | `UUID` | Yes | None | FK to `departments.id` |
| DB-USER-006-F005 | `title` | `VARCHAR(128)` | Yes | None | Instructor title |
| DB-USER-006-F006 | `bio` | `TEXT` | Yes | None | Instructor biography |
| DB-USER-006-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-006-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: partial unique `uq_instructor_profiles_employee_number`, `idx_instructor_profiles_department_id`.

### DB-USER-007 `admin_profiles`
Purpose: Institution or platform admin profile attributes.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-007-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-007-F002 | `user_profile_id` | `UUID` | No | None | FK to `user_profiles.id`, unique |
| DB-USER-007-F003 | `admin_type` | `VARCHAR(32)` | No | `'institution_admin'` | Enum: `super_admin`, `institution_admin` |
| DB-USER-007-F004 | `department_id` | `UUID` | Yes | None | FK to `departments.id` |
| DB-USER-007-F005 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-007-F006 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_admin_profiles_admin_type`, `idx_admin_profiles_department_id`.

### DB-USER-008 `user_import_jobs`
Purpose: Future CSV or Excel bulk import tracking.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-USER-008-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-USER-008-F002 | `institution_id` | `UUID` | No | None | FK to `institutions.id` |
| DB-USER-008-F003 | `requested_by_profile_id` | `UUID` | No | None | FK to `user_profiles.id` |
| DB-USER-008-F004 | `source_file_asset_id` | `UUID` | Yes | None | Cross-service UUID reference to content asset |
| DB-USER-008-F005 | `status` | `VARCHAR(24)` | No | `'queued'` | Enum: `queued`, `processing`, `completed`, `failed`, `cancelled` |
| DB-USER-008-F006 | `summary` | `JSONB` | No | `'{}'::jsonb` | Import counts and errors |
| DB-USER-008-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-USER-008-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_user_import_jobs_institution_status`, `idx_user_import_jobs_requested_by`.

## course_db

### DB-COURSE-001 `courses`
Purpose: Course catalog and lifecycle record.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-001-F002 | `institution_id` | `UUID` | No | None | Cross-service UUID reference to institution |
| DB-COURSE-001-F003 | `owner_profile_id` | `UUID` | No | None | Cross-service UUID reference to instructor/admin profile |
| DB-COURSE-001-F004 | `title` | `VARCHAR(255)` | No | None | Course title |
| DB-COURSE-001-F005 | `slug` | `VARCHAR(255)` | No | None | Unique per institution |
| DB-COURSE-001-F006 | `description` | `TEXT` | Yes | None | Course description |
| DB-COURSE-001-F007 | `difficulty_level` | `VARCHAR(32)` | Yes | None | Enum: `beginner`, `intermediate`, `advanced` |
| DB-COURSE-001-F008 | `thumbnail_asset_id` | `UUID` | Yes | None | Cross-service UUID reference to content asset |
| DB-COURSE-001-F009 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `published`, `archived`, `deleted` |
| DB-COURSE-001-F010 | `published_at` | `TIMESTAMPTZ` | Yes | None | Publish timestamp |
| DB-COURSE-001-F011 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-001-F012 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-001-F013 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: unique `uq_courses_institution_slug`, `idx_courses_institution_status`, `idx_courses_owner_profile_id`.

### DB-COURSE-002 `course_categories`
Purpose: Course category taxonomy.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-002-F002 | `institution_id` | `UUID` | Yes | None | Cross-service UUID reference; null for global |
| DB-COURSE-002-F003 | `name` | `VARCHAR(128)` | No | None | Category name |
| DB-COURSE-002-F004 | `slug` | `VARCHAR(128)` | No | None | Unique per institution/global |
| DB-COURSE-002-F005 | `parent_category_id` | `UUID` | Yes | None | FK to `course_categories.id` |
| DB-COURSE-002-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-002-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_course_categories_scope_slug`, `idx_course_categories_parent`.

### DB-COURSE-003 `course_tags`
Purpose: Tags for course discovery and filtering.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-003-F002 | `institution_id` | `UUID` | Yes | None | Cross-service UUID reference; null for global |
| DB-COURSE-003-F003 | `name` | `VARCHAR(128)` | No | None | Tag name |
| DB-COURSE-003-F004 | `slug` | `VARCHAR(128)` | No | None | Unique per institution/global |
| DB-COURSE-003-F005 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_course_tags_scope_slug`.

### DB-COURSE-004 `course_category_links`
Purpose: Many-to-many link between courses and categories.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-004-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-004-F003 | `category_id` | `UUID` | No | None | FK to `course_categories.id` |
| DB-COURSE-004-F004 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_course_category_links_course_category`, `idx_course_category_links_category_id`.

### DB-COURSE-005 `course_tag_links`
Purpose: Many-to-many link between courses and tags.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-005-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-005-F003 | `tag_id` | `UUID` | No | None | FK to `course_tags.id` |
| DB-COURSE-005-F004 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_course_tag_links_course_tag`, `idx_course_tag_links_tag_id`.

### DB-COURSE-006 `course_prerequisites`
Purpose: Course prerequisite relationships.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-006-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-006-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-006-F003 | `prerequisite_course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-006-F004 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_course_prerequisites_course_prerequisite`, `idx_course_prerequisites_prerequisite`.

### DB-COURSE-007 `course_modules`
Purpose: Ordered modules inside a course.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-007-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-007-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-007-F003 | `title` | `VARCHAR(255)` | No | None | Module title |
| DB-COURSE-007-F004 | `description` | `TEXT` | Yes | None | Module description |
| DB-COURSE-007-F005 | `position` | `INTEGER` | No | None | Ordered position |
| DB-COURSE-007-F006 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `published`, `archived` |
| DB-COURSE-007-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-007-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-007-F009 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: unique `uq_course_modules_course_position`, `idx_modules_course_status`.

### DB-COURSE-008 `lessons`
Purpose: Ordered lessons inside modules.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-008-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-008-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-008-F003 | `module_id` | `UUID` | No | None | FK to `course_modules.id` |
| DB-COURSE-008-F004 | `title` | `VARCHAR(255)` | No | None | Lesson title |
| DB-COURSE-008-F005 | `summary` | `TEXT` | Yes | None | Lesson summary |
| DB-COURSE-008-F006 | `position` | `INTEGER` | No | None | Ordered position |
| DB-COURSE-008-F007 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `published`, `archived` |
| DB-COURSE-008-F008 | `content_asset_id` | `UUID` | Yes | None | Cross-service UUID reference to content asset |
| DB-COURSE-008-F009 | `published_at` | `TIMESTAMPTZ` | Yes | None | Publish timestamp |
| DB-COURSE-008-F010 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-008-F011 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-008-F012 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: unique `uq_lessons_module_position`, `idx_lessons_course_status`, `idx_lessons_module_id`.

### DB-COURSE-009 `topics`
Purpose: Lesson topics and sub-lesson organization.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-009-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-009-F002 | `lesson_id` | `UUID` | No | None | FK to `lessons.id` |
| DB-COURSE-009-F003 | `title` | `VARCHAR(255)` | No | None | Topic title |
| DB-COURSE-009-F004 | `position` | `INTEGER` | No | None | Ordered position |
| DB-COURSE-009-F005 | `content_asset_id` | `UUID` | Yes | None | Cross-service UUID reference to content asset |
| DB-COURSE-009-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-009-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_topics_lesson_position`, `idx_topics_lesson_id`.

### DB-COURSE-010 `learning_outcomes`
Purpose: Course learning outcomes.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-010-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-010-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-010-F003 | `description` | `TEXT` | No | None | Outcome text |
| DB-COURSE-010-F004 | `position` | `INTEGER` | No | None | Ordered position |
| DB-COURSE-010-F005 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-COURSE-010-F006 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_learning_outcomes_course_position`, `idx_learning_outcomes_course_id`.

### DB-COURSE-011 `course_revisions`
Purpose: Course versioning and content revision history.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-COURSE-011-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-COURSE-011-F002 | `course_id` | `UUID` | No | None | FK to `courses.id` |
| DB-COURSE-011-F003 | `version_number` | `INTEGER` | No | None | Incrementing course version |
| DB-COURSE-011-F004 | `snapshot` | `JSONB` | No | None | Course/module/lesson snapshot |
| DB-COURSE-011-F005 | `created_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-COURSE-011-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Revision timestamp |

Indexes: unique `uq_course_revisions_course_version`, `idx_course_revisions_course`.

## content_db

### DB-CONTENT-001 `content_assets`
Purpose: File or link metadata owned by content-service.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-CONTENT-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-CONTENT-001-F002 | `institution_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-CONTENT-001-F003 | `owner_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-CONTENT-001-F004 | `asset_type` | `VARCHAR(32)` | No | None | Enum: `video`, `pdf`, `document`, `image`, `link`, `assignment_resource` |
| DB-CONTENT-001-F005 | `title` | `VARCHAR(255)` | No | None | Asset title |
| DB-CONTENT-001-F006 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `published`, `deleted`, `quarantined` |
| DB-CONTENT-001-F007 | `metadata` | `JSONB` | No | `'{}'::jsonb` | Flexible asset metadata; stores upload workflow state such as `upload_status` |
| DB-CONTENT-001-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-CONTENT-001-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-CONTENT-001-F010 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_content_assets_inst_status`, `idx_content_assets_owner`, `idx_content_assets_asset_type`.

### DB-CONTENT-002 `file_metadata`
Purpose: Object storage metadata for uploaded files.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-CONTENT-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-CONTENT-002-F002 | `content_asset_id` | `UUID` | No | None | FK to `content_assets.id`, unique |
| DB-CONTENT-002-F003 | `storage_provider` | `VARCHAR(32)` | No | `'minio'` | Resolved provider from OD-002 |
| DB-CONTENT-002-F004 | `bucket_name` | `VARCHAR(255)` | No | None | MinIO bucket |
| DB-CONTENT-002-F005 | `object_key` | `TEXT` | No | None | MinIO object key |
| DB-CONTENT-002-F006 | `file_name` | `VARCHAR(255)` | No | None | Original file name |
| DB-CONTENT-002-F007 | `mime_type` | `VARCHAR(128)` | No | None | Validated MIME type |
| DB-CONTENT-002-F008 | `file_size_bytes` | `BIGINT` | No | None | Must be greater than 0 |
| DB-CONTENT-002-F009 | `checksum_sha256` | `CHAR(64)` | Yes | None | File checksum |
| DB-CONTENT-002-F010 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_file_metadata_asset_id`, `idx_file_metadata_mime_type`, `idx_file_metadata_object_key_hash`.

### DB-CONTENT-003 `content_permissions`
Purpose: Asset-level access grants.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-CONTENT-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-CONTENT-003-F002 | `content_asset_id` | `UUID` | No | None | FK to `content_assets.id` |
| DB-CONTENT-003-F003 | `grantee_type` | `VARCHAR(32)` | No | None | Enum: `profile`, `course`, `institution`, `role` |
| DB-CONTENT-003-F004 | `grantee_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-CONTENT-003-F005 | `permission` | `VARCHAR(32)` | No | `'view'` | Enum: `view`, `download`, `manage` |
| DB-CONTENT-003-F006 | `expires_at` | `TIMESTAMPTZ` | Yes | None | Optional access expiry |
| DB-CONTENT-003-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_content_permissions_grant`, `idx_content_permissions_asset`, `idx_content_perms_grantee`.

### DB-CONTENT-004 `signed_access_records`
Purpose: Track signed URL or authenticated download grants.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-CONTENT-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-CONTENT-004-F002 | `content_asset_id` | `UUID` | No | None | FK to `content_assets.id` |
| DB-CONTENT-004-F003 | `requested_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-CONTENT-004-F004 | `access_token_hash` | `TEXT` | No | None | Stored hash only |
| DB-CONTENT-004-F005 | `expires_at` | `TIMESTAMPTZ` | No | None | Signed URL expiry |
| DB-CONTENT-004-F006 | `used_at` | `TIMESTAMPTZ` | Yes | None | First access timestamp |
| DB-CONTENT-004-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_signed_access_asset_id`, `idx_signed_access_profile_id`, `idx_signed_access_expires_at`.

### DB-CONTENT-005 `content_versions`
Purpose: Content version metadata.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-CONTENT-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-CONTENT-005-F002 | `content_asset_id` | `UUID` | No | None | FK to `content_assets.id` |
| DB-CONTENT-005-F003 | `version_number` | `INTEGER` | No | None | Incrementing version |
| DB-CONTENT-005-F004 | `file_metadata_id` | `UUID` | Yes | None | FK to `file_metadata.id` |
| DB-CONTENT-005-F005 | `change_note` | `TEXT` | Yes | None | Version note |
| DB-CONTENT-005-F006 | `created_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-CONTENT-005-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Version timestamp |

Indexes: unique `uq_content_versions_asset_version`, `idx_content_versions_asset`.

## enrollment_db

### DB-ENROLL-001 `enrollments`
Purpose: Student course enrollment and lifecycle state.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ENROLL-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ENROLL-001-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-001-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-001-F004 | `institution_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-001-F005 | `status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `completed`, `expired`, `cancelled`, `suspended` |
| DB-ENROLL-001-F006 | `enrolled_by_profile_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ENROLL-001-F007 | `enrolled_at` | `TIMESTAMPTZ` | No | `now()` | Enrollment timestamp |
| DB-ENROLL-001-F008 | `completed_at` | `TIMESTAMPTZ` | Yes | None | Course completion |
| DB-ENROLL-001-F009 | `expires_at` | `TIMESTAMPTZ` | Yes | None | Access expiry |
| DB-ENROLL-001-F010 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ENROLL-001-F011 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_enrollments_student_course`, `idx_enroll_course_status`, `idx_enroll_student_status`, `idx_enroll_institution_id`.

### DB-ENROLL-002 `batch_enrollments`
Purpose: Batch-based enrollment jobs.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ENROLL-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ENROLL-002-F002 | `batch_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-002-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-002-F004 | `requested_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-002-F005 | `status` | `VARCHAR(24)` | No | `'queued'` | Enum: `queued`, `processing`, `completed`, `failed`, `cancelled` |
| DB-ENROLL-002-F006 | `summary` | `JSONB` | No | `'{}'::jsonb` | Created/failed counts |
| DB-ENROLL-002-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ENROLL-002-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_batch_enroll_batch_course`, `idx_batch_enroll_status`.

### DB-ENROLL-003 `cohort_enrollments`
Purpose: Cohort-based enrollment jobs.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ENROLL-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ENROLL-003-F002 | `cohort_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-003-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-003-F004 | `requested_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-003-F005 | `status` | `VARCHAR(24)` | No | `'queued'` | Enum: `queued`, `processing`, `completed`, `failed`, `cancelled` |
| DB-ENROLL-003-F006 | `summary` | `JSONB` | No | `'{}'::jsonb` | Created/failed counts |
| DB-ENROLL-003-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ENROLL-003-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_cohort_enroll_course`, `idx_cohort_enroll_status`.

### DB-ENROLL-004 `enrollment_history`
Purpose: Immutable enrollment status and access audit history.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ENROLL-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ENROLL-004-F002 | `enrollment_id` | `UUID` | No | None | FK to `enrollments.id` |
| DB-ENROLL-004-F003 | `from_status` | `VARCHAR(24)` | Yes | None | Previous status |
| DB-ENROLL-004-F004 | `to_status` | `VARCHAR(24)` | No | None | New status |
| DB-ENROLL-004-F005 | `changed_by_profile_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ENROLL-004-F006 | `reason` | `TEXT` | Yes | None | Change reason |
| DB-ENROLL-004-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit timestamp |

Indexes: `idx_enroll_history_enroll`, `idx_enroll_history_created`.

### DB-ENROLL-005 `access_grants`
Purpose: Derived course access grants for enforcement.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ENROLL-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ENROLL-005-F002 | `enrollment_id` | `UUID` | No | None | FK to `enrollments.id` |
| DB-ENROLL-005-F003 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-005-F004 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ENROLL-005-F005 | `access_status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `expired`, `suspended`, `revoked` |
| DB-ENROLL-005-F006 | `valid_from` | `TIMESTAMPTZ` | No | `now()` | Access start |
| DB-ENROLL-005-F007 | `valid_until` | `TIMESTAMPTZ` | Yes | None | Access end |
| DB-ENROLL-005-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ENROLL-005-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_access_student_course`, `idx_access_course_status`, unique partial `uq_active_access_grant`.

## progress_db

### DB-PROGRESS-001 `lesson_progress`
Purpose: Track learner lesson completion.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-PROGRESS-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-PROGRESS-001-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-001-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-001-F004 | `lesson_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-001-F005 | `status` | `VARCHAR(24)` | No | `'not_started'` | Enum: `not_started`, `in_progress`, `completed` |
| DB-PROGRESS-001-F006 | `view_count` | `INTEGER` | No | `0` | Lesson views |
| DB-PROGRESS-001-F007 | `first_viewed_at` | `TIMESTAMPTZ` | Yes | None | First view |
| DB-PROGRESS-001-F008 | `completed_at` | `TIMESTAMPTZ` | Yes | None | Completion timestamp |
| DB-PROGRESS-001-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Update timestamp |

Indexes: unique `uq_lesson_progress_student_lesson`, `idx_lesson_progress_course`, `idx_lesson_progress_student`.

### DB-PROGRESS-002 `video_progress`
Purpose: Track learner video playback progress.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-PROGRESS-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-PROGRESS-002-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-002-F003 | `content_asset_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-002-F004 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-002-F005 | `last_position_seconds` | `INTEGER` | No | `0` | Last watched position |
| DB-PROGRESS-002-F006 | `duration_seconds` | `INTEGER` | Yes | None | Video duration |
| DB-PROGRESS-002-F007 | `percent_complete` | `NUMERIC(5,2)` | No | `0` | 0 to 100 |
| DB-PROGRESS-002-F008 | `completed_at` | `TIMESTAMPTZ` | Yes | None | Completion timestamp |
| DB-PROGRESS-002-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Update timestamp |

Indexes: unique `uq_video_progress_student_asset`, `idx_video_progress_course`.

### DB-PROGRESS-003 `assessment_progress`
Purpose: Track quiz, exam, and assignment progress summary.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-PROGRESS-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-PROGRESS-003-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-003-F003 | `assessment_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-003-F004 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-003-F005 | `status` | `VARCHAR(24)` | No | `'not_started'` | Enum: `not_started`, `started`, `submitted`, `graded` |
| DB-PROGRESS-003-F006 | `attempt_count` | `INTEGER` | No | `0` | Number of attempts |
| DB-PROGRESS-003-F007 | `last_submitted_at` | `TIMESTAMPTZ` | Yes | None | Last submission |
| DB-PROGRESS-003-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Update timestamp |

Indexes: unique `uq_assess_progress_student_assess`, `idx_assess_progress_course`.

### DB-PROGRESS-004 `course_progress`
Purpose: Course completion percentage and dashboard summary.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-PROGRESS-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-PROGRESS-004-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-004-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-PROGRESS-004-F004 | `completion_percent` | `NUMERIC(5,2)` | No | `0` | 0 to 100 |
| DB-PROGRESS-004-F005 | `lessons_completed` | `INTEGER` | No | `0` | Completed lesson count |
| DB-PROGRESS-004-F006 | `assessments_completed` | `INTEGER` | No | `0` | Completed assessment count |
| DB-PROGRESS-004-F007 | `status` | `VARCHAR(24)` | No | `'in_progress'` | Enum: `not_started`, `in_progress`, `completed` |
| DB-PROGRESS-004-F008 | `completed_at` | `TIMESTAMPTZ` | Yes | None | Completion timestamp |
| DB-PROGRESS-004-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Update timestamp |

Indexes: unique `uq_course_progress_student_course`, `idx_course_progress_course`, `idx_course_progress_student`.

### DB-PROGRESS-005 `progress_events`
Purpose: Idempotency and audit record for consumed progress events.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-PROGRESS-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-PROGRESS-005-F002 | `event_id` | `UUID` | No | None | Unique Kafka event ID |
| DB-PROGRESS-005-F003 | `event_type` | `VARCHAR(80)` | No | None | Event type |
| DB-PROGRESS-005-F004 | `aggregate_id` | `UUID` | No | None | Event aggregate |
| DB-PROGRESS-005-F005 | `payload` | `JSONB` | No | None | Event payload snapshot |
| DB-PROGRESS-005-F006 | `processed_at` | `TIMESTAMPTZ` | No | `now()` | Processing timestamp |

Indexes: unique `uq_progress_events_event_id`, `idx_progress_events_event_type`.

## assessment_db

Implementation note: `T-012` implements `DB-ASSESS-001` through `DB-ASSESS-005` and `DB-ASSESS-008`; `T-013` implements `DB-ASSESS-006`, `DB-ASSESS-007`, and `DB-ASSESS-010`; `T-014` implements `DB-ASSESS-009 assignment_submissions`.

### DB-ASSESS-001 `question_banks`
Purpose: Question bank owned by instructor or institution.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-001-F002 | `institution_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ASSESS-001-F003 | `owner_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ASSESS-001-F004 | `title` | `VARCHAR(255)` | No | None | Bank title |
| DB-ASSESS-001-F005 | `description` | `TEXT` | Yes | None | Bank description |
| DB-ASSESS-001-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-001-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-001-F008 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_question_banks_institution_id`, `idx_question_banks_owner_profile_id`.

### DB-ASSESS-002 `questions`
Purpose: Reusable assessment questions.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-002-F002 | `question_bank_id` | `UUID` | No | None | FK to `question_banks.id` |
| DB-ASSESS-002-F003 | `question_type` | `VARCHAR(32)` | No | None | Enum: `multiple_choice`, `multiple_select`, `true_false`, `short_answer`, `essay`, `file_upload`, `coding` |
| DB-ASSESS-002-F004 | `prompt` | `TEXT` | No | None | Question prompt |
| DB-ASSESS-002-F005 | `choices` | `JSONB` | Yes | None | Objective question choices |
| DB-ASSESS-002-F006 | `correct_answer` | `JSONB` | Yes | None | Objective grading data |
| DB-ASSESS-002-F007 | `points` | `NUMERIC(8,2)` | No | `0` | Available points |
| DB-ASSESS-002-F008 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `published`, `archived` |
| DB-ASSESS-002-F009 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-002-F010 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-002-F011 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_questions_bank_type`, `idx_questions_status`.

### DB-ASSESS-003 `assessments`
Purpose: Common assessment shell for quizzes, exams, and assignments.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-003-F002 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ASSESS-003-F003 | `lesson_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ASSESS-003-F004 | `created_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ASSESS-003-F005 | `assessment_type` | `VARCHAR(32)` | No | None | Enum: `quiz`, `exam`, `assignment` |
| DB-ASSESS-003-F006 | `title` | `VARCHAR(255)` | No | None | Assessment title |
| DB-ASSESS-003-F007 | `description` | `TEXT` | Yes | None | Assessment instructions |
| DB-ASSESS-003-F008 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `published`, `closed`, `archived` |
| DB-ASSESS-003-F009 | `available_from` | `TIMESTAMPTZ` | Yes | None | Start window |
| DB-ASSESS-003-F010 | `available_until` | `TIMESTAMPTZ` | Yes | None | End window |
| DB-ASSESS-003-F011 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-003-F012 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-003-F013 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_assessments_course_status`, `idx_assessments_type`, `idx_assessments_window`.

### DB-ASSESS-004 `quizzes`
Purpose: Quiz or exam configuration.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-004-F002 | `assessment_id` | `UUID` | No | None | FK to `assessments.id`, unique |
| DB-ASSESS-004-F003 | `time_limit_seconds` | `INTEGER` | Yes | None | Attempt time limit |
| DB-ASSESS-004-F004 | `max_attempts` | `INTEGER` | Yes | None | Null means unlimited |
| DB-ASSESS-004-F005 | `randomize_questions` | `BOOLEAN` | No | `false` | Randomization |
| DB-ASSESS-004-F006 | `auto_submit` | `BOOLEAN` | No | `true` | Auto-submit at time limit/end window |
| DB-ASSESS-004-F007 | `grading_policy` | `JSONB` | No | `'{}'::jsonb` | Scoring rules |
| DB-ASSESS-004-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-004-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_quizzes_assessment_id`.

### DB-ASSESS-005 `quiz_questions`
Purpose: Ordered question selection for a quiz.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-005-F002 | `quiz_id` | `UUID` | No | None | FK to `quizzes.id` |
| DB-ASSESS-005-F003 | `question_id` | `UUID` | No | None | FK to `questions.id` |
| DB-ASSESS-005-F004 | `position` | `INTEGER` | No | None | Ordered position |
| DB-ASSESS-005-F005 | `points_override` | `NUMERIC(8,2)` | Yes | None | Override points |
| DB-ASSESS-005-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_quiz_questions_quiz_position`, unique `uq_quiz_questions_quiz_question`.

### DB-ASSESS-006 `quiz_attempts`
Purpose: Student quiz or exam attempts.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-006-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-006-F002 | `quiz_id` | `UUID` | No | None | FK to `quizzes.id` |
| DB-ASSESS-006-F003 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ASSESS-006-F004 | `attempt_number` | `INTEGER` | No | None | Attempt sequence |
| DB-ASSESS-006-F005 | `status` | `VARCHAR(24)` | No | `'started'` | Enum: `started`, `submitted`, `auto_submitted`, `cancelled`, `graded` |
| DB-ASSESS-006-F006 | `started_at` | `TIMESTAMPTZ` | No | `now()` | Start time |
| DB-ASSESS-006-F007 | `submitted_at` | `TIMESTAMPTZ` | Yes | None | Submit time |
| DB-ASSESS-006-F008 | `score` | `NUMERIC(8,2)` | Yes | None | Calculated score |
| DB-ASSESS-006-F009 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-006-F010 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_quiz_attempts_quiz_student_attempt`, `idx_quiz_attempts_student_status`, `idx_quiz_attempts_quiz_status`.

### DB-ASSESS-007 `quiz_answers`
Purpose: Answers within quiz attempts.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-007-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-007-F002 | `quiz_attempt_id` | `UUID` | No | None | FK to `quiz_attempts.id` |
| DB-ASSESS-007-F003 | `question_id` | `UUID` | No | None | FK to `questions.id` |
| DB-ASSESS-007-F004 | `answer_payload` | `JSONB` | No | None | Submitted answer |
| DB-ASSESS-007-F005 | `score` | `NUMERIC(8,2)` | Yes | None | Per-question score |
| DB-ASSESS-007-F006 | `graded_at` | `TIMESTAMPTZ` | Yes | None | Grading timestamp |
| DB-ASSESS-007-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-007-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_quiz_answers_attempt_question`, `idx_quiz_answers_question_id`.

### DB-ASSESS-008 `assignments`
Purpose: Assignment-specific configuration.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-008-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-008-F002 | `assessment_id` | `UUID` | No | None | FK to `assessments.id`, unique |
| DB-ASSESS-008-F003 | `due_at` | `TIMESTAMPTZ` | Yes | None | Deadline |
| DB-ASSESS-008-F004 | `allow_late_submission` | `BOOLEAN` | No | `false` | Late submission rule |
| DB-ASSESS-008-F005 | `max_points` | `NUMERIC(8,2)` | No | `0` | Maximum score |
| DB-ASSESS-008-F006 | `resource_asset_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ASSESS-008-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-008-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_assignments_assessment_id`, `idx_assignments_due_at`.

### DB-ASSESS-009 `assignment_submissions`
Purpose: Student assignment submissions.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-009-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-009-F002 | `assignment_id` | `UUID` | No | None | FK to `assignments.id` |
| DB-ASSESS-009-F003 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ASSESS-009-F004 | `submission_text` | `TEXT` | Yes | None | Text response |
| DB-ASSESS-009-F005 | `attachment_asset_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ASSESS-009-F006 | `status` | `VARCHAR(24)` | No | `'submitted'` | Enum: `draft`, `submitted`, `late`, `withdrawn`, `graded` |
| DB-ASSESS-009-F007 | `submitted_at` | `TIMESTAMPTZ` | Yes | None | Submission timestamp |
| DB-ASSESS-009-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-ASSESS-009-F009 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_assignment_submissions_assignment_student`, `idx_assignment_submissions_status`, `idx_assignment_submissions_student_id`.

### DB-ASSESS-010 `submission_audit_logs`
Purpose: Preserve assessment submission audit trails.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ASSESS-010-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ASSESS-010-F002 | `submission_type` | `VARCHAR(32)` | No | None | Enum: `quiz_attempt`, `assignment_submission` |
| DB-ASSESS-010-F003 | `submission_id` | `UUID` | No | None | In-service submission UUID |
| DB-ASSESS-010-F004 | `event_type` | `VARCHAR(64)` | No | None | Submission event type |
| DB-ASSESS-010-F005 | `actor_profile_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ASSESS-010-F006 | `metadata` | `JSONB` | No | `'{}'::jsonb` | Audit metadata |
| DB-ASSESS-010-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit timestamp |

Indexes: `idx_submission_audit_submission`, `idx_submission_audit_event_type`, `idx_submission_audit_created_at`.

## grading_db

Implementation note: `T-015` implements `DB-GRADE-001` through `DB-GRADE-005`; `T-016` implements `DB-GRADE-006 certificate_eligibility` and `DB-GRADE-007 certificates`.

### DB-GRADE-001 `grading_rules`
Purpose: Course or assessment grading rule configuration.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-001-F002 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-001-F003 | `assessment_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-GRADE-001-F004 | `rule_type` | `VARCHAR(32)` | No | None | Enum: `points`, `percentage`, `weighted`, `pass_fail` |
| DB-GRADE-001-F005 | `configuration` | `JSONB` | No | None | Rule details |
| DB-GRADE-001-F006 | `created_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-001-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-GRADE-001-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_grading_rules_course_id`, `idx_grading_rules_assessment_id`.

### DB-GRADE-002 `grade_records`
Purpose: Student grade records for assessments or courses.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-002-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-002-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-002-F004 | `assessment_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-GRADE-002-F005 | `submission_id` | `UUID` | Yes | None | Cross-service UUID reference to assessment submission |
| DB-GRADE-002-F006 | `score` | `NUMERIC(8,2)` | No | `0` | Earned score |
| DB-GRADE-002-F007 | `max_score` | `NUMERIC(8,2)` | No | `0` | Maximum score |
| DB-GRADE-002-F008 | `status` | `VARCHAR(24)` | No | `'draft'` | Enum: `draft`, `calculated`, `reviewed`, `published`, `overridden` |
| DB-GRADE-002-F009 | `published_at` | `TIMESTAMPTZ` | Yes | None | Publication timestamp |
| DB-GRADE-002-F010 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-GRADE-002-F011 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_grade_records_student_course`, `idx_grade_records_assessment_status`, `idx_grade_records_course_status`.

### DB-GRADE-003 `manual_reviews`
Purpose: Manual grading workflow for subjective submissions.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-003-F002 | `grade_record_id` | `UUID` | No | None | FK to `grade_records.id` |
| DB-GRADE-003-F003 | `reviewer_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-003-F004 | `status` | `VARCHAR(24)` | No | `'pending'` | Enum: `pending`, `in_review`, `completed`, `returned` |
| DB-GRADE-003-F005 | `feedback` | `TEXT` | Yes | None | Reviewer feedback |
| DB-GRADE-003-F006 | `reviewed_at` | `TIMESTAMPTZ` | Yes | None | Review completion |
| DB-GRADE-003-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-GRADE-003-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_manual_reviews_grade_record`, `idx_manual_reviews_reviewer_status`.

### DB-GRADE-004 `grade_history`
Purpose: Immutable audit trail for grade changes.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-004-F002 | `grade_record_id` | `UUID` | No | None | FK to `grade_records.id` |
| DB-GRADE-004-F003 | `previous_score` | `NUMERIC(8,2)` | Yes | None | Previous score |
| DB-GRADE-004-F004 | `new_score` | `NUMERIC(8,2)` | No | None | New score |
| DB-GRADE-004-F005 | `changed_by_profile_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-GRADE-004-F006 | `change_reason` | `TEXT` | Yes | None | Override or edit reason |
| DB-GRADE-004-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit timestamp |

Indexes: `idx_grade_history_grade_record`, `idx_grade_history_created_at`.

### DB-GRADE-005 `published_results`
Purpose: Published result snapshot visible to students.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-005-F002 | `grade_record_id` | `UUID` | No | None | FK to `grade_records.id`, unique |
| DB-GRADE-005-F003 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-005-F004 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-005-F005 | `published_score` | `NUMERIC(8,2)` | No | None | Published score |
| DB-GRADE-005-F006 | `published_feedback` | `TEXT` | Yes | None | Feedback snapshot |
| DB-GRADE-005-F007 | `published_by_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-005-F008 | `published_at` | `TIMESTAMPTZ` | No | `now()` | Publication timestamp |

Indexes: unique `uq_published_results_grade_record`, `idx_published_results_student_course`.

### DB-GRADE-006 `certificate_eligibility`
Purpose: Certificate eligibility decisions calculated from course progress and published grades.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-006-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-006-F002 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-006-F003 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-006-F004 | `eligible` | `BOOLEAN` | No | `false` | Eligibility result |
| DB-GRADE-006-F005 | `reason` | `TEXT` | Yes | None | Ineligibility or eligibility reason |
| DB-GRADE-006-F006 | `evaluated_at` | `TIMESTAMPTZ` | No | `now()` | Evaluation timestamp |
| DB-GRADE-006-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-GRADE-006-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_certificate_eligibility_student_course`, `idx_certificate_eligibility_course_eligible`.

### DB-GRADE-007 `certificates`
Purpose: Issued course completion certificates.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-GRADE-007-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-GRADE-007-F002 | `certificate_eligibility_id` | `UUID` | No | None | FK to `certificate_eligibility.id`, unique |
| DB-GRADE-007-F003 | `student_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-007-F004 | `course_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-GRADE-007-F005 | `certificate_number` | `VARCHAR(80)` | No | None | Unique public certificate number |
| DB-GRADE-007-F006 | `certificate_asset_id` | `UUID` | Yes | None | Cross-service UUID reference to generated asset |
| DB-GRADE-007-F007 | `issued_at` | `TIMESTAMPTZ` | No | `now()` | Issue timestamp |
| DB-GRADE-007-F008 | `revoked_at` | `TIMESTAMPTZ` | Yes | None | Revocation timestamp |

Indexes: unique `uq_certificates_certificate_number`, unique `uq_certificates_eligibility`, `idx_certificates_student_course`.

## notification_db

Implementation note: `T-017` implements `DB-NOTIFY-001` through `DB-NOTIFY-004` for in-app notifications, delivery attempts, and channel preference placeholders.

### DB-NOTIFY-001 `notification_templates`
Purpose: Templates for in-app and future delivery channels.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-NOTIFY-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-NOTIFY-001-F002 | `event_type` | `VARCHAR(80)` | No | None | Triggering event |
| DB-NOTIFY-001-F003 | `channel` | `VARCHAR(32)` | No | `'in_app'` | Enum: `in_app`, `email`, `sms`, `push` |
| DB-NOTIFY-001-F004 | `subject_template` | `TEXT` | Yes | None | Subject format |
| DB-NOTIFY-001-F005 | `body_template` | `TEXT` | No | None | Body format |
| DB-NOTIFY-001-F006 | `status` | `VARCHAR(24)` | No | `'active'` | Enum: `active`, `inactive` |
| DB-NOTIFY-001-F007 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-NOTIFY-001-F008 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_notification_templates_event_channel`, `idx_notification_templates_status`.

### DB-NOTIFY-002 `notifications`
Purpose: User notification records.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-NOTIFY-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-NOTIFY-002-F002 | `recipient_profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-NOTIFY-002-F003 | `event_type` | `VARCHAR(80)` | No | None | Source event type |
| DB-NOTIFY-002-F004 | `title` | `VARCHAR(255)` | No | None | Notification title |
| DB-NOTIFY-002-F005 | `body` | `TEXT` | No | None | Notification body |
| DB-NOTIFY-002-F006 | `payload` | `JSONB` | No | `'{}'::jsonb` | Link and metadata |
| DB-NOTIFY-002-F007 | `read_at` | `TIMESTAMPTZ` | Yes | None | Read timestamp |
| DB-NOTIFY-002-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp |
| DB-NOTIFY-002-F009 | `deleted_at` | `TIMESTAMPTZ` | Yes | None | Soft delete |

Indexes: `idx_notifications_recipient_created_at`, `idx_notifications_recipient_unread`, `idx_notifications_event_type`.

### DB-NOTIFY-003 `delivery_attempts`
Purpose: Delivery state for in-app and future email, SMS, or push channels.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-NOTIFY-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-NOTIFY-003-F002 | `notification_id` | `UUID` | No | None | FK to `notifications.id` |
| DB-NOTIFY-003-F003 | `channel` | `VARCHAR(32)` | No | None | Enum: `in_app`, `email`, `sms`, `push` |
| DB-NOTIFY-003-F004 | `status` | `VARCHAR(24)` | No | `'queued'` | Enum: `queued`, `sent`, `failed`, `cancelled` |
| DB-NOTIFY-003-F005 | `provider_message_id` | `VARCHAR(255)` | Yes | None | Provider reference |
| DB-NOTIFY-003-F006 | `error_message` | `TEXT` | Yes | None | Failure reason |
| DB-NOTIFY-003-F007 | `attempted_at` | `TIMESTAMPTZ` | No | `now()` | Attempt timestamp |

Indexes: `idx_delivery_attempts_notification_id`, `idx_delivery_attempts_channel_status`.

### DB-NOTIFY-004 `user_notification_preferences`
Purpose: Per-user notification channel preferences.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-NOTIFY-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-NOTIFY-004-F002 | `profile_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-NOTIFY-004-F003 | `event_type` | `VARCHAR(80)` | No | None | Notification event type |
| DB-NOTIFY-004-F004 | `channel` | `VARCHAR(32)` | No | None | Enum: `in_app`, `email`, `sms`, `push` |
| DB-NOTIFY-004-F005 | `enabled` | `BOOLEAN` | No | `true` | Preference flag |
| DB-NOTIFY-004-F006 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |
| DB-NOTIFY-004-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: unique `uq_user_notification_preferences_profile_event_channel`, `idx_user_notification_preferences_profile`.

## analytics_db

Implemented designs: [DBD-011 Dashboards And Portals](db-design/DBD-011-dashboards-portals.md), [DBD-018 Search, Reporting, And Analytics](db-design/DBD-018-search-reporting-analytics.md).

### DB-ANALYTICS-001 `event_facts`
Purpose: Analytics event fact table populated from Kafka.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ANALYTICS-001-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ANALYTICS-001-F002 | `event_id` | `UUID` | No | None | Unique Kafka event ID |
| DB-ANALYTICS-001-F003 | `event_type` | `VARCHAR(80)` | No | None | Event type |
| DB-ANALYTICS-001-F004 | `producer_service` | `VARCHAR(80)` | No | None | Producing service |
| DB-ANALYTICS-001-F005 | `aggregate_id` | `UUID` | No | None | Aggregate UUID |
| DB-ANALYTICS-001-F006 | `institution_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ANALYTICS-001-F007 | `occurred_at` | `TIMESTAMPTZ` | No | None | Event timestamp |
| DB-ANALYTICS-001-F008 | `payload` | `JSONB` | No | None | Event payload |
| DB-ANALYTICS-001-F009 | `ingested_at` | `TIMESTAMPTZ` | No | `now()` | Ingestion timestamp |

Indexes: unique `event_id`, `idx_event_facts_type_time`, `idx_event_facts_inst_time`, `idx_event_facts_aggregate_id`.

### DB-ANALYTICS-002 `dashboard_aggregates`
Purpose: Cached dashboard metrics for students, instructors, and admins.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ANALYTICS-002-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ANALYTICS-002-F002 | `scope_type` | `VARCHAR(32)` | No | None | Enum: `student`, `instructor`, `institution`, `course`, `platform` |
| DB-ANALYTICS-002-F003 | `scope_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ANALYTICS-002-F004 | `metric_date` | `DATE` | No | None | Aggregate date |
| DB-ANALYTICS-002-F005 | `metrics` | `JSONB` | No | None | Dashboard metric values |
| DB-ANALYTICS-002-F006 | `computed_at` | `TIMESTAMPTZ` | No | `now()` | Computation timestamp |

Indexes: unique `uq_dash_aggr_scope_date`, `idx_dash_aggr_scope_type`.

### DB-ANALYTICS-003 `report_snapshots`
Purpose: Saved admin reports and large-scale reporting output.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ANALYTICS-003-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ANALYTICS-003-F002 | `institution_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ANALYTICS-003-F003 | `report_type` | `VARCHAR(80)` | No | None | Enum: `active_users`, `enrollments`, `completion_rates`, `assessment_results`, `system_usage`, `dashboard` |
| DB-ANALYTICS-003-F004 | `parameters` | `JSONB` | No | `'{}'::jsonb` | Report filters |
| DB-ANALYTICS-003-F005 | `result_payload` | `JSONB` | No | None | Report result snapshot |
| DB-ANALYTICS-003-F006 | `generated_by_profile_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ANALYTICS-003-F007 | `generated_at` | `TIMESTAMPTZ` | No | `now()` | Generation timestamp |

Indexes: `idx_report_snap_inst_type`, `idx_report_snap_generated`.

### DB-ANALYTICS-004 `usage_metrics`
Purpose: Time-bucketed platform usage metrics.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ANALYTICS-004-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ANALYTICS-004-F002 | `metric_name` | `VARCHAR(128)` | No | None | Metric key |
| DB-ANALYTICS-004-F003 | `metric_value` | `NUMERIC(18,4)` | No | None | Metric value |
| DB-ANALYTICS-004-F004 | `scope_type` | `VARCHAR(32)` | Yes | None | Optional scope |
| DB-ANALYTICS-004-F005 | `scope_id` | `UUID` | Yes | None | Optional scope UUID |
| DB-ANALYTICS-004-F006 | `bucket_start_at` | `TIMESTAMPTZ` | No | None | Time bucket start |
| DB-ANALYTICS-004-F007 | `bucket_end_at` | `TIMESTAMPTZ` | No | None | Time bucket end |
| DB-ANALYTICS-004-F008 | `created_at` | `TIMESTAMPTZ` | No | `now()` | Audit field |

Indexes: `idx_usage_metrics_name_bucket`, `idx_usage_metrics_scope_bucket`.

### DB-ANALYTICS-005 `search_index_records`
Purpose: Search index metadata for courses, users, enrollments, assessments, and submissions.

| Field ID | Field name | PostgreSQL datatype | Nullable | Default | Key and details |
| --- | --- | --- | --- | --- | --- |
| DB-ANALYTICS-005-F001 | `id` | `UUID` | No | `gen_random_uuid()` | PK |
| DB-ANALYTICS-005-F002 | `resource_type` | `VARCHAR(64)` | No | None | Enum: `course`, `user`, `enrollment`, `assessment`, `submission` |
| DB-ANALYTICS-005-F003 | `resource_id` | `UUID` | No | None | Cross-service UUID reference |
| DB-ANALYTICS-005-F004 | `institution_id` | `UUID` | Yes | None | Cross-service UUID reference |
| DB-ANALYTICS-005-F005 | `search_text` | `TEXT` | No | None | Searchable text |
| DB-ANALYTICS-005-F006 | `metadata` | `JSONB` | No | `'{}'::jsonb` | Search facets |
| DB-ANALYTICS-005-F007 | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Index update timestamp |

Indexes: unique `uq_search_index_resource`, `idx_search_index_resource_type`, `idx_search_index_institution`, GIN `gin_search_index_search_text`.

## Kafka Event Persistence Notes
Kafka topics are not SQL tables, but service tables that consume events must record `event_id`
values for idempotency. The implemented topic catalog, retry topics, DLQ topics, producer
behavior, consumer behavior, and lag commands are documented in
[EVT-020 Kafka Eventing](event-design/EVT-020-kafka-eventing.md). Event payloads use:

```json
{
  "event_id": "uuid",
  "event_type": "StudentEnrolled",
  "aggregate_id": "uuid",
  "producer_service": "enrollment-service",
  "timestamp": "2026-06-04T10:00:00Z",
  "version": 1,
  "correlation_id": "uuid",
  "payload": {}
}
```

## Schema Acceptance Checklist
- [ ] DB-AC-001 Every implemented model has a matching documented table ID.
- [ ] DB-AC-002 Every implemented field has a matching documented field ID or an approved documentation update.
- [ ] DB-AC-003 Cross-service UUID references are not implemented as database foreign keys.
- [ ] DB-AC-004 In-service relationships use database foreign keys and indexes.
- [ ] DB-AC-005 List API filter fields are indexed.
- [ ] DB-AC-006 Soft delete is implemented where the schema marks `deleted_at`.
- [ ] DB-AC-007 JSONB fields are not used for searchable data without a documented reason.
