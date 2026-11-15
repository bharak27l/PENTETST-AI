# PENTETST-AI

Safe, modular security testing and reporting for systems you are authorized to assess. Includes FastAPI, SQLite persistence, React dashboard, authenticated admin/user accounts, report exports, and optional scheduled safe checks.

## Security and scanner status

- HTTP/HTTPS only; private and loopback IP literals are blocked by default.
- No exploitation, intrusive fuzzing, or destructive testing is included.
- Nuclei/ZAP execution adapters are **not implemented**. They are reported unavailable and no scanner process is launched.
- Use only against systems you own or are explicitly authorized to test.

## Authentication

Configure a random signing secret and bootstrap administrator before starting:

```bash
export AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export BOOTSTRAP_USERNAME="admin"
export BOOTSTRAP_PASSWORD="replace-with-a-unique-password-of-at-least-12-characters"
```

Keep secrets out of source control. The bootstrap account is created if it does not exist. Accounts can be provisioned by an admin through `/api/admin/users`; self-registration is disabled.

## Scheduled scans

Scheduling is disabled by default; enable explicitly with `SCHEDULER_ENABLED=true`. Jobs require auth, are scoped to their creator, and can be created/listed/paused/resumed/deleted in the React dashboard or through `/api/jobs`. Intervals are constrained to 60–86400 seconds. The API exposes execution history at `GET /api/jobs/{job_id}/runs`. Runs only use safe metadata/header checks. Run one scheduler-enabled app process to avoid duplicate schedules.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Backend docs are at http://localhost:8000/docs. Start the dashboard in another terminal with `cd frontend && npm install && npm run dev`.

## API

- `POST /api/auth/login` and `GET /api/auth/me`
- `POST /api/scan`, `GET /api/scans`, and `GET /api/scans/{id}`
- `GET /api/scans/{id}/export/{pdf|docx|json}`
- `GET/POST /api/jobs`, `PATCH/DELETE /api/jobs/{id}`, `GET /api/jobs/{id}/runs`
- `GET/POST /api/admin/users` (admin only)

SQLite defaults to `./data/pentest_ai.db`; set `SQLITE_DATABASE_PATH` to change it. Existing databases receive additive schema migration for the user role and scan owner columns.

## License

MIT
