# API-004 User Profile Management

Related task: [T-004 User And Profile Management](../tasks/T-004-user-profile-management.md)  
Related spec: [SPEC-004 User Profile Management](../specs/004-user-profile-management.md)  
Related database design: [DBD-004](../db-design/DBD-004-user-profile-management.md)

## Design Summary
T-004 implemented user and profile workflows across `auth-service` and `user-service`. Auth-service owns account lifecycle APIs. User-service owns profile APIs and coordinates auth account creation, update, and deactivation through auth-service.

## Auth Account Endpoints
| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/accounts/` | `profile.manage` | Create account, credential, and optional initial role assignment |
| `PATCH` | `/api/auth/accounts/<uuid>/` | `profile.manage` | Update account email, phone, or status |
| `POST` | `/api/auth/accounts/<uuid>/deactivate/` | `profile.manage` | Deactivate account and revoke active tokens |

Account create accepts `email`, optional `phone`, `temporary_password`, optional `role_code`, `scope_type`, and optional `scope_id`. Temporary passwords are never returned after creation.

## User Profile Endpoints
| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/users/profiles/` | `profile.manage` | Create auth account, base profile, and role-specific profile |
| `GET` | `/api/users/profiles/` | `profile.view` | Search profiles with pagination and filters |
| `GET` | `/api/users/profiles/<uuid>/` | `profile.view` | Return profile detail with role-specific data |
| `PATCH` | `/api/users/profiles/<uuid>/` | `profile.manage` | Update profile and optional auth email/phone |
| `POST` | `/api/users/profiles/<uuid>/deactivate/` | `profile.manage` | Deactivate profile and auth account together |
| `POST` | `/api/users/import-jobs/` | `profile.manage` | Return `501 not_implemented` placeholder for future bulk imports |

## Search And Response Shape
Profile search supports `institution_id`, `q`, `profile_type`, `status`, `department_id`, `batch_id`, `sort`, `page`, and `page_size`.

Search returns a DRF paginated response:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": []
}
```

Profile responses include base profile fields, `auth_account_id`, `institution_id`, `profile_type`, and `role_profile`.

## Auth And Failure Behavior
- Requests with `institution_id` authorize against institution scope.
- Requests without `institution_id` authorize against platform scope.
- Platform account operations require Super Admin through auth-service.
- If local profile creation fails after auth account creation, user-service calls auth-service deactivation as compensation.
- Auth-service failures during create, update, or deactivate return a controlled API error.

## Verification
T-004 tests cover account creation/update/deactivation, role assignment during account creation, unauthorized account creation denial, profile creation for student/instructor/admin, profile update, profile deactivation, paginated scoped search, cross-institution denial, import placeholder response, auth-service failure handling, and compensation after local create failure.
