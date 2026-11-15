from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.ai_analyzer import AIAnalyzer
from app.modules.recon.recon import ReconModule
from app.modules.reporting.report_builder import ReportBuilder
from app.modules.scanner.scanner import ScannerModule


@dataclass
class ScanContext:
    target: str
    discovered_services: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    report: dict[str, Any] | None = None


class SecurityEngine:
    def __init__(self) -> None:
        self.recon = ReconModule()
        self.scanner = ScannerModule()
        self.ai = AIAnalyzer()
        self.report_builder = ReportBuilder()

    def run(self, target: str) -> dict[str, Any]:
        ctx = ScanContext(target=target)
        ctx.discovered_services = self.recon.run(target)
        ctx.findings = self.scanner.run(target, ctx.discovered_services)
        ctx.report = self.report_builder.build(target, ctx.discovered_services, ctx.findings)

        prioritized = self.ai.analyze(ctx.findings)
        ctx.report["summary"] = prioritized["summary"]
        ctx.report["prioritized_findings"] = prioritized["findings"]
        ctx.report["evidence"] = prioritized["evidence"]
        ctx.report["status"] = "completed"
        return ctx.report
