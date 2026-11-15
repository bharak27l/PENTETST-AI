from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.auth import create_access_token, get_current_user, require_admin, verify_password
from app.core.config import settings
from app.core.engine import SecurityEngine
from app.database import (
    create_job_run,
    create_scan_job,
    create_user,
    delete_scan_job,
    get_scan,
    get_scan_job,
    get_user_by_username,
    list_job_runs,
    list_scan_jobs,
    list_scans,
    list_users,
    save_scan,
    update_scan_job,
)
from app.modules.reporting.exporters import ReportExporter

router = APIRouter()
engine = SecurityEngine()
exporter = ReportExporter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=1024)


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=12, max_length=1024)
    role: str = Field(default="user", pattern="^(admin|user)$")


class ScanRequest(BaseModel):
    target: str = Field(..., description="Authorized target URL to assess safely.")


class JobRequest(BaseModel):
    target: str = Field(..., description="Authorized target URL for a scheduled scan.")
    interval_seconds: int = Field(default=3600, ge=60, le=86400)
    enabled: bool = True


class JobUpdateRequest(BaseModel):
    enabled: bool | None = None
    interval_seconds: int | None = Field(default=None, ge=60, le=86400)


@router.post("/auth/login")
def login(payload: LoginRequest):
    user = get_user_by_username(payload.username)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "expires_in": settings.auth_token_ttl_seconds,
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
    }


@router.get("/auth/me")
def current_user(user: dict = Depends(get_current_user)):
    return user


@router.get("/admin/users")
def admin_users(user: dict = Depends(require_admin)):
    return {"items": list_users(), "current_user": user}


@router.post("/admin/users")
def create_admin_user(payload: UserCreateRequest, user: dict = Depends(require_admin)):
    existing = get_user_by_username(payload.username)
    if existing is not None:
        raise HTTPException(status_code=409, detail="User already exists.")
    created = create_user(payload.username, __import__("hashlib").sha256(payload.password.encode()).hexdigest(), role=payload.role)
    return {"user": created, "created_by": user["username"]}


@router.post("/scan")
def scan_target(payload: ScanRequest, user: dict = Depends(get_current_user)):
    try:
        return save_scan(engine.run(payload.target), user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/scans")
def scan_history(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return {"items": list_scans(user["id"], limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/scans/{scan_id}")
def scan_detail(scan_id: str, user: dict = Depends(get_current_user)):
    report = get_scan(scan_id, user["id"])
    if report is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return report


@router.get("/scans/{scan_id}/export/{format}")
def export_report(scan_id: str, format: str, user: dict = Depends(get_current_user)):
    report = get_scan(scan_id, user["id"])
    if report is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    try:
        content, media_type, extension = exporter.export(report, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="pentest-report-{scan_id}.{extension}"'},
    )


@router.get("/jobs")
def list_jobs(user: dict = Depends(get_current_user)):
    return {"items": list_scan_jobs(user["id"]) }


@router.get("/jobs/{job_id}/runs")
def list_job_runs_endpoint(job_id: str, user: dict = Depends(get_current_user)):
    return {"items": list_job_runs(job_id, user["id"]) }


@router.post("/jobs")
def create_job(payload: JobRequest, user: dict = Depends(get_current_user)):
    if not settings.scheduler_enabled:
        raise HTTPException(status_code=400, detail="Scheduled scans are disabled. Set SCHEDULER_ENABLED=true to enable them.")
    job = create_scan_job(user["id"], payload.target, payload.interval_seconds, payload.enabled)
    if job["enabled"]:
        from app.scheduler import register_job

        register_job(job["id"], user["id"], job["target"], job["interval_seconds"])
    return job


@router.patch("/jobs/{job_id}")
def edit_job(job_id: str, payload: JobUpdateRequest, user: dict = Depends(get_current_user)):
    if not settings.scheduler_enabled:
        raise HTTPException(status_code=400, detail="Scheduled scans are disabled.")
    job = update_scan_job(job_id, user["id"], enabled=payload.enabled, interval_seconds=payload.interval_seconds)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    from app.scheduler import register_job, unregister_job

    if job["enabled"]:
        register_job(job["id"], user["id"], job["target"], job["interval_seconds"])
    else:
        unregister_job(job["id"])
    return job


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, user: dict = Depends(get_current_user)):
    if not delete_scan_job(job_id, user["id"]):
        raise HTTPException(status_code=404, detail="Job not found")
    from app.scheduler import unregister_job

    unregister_job(job_id)
    return {"status": "deleted"}


@router.get("/integrations")
def integration_status(user: dict = Depends(get_current_user)):
    return {
        "nuclei": {"enabled": bool(settings.nuclei_enabled), "available": bool(settings.nuclei_enabled), "mode": "enabled" if settings.nuclei_enabled else "disabled"},
        "zap": {"enabled": bool(settings.zap_enabled), "available": bool(settings.zap_enabled), "mode": "enabled" if settings.zap_enabled else "disabled"},
        "scheduler": {"enabled": bool(settings.scheduler_enabled), "mode": "enabled" if settings.scheduler_enabled else "disabled"},
        "message": "External scanner execution remains opt-in only and is not automatically launched.",
    }


@router.get("/health")
def api_health():
    return {"status": "ok", "service": "pentest-ai"}
