# End-To-End Tests

These Selenium tests cover the browser journeys that the current frontend exposes, including
seeded demo credential login, dashboard, feature-route, logout, and optional admin create-user
smoke checks.

## Docker Compose Visible Browser

Start the app stack, seed demo data, then run the visible seeded-credential smoke:

```bash
docker compose up --build -d
scripts/seed-sample-data-compose.sh --reset-sample-data
docker compose --profile e2e up --abort-on-container-exit --exit-code-from selenium-e2e selenium-e2e
```

Open `http://127.0.0.1:7900` while the test is running to watch the browser through noVNC. The
default viewer password is `secret`, and the Selenium WebDriver endpoint is exposed on
`http://127.0.0.1:4444`.

To run the full e2e directory with the same visible browser, override the default pytest target:

```bash
SELENIUM_PYTEST_ARGS=tests/e2e docker compose --profile e2e up --abort-on-container-exit --exit-code-from selenium-e2e selenium-e2e
```

The Compose runner uses the seeded bot credentials by default:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `bot.admin@learngrid.local` | `BotAdmin123!` |
| Super Admin | `bot.superadmin@learngrid.local` | `BotSuperAdmin123!` |
| Instructor | `bot.instructor@learngrid.local` | `BotInstructor123!` |
| Student | `bot.student@learngrid.local` | `BotStudent123!` |

## Host Browser

Host runs can target a local browser driver or a remote Selenium server:

```bash
E2E_BASE_URL=http://127.0.0.1:5173
python -m pytest tests/e2e
```

Set `SELENIUM_REMOTE_URL`, `SELENIUM_BROWSER`, and `SELENIUM_HEADLESS=false` to drive an external
visible browser. Override `E2E_*_EMAIL` and `E2E_*_PASSWORD` only when testing non-demo users.

The admin create-user journey is mutating and remains opt-in with
`E2E_CREATE_USER_ENABLED=true`.
