# PENTETST-AI

Safe, modular security testing and reporting for systems you are authorized to assess. This MVP provides a FastAPI backend, persistent SQLite scan history, a React dashboard, and PDF/DOCX/JSON report exports.

## Included

- FastAPI API and modular orchestration
- Safe target metadata and security-header checks
- SQLite persistence for scan history and full reports
- React + Vite dashboard source (`frontend/`)
- PDF, DOCX, and JSON report exports
- Docker support for the backend
- Nuclei/ZAP integration status placeholders; external scanner execution is **not implemented** and no scanner process is launched

This application does not execute exploit payloads. Only use it against systems you own or are explicitly authorized to test. The built-in checks are limited and are not a substitute for a professional security assessment.

## Backend quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for API docs. The legacy HTML page is available at http://localhost:8000/.

## React dashboard

```bash
cd frontend
npm install
npm run dev
```

Vite runs at http://localhost:5173 and proxies `/api` requests to the backend at `http://localhost:8000`. Start the backend separately.

## API

- `POST /api/scan` with `{"target":"https://example.com"}` runs safe metadata/header checks and saves the report.
- `GET /api/scans` lists persisted scans (`limit` 1–100, `offset` >= 0).
- `GET /api/scans/{id}` returns a saved report.
- `GET /api/scans/{id}/export/pdf`, `/docx`, or `/json` downloads an export.
- `GET /api/integrations` reports the disabled external scanner adapters.

SQLite defaults to `./data/pentest_ai.db`; configure `SQLITE_DATABASE_PATH` to change it.

## Docker

```bash
docker compose up --build
```

The API listens on port 8000. Persist database data by mounting a host directory at `/app/data`.

## Safety

- HTTP/HTTPS only; private and loopback IP literals are blocked by default.
- No exploitation, intrusive fuzzing, port scanning, or external scanner execution is included.
- Nuclei/ZAP adapters are intentionally disabled placeholders, not executable integrations.
- Use only with explicit authorization and follow your organization's rules of engagement.

## License

MIT
