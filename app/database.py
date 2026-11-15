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
                report_json TEXT NOT NULL,
                owner_id TEXT
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scan_jobs (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                target TEXT NOT NULL,
                interval_seconds INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_run_at TEXT,
                next_run_at TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scans_owner_created ON scans(owner_id, created_at DESC)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_owner ON scan_jobs(owner_id, enabled)")


def create_user(username: str, password_hash: str) -> dict[str, str]:
    initialize_database()
    user_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, created_at),
        )
        row = connection.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
    return {"id": row["id"], "username": row["username"]}


def get_user_by_username(username: str) -> dict[str, str] | None:
    initialize_database()
    with _connect() as connection:
        row = connection.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def save_scan(report: dict[str, Any], owner_id: str) -> dict[str, Any]:
    initialize_database()
    scan_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    report = {**report, "id": scan_id, "created_at": created_at}
    with _connect() as connection:
        connection.execute(
            "INSERT INTO scans (id, target, status, created_at, report_json, owner_id) VALUES (?, ?, ?, ?, ?, ?)",
            (scan_id, str(report.get("target", "")), str(report.get("status", "completed")), created_at,
             json.dumps(report, ensure_ascii=False), owner_id),
        )
    return report


def list_scans(owner_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, target, status, created_at, report_json FROM scans WHERE owner_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (owner_id, limit, offset),
        ).fetchall()
    results = []
    for row in rows:
        report = json.loads(row["report_json"])
        results.append({"id": row["id"], "target": row["target"], "status": row["status"], "created_at": row["created_at"], "summary": report.get("summary", {})})
    return results


def get_scan(scan_id: str, owner_id: str) -> dict[str, Any] | None:
    initialize_database()
    with _connect() as connection:
        row = connection.execute("SELECT report_json FROM scans WHERE id = ? AND owner_id = ?", (scan_id, owner_id)).fetchone()
    return json.loads(row["report_json"]) if row else None


def create_scan_job(owner_id: str, target: str, interval_seconds: int, enabled: bool = True) -> dict[str, Any]:
    initialize_database()
    job_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    next_run_at = created_at if enabled else None
    with _connect() as connection:
        connection.execute(
            "INSERT INTO scan_jobs (id, owner_id, target, interval_seconds, enabled, last_run_at, next_run_at, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, owner_id, target, int(interval_seconds), int(enabled), None, next_run_at, created_at, "active"),
        )
    return {"id": job_id, "owner_id": owner_id, "target": target, "interval_seconds": int(interval_seconds), "enabled": bool(enabled), "next_run_at": next_run_at, "created_at": created_at, "status": "active"}


def list_scan_jobs(owner_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, owner_id, target, interval_seconds, enabled, last_run_at, next_run_at, created_at, status FROM scan_jobs WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "owner_id": row["owner_id"],
            "target": row["target"],
            "interval_seconds": row["interval_seconds"],
            "enabled": bool(row["enabled"]),
            "last_run_at": row["last_run_at"],
            "next_run_at": row["next_run_at"],
            "created_at": row["created_at"],
            "status": row["status"],
        } for row in rows
    ]


def get_scan_job(job_id: str, owner_id: str) -> dict[str, Any] | None:
    initialize_database()
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, owner_id, target, interval_seconds, enabled, last_run_at, next_run_at, created_at, status FROM scan_jobs WHERE id = ? AND owner_id = ?",
            (job_id, owner_id),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "target": row["target"],
        "interval_seconds": row["interval_seconds"],
        "enabled": bool(row["enabled"]),
        "last_run_at": row["last_run_at"],
        "next_run_at": row["next_run_at"],
        "created_at": row["created_at"],
        "status": row["status"],
    }


def update_scan_job(job_id: str, owner_id: str, *, enabled: bool | None = None, interval_seconds: int | None = None, status: str | None = None, last_run_at: str | None = None, next_run_at: str | None = None) -> dict[str, Any] | None:
    current = get_scan_job(job_id, owner_id)
    if current is None:
        return None
    if enabled is not None:
        current["enabled"] = bool(enabled)
    if interval_seconds is not None:
        current["interval_seconds"] = int(interval_seconds)
    if status is not None:
        current["status"] = status
    if last_run_at is not None:
        current["last_run_at"] = last_run_at
    if next_run_at is not None:
        current["next_run_at"] = next_run_at
    with _connect() as connection:
        connection.execute(
            "UPDATE scan_jobs SET enabled = ?, interval_seconds = ?, status = ?, last_run_at = ?, next_run_at = ? WHERE id = ? AND owner_id = ?",
            (int(current["enabled"]), current["interval_seconds"], current["status"], current["last_run_at"], current["next_run_at"], job_id, owner_id),
        )
    return current


def delete_scan_job(job_id: str, owner_id: str) -> bool:
    initialize_database()
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM scan_jobs WHERE id = ? AND owner_id = ?", (job_id, owner_id))
    return cursor.rowcount > 0
