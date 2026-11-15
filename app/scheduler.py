from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.engine import SecurityEngine
from app.database import list_enabled_scan_jobs, save_scan, update_scan_job

_scheduler: BackgroundScheduler | None = None
_scheduler_lock = threading.Lock()


def _job_runner(job_id: str, owner_id: str, target: str) -> None:
    started_at = datetime.now(timezone.utc)
    try:
        report = SecurityEngine().run(target)
        save_scan(report, owner_id)
        next_run = datetime.now(timezone.utc) + timedelta(seconds=settings.scheduler_interval_seconds)
        update_scan_job(job_id, owner_id, status="active", last_run_at=started_at.isoformat(), next_run_at=next_run.isoformat())
    except Exception:
        next_run = datetime.now(timezone.utc) + timedelta(seconds=settings.scheduler_interval_seconds)
        update_scan_job(job_id, owner_id, status="error", last_run_at=started_at.isoformat(), next_run_at=next_run.isoformat())


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            return _scheduler
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.start()
        _scheduler = scheduler
        for job in list_enabled_scan_jobs():
            register_job(job["id"], job["owner_id"], job["target"], job["interval_seconds"])
        return scheduler


def stop_scheduler() -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=False)
        _scheduler = None


def register_job(job_id: str, owner_id: str, target: str, interval_seconds: int) -> None:
    if not settings.scheduler_enabled or _scheduler is None:
        return
    interval = max(60, min(int(interval_seconds), 86400))
    _scheduler.add_job(
        _job_runner,
        "interval",
        seconds=interval,
        id=f"scanjob-{job_id}",
        args=[job_id, owner_id, target],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def unregister_job(job_id: str) -> None:
    if _scheduler is None:
        return
    try:
        _scheduler.remove_job(f"scanjob-{job_id}")
    except Exception:
        pass
