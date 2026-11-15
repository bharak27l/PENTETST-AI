# PENTETST-AI

Safe, modular security testing and reporting for systems you are authorized to assess.

## Scheduled scans

This release adds optional scheduled scan jobs behind a strict opt-in configuration flag:

```bash
export SCHEDULER_ENABLED=true
export SCHEDULER_INTERVAL_SECONDS=3600
```

When enabled, a logged-in user can create scan jobs through the API and receive periodic runs for the configured target. Jobs remain user-specific and are stored in SQLite. The scheduler is intentionally limited to safe, authorized scanning workflows and does not execute exploit payloads.

## Authentication

Before starting the service, configure:

```bash
export AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export BOOTSTRAP_USERNAME="admin"
export BOOTSTRAP_PASSWORD="replace-with-a-unique-password-of-at-least-12-characters"
```

## Run the backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Then use the API docs at http://localhost:8000/docs.

## API

- `POST /api/auth/login`
- `POST /api/scan`
- `GET /api/scans`
- `GET /api/scans/{id}/export/{pdf|docx|json}`
- `POST /api/jobs` to create a scheduled scan job
- `GET /api/jobs` to list scheduled jobs
- `DELETE /api/jobs/{id}` to remove a job

## Safety

- HTTP/HTTPS only
- Private/loopback targets are blocked by default
- No exploit execution or destructive testing is included
- External scanner integrations remain intentionally disabled placeholders
