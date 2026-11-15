# PENTETST-AI

Safe, modular security testing and reporting for systems you are authorized to assess. Includes FastAPI, SQLite scan history, React dashboard, PDF/DOCX/JSON reports, and per-user authentication with isolated scan history.

## Configure authentication first

Authentication is required for scans, history, and reports. Configure a long random signing secret and an initial administrator account through environment variables; do not commit secrets:

```bash
export AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export BOOTSTRAP_USERNAME="admin"
export BOOTSTRAP_PASSWORD="replace-with-a-unique-password-of-at-least-12-characters"
```

On first startup the bootstrap user is created if it does not already exist. User self-registration is intentionally disabled. Store `AUTH_SECRET` securely and keep it stable across restarts; changing it invalidates issued tokens. Tokens expire after one hour by default (`AUTH_TOKEN_TTL_SECONDS`).

## Run the backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs. The React dashboard is at http://localhost:5173 when running Vite:

```bash
cd frontend
npm install
npm run dev
```

## API

- `POST /api/auth/login` with username/password returns a bearer token.
- `GET /api/auth/me` returns the authenticated user.
- `POST /api/scan` requires a bearer token and stores the report under that user.
- `GET /api/scans` lists only the authenticated user's scans.
- `GET /api/scans/{id}` and `/export/{pdf|docx|json}` only expose the owner's report.
- `GET /api/integrations` reports disabled scanner placeholders.

SQLite defaults to `./data/pentest_ai.db` (`SQLITE_DATABASE_PATH`). Existing scan rows without an owner remain inaccessible, rather than being exposed to newly created accounts.

## Safety

- HTTP/HTTPS only; private and loopback IP literals are blocked by default.
- No exploitation, intrusive fuzzing, port scanning, or external scanner execution is included.
- Nuclei/ZAP integrations remain disabled placeholders; no external scanner is launched.
- Use only with explicit authorization. Built-in checks are limited and not a substitute for a professional assessment.

## Docker

Set `AUTH_SECRET`, `BOOTSTRAP_USERNAME`, and `BOOTSTRAP_PASSWORD` in the environment, then run `docker compose up --build`. Keep secrets out of source control and use a persistent `/app/data` volume.
