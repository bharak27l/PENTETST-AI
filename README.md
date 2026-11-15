# PENTETST-AI

Safe, modular security testing and reporting for systems you are authorized to assess. Includes a FastAPI backend, SQLite persistence, React dashboard, authenticated user management, PDF/DOCX/JSON exports, and optional scheduled safe checks.

## Security model

- HTTP/HTTPS only; private and loopback IP addresses are blocked by default.
- No exploitation, intrusive fuzzing, or destructive testing is included.
- Nuclei and ZAP remain opt-in placeholders and are not launched automatically.
- Use only against systems you own or are explicitly authorized to test.

## Authentication

Configure a random signing secret and a bootstrap administrator before starting the app:

```bash
export AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export BOOTSTRAP_USERNAME="admin"
export BOOTSTRAP_PASSWORD="replace-with-a-unique-password-of-at-least-12-characters"
```

The bootstrap account is created automatically if it does not exist. Keep `AUTH_SECRET` stable; changing it invalidates existing tokens. Tokens expire after one hour by default.

## Scheduled scans

Scheduling is disabled by default. Enable it explicitly:

```bash
export SCHEDULER_ENABLED=true
```

Users can then create safe recurring jobs through the authenticated API endpoints:

- `POST /api/jobs` with `{"target":"https://example.com","interval_seconds":3600,"enabled":true}`
- `GET /api/jobs`
- `PATCH /api/jobs/{id}`
- `DELETE /api/jobs/{id}`

Job intervals are restricted to 60–86400 seconds. Jobs are user-scoped and persisted in SQLite. A scheduler process is started when enabled and is stopped when the app exits.

## Admin users

The bootstrap admin account can create additional users through the admin API:

- `GET /api/admin/users`
- `POST /api/admin/users` with `{"username":"analyst","password":"a-strong-password","role":"user"}`

The default bootstrap user is always created as `admin` if a password is supplied.

## Run the backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for Swagger. For the React dashboard, run:

```bash
cd frontend
npm install
npm run dev
```

## Reports

- `GET /api/scans/{id}/export/pdf`
- `GET /api/scans/{id}/export/docx`
- `GET /api/scans/{id}/export/json`

## SQLite

SQLite defaults to `./data/pentest_ai.db`; override with `SQLITE_DATABASE_PATH` when needed.

## Safety

Built-in checks are status/header-driven and are intended for authorized, non-destructive validation only. They do not provide a complete pentest workflow or replace professional assessments.
