# PENTETST-AI

Safe, modular security testing and reporting for systems you are authorized to assess. Includes FastAPI, SQLite scan history, a React dashboard, PDF/DOCX/JSON reports, per-user authentication, and optional scheduled safe checks.

## Authentication setup

Configure a random signing secret and initial account. Keep these out of source control:

```bash
export AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export BOOTSTRAP_USERNAME="admin"
export BOOTSTRAP_PASSWORD="replace-with-a-unique-password-of-at-least-12-characters"
```

The bootstrap account is created on first startup if it does not exist. Self-registration is disabled. Tokens expire after one hour by default.

## Scheduled scans (opt-in)

Scheduling is disabled by default. To enable the in-process scheduler:

```bash
export SCHEDULER_ENABLED=true
```

Create and manage jobs through authenticated API endpoints:

- `POST /api/jobs` with `{"target":"https://example.com","interval_seconds":3600,"enabled":true}`
- `GET /api/jobs`
- `PATCH /api/jobs/{id}` with `{"enabled":false}` or `{"interval_seconds":7200}`
- `DELETE /api/jobs/{id}`

Intervals are restricted to 60–86400 seconds. Jobs are owned by the creating user and reloaded from SQLite when the service starts. Scheduled runs use the same safe metadata/header checks as manual scans; there is no exploitation or external scanner execution. For multiple web workers or production deployments, run a single scheduler process to avoid duplicate jobs.

## Run the backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs. For the React UI, run `cd frontend && npm install && npm run dev` in a second terminal.

## Reports and API

- `POST /api/auth/login` returns a bearer token
- `POST /api/scan` runs safe checks and persists the report
- `GET /api/scans` lists only the current user's reports
- `GET /api/scans/{id}/export/{pdf|docx|json}` downloads a report
- `GET /api/integrations` reports status

SQLite defaults to `./data/pentest_ai.db`; configure `SQLITE_DATABASE_PATH` to change it.

## Safety

- Only HTTP/HTTPS is supported; private/loopback IP literals are blocked by default.
- No exploitation, intrusive fuzzing, port scanning, or external scanner process is included.
- Nuclei and ZAP remain disabled placeholders; no integration launches them.
- Use only with explicit authorization. Built-in checks are limited and are not a substitute for a professional assessment.
