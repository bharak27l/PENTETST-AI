from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.engine import SecurityEngine
from app.database import get_scan, list_scans, save_scan
from app.modules.reporting.exporters import ReportExporter

router = APIRouter()
engine = SecurityEngine()
exporter = ReportExporter()


class ScanRequest(BaseModel):
    target: str = Field(..., description="Authorized target URL to assess safely.")


@router.post("/scan")
def scan_target(payload: ScanRequest):
    try:
        report = engine.run(payload.target)
        return save_scan(report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/scans")
def scan_history(limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    return {"items": list_scans(limit=limit, offset=offset), "limit": limit, "offset": offset}


@router.get("/scans/{scan_id}")
def scan_detail(scan_id: str):
    report = get_scan(scan_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return report


@router.get("/scans/{scan_id}/export/{format}")
def export_report(scan_id: str, format: str):
    report = get_scan(scan_id)
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


@router.get("/integrations")
def integration_status():
    # Scanner processes are deliberately not invoked by this MVP. These adapters
    # remain disabled until a separately reviewed, explicitly authorized workflow exists.
    return {
        "nuclei": {"enabled": False, "available": False, "mode": "disabled"},
        "zap": {"enabled": False, "available": False, "mode": "disabled"},
        "message": "External scanner execution is not implemented; no scanner is launched.",
    }


@router.get("/health")
def api_health():
    return {"status": "ok", "service": "pentest-ai"}
