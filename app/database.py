from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings


def _connect() -> sqlite3.Connection:
    path = Path(settings.sqlite_database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                report_json TEXT NOT NULL
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC)")


def save_scan(report: dict[str, Any]) -> dict[str, Any]:
    initialize_database()
    scan_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    report = {**report, "id": scan_id, "created_at": created_at}
    with _connect() as connection:
        connection.execute(
            "INSERT INTO scans (id, target, status, created_at, report_json) VALUES (?, ?, ?, ?, ?)",
            (scan_id, str(report.get("target", "")), str(report.get("status", "completed")), created_at,
             json.dumps(report, ensure_ascii=False)),
        )
    return report


def list_scans(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, target, status, created_at, report_json FROM scans ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    results = []
    for row in rows:
        report = json.loads(row["report_json"])
        results.append({
            "id": row["id"], "target": row["target"], "status": row["status"],
            "created_at": row["created_at"], "summary": report.get("summary", {}),
        })
    return results


def get_scan(scan_id: str) -> dict[str, Any] | None:
    initialize_database()
    with _connect() as connection:
        row = connection.execute("SELECT report_json FROM scans WHERE id = ?", (scan_id,)).fetchone()
    return json.loads(row["report_json"]) if row else None
