# End-To-End Tests

These Selenium tests cover the browser journeys that the current frontend exposes and skip cleanly
unless a target app and credentials are configured.

Required for role dashboard/logout smoke:

```bash
E2E_BASE_URL=http://127.0.0.1:5173
E2E_STUDENT_EMAIL=student@example.com
E2E_STUDENT_PASSWORD=...
E2E_INSTRUCTOR_EMAIL=instructor@example.com
E2E_INSTRUCTOR_PASSWORD=...
E2E_ADMIN_EMAIL=admin@example.com
E2E_ADMIN_PASSWORD=...
python -m pytest tests/e2e
```

The admin create-user journey is mutating and remains opt-in with
`E2E_CREATE_USER_ENABLED=true`.

