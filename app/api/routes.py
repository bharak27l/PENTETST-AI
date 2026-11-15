from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.engine import SecurityEngine

router = APIRouter()
engine = SecurityEngine()


class ScanRequest(BaseModel):
    target: str = Field(..., description="Target URL to validate and assess safely.")


class ScanResponse(BaseModel):
    target: str
    status: str
    summary: dict
    prioritized_findings: list[dict]
    evidence: list[dict]
    report_html: str


@router.post("/scan", response_model=ScanResponse)
async def scan_target(payload: ScanRequest):
    try:
        report = engine.run(payload.target)
        return {
            "target": payload.target,
            "status": report.get("status", "completed"),
            "summary": report.get("summary", {}),
            "prioritized_findings": report.get("prioritized_findings", []),
            "evidence": report.get("evidence", []),
            "report_html": report.get("report_html", ""),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/health")
async def api_health():
    return {"status": "ok", "service": "pentest-ai"}
