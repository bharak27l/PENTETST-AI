# PENTETST-AI

PENTETST-AI is a safe, modular application framework for orchestrating reconnaissance, scanning, AI-assisted triage, and report generation against authorized targets only.

This repository contains an MVP implementation designed around the architecture you described:

- Core orchestration engine
- Reconnaissance and target validation
- Safe vulnerability scanning heuristics
- AI prioritization layer
- Report generation
- Dashboard and API interface
- Dockerized local setup

Important: This project is intentionally limited to safe, read-only/authorized checks. It does not perform destructive exploitation or unauthorized live attacks.

## Features

- FastAPI backend with a scan API
- Reusable modular architecture
- Safe HTTP target validation and header analysis
- AI prioritization layer with a fallback heuristic engine
- HTML report generation and JSON report output
- Local SQLite-backed report storage
- Docker support
- CLI for local execution

## Quick start

### Local Python

1. Create a virtual environment
2. Install dependencies
3. Start the API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
python -m uvicorn app.main:app --reload
```

Then open:

- http://localhost:8000/
- http://localhost:8000/docs

### Docker

```bash
docker compose up --build
```

## API usage

### Submit a scan

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'
```

### CLI

```bash
pentest-ai scan https://example.com
```

## Safety guardrails

- Only HTTP/HTTPS targets are accepted.
- Private/internal IP targets are blocked by default.
- No exploitation payloads are executed.
- Reporting is based on safe validation and heuristic checks.
- Use only against systems you are explicitly authorized to test.

## Project structure

```text
app/
  api/
  core/
  modules/
  templates/
  database.py
Dockerfile
docker-compose.yml
pyproject.toml
README.md
```

## License

MIT
