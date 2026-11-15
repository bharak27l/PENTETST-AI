from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class ReportBuilder:
    def __init__(self, template_dir: str = "app/templates") -> None:
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def build(self, target: str, services: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
        summary = {
            "target": target,
            "total_services": len(services),
            "total_findings": len(findings),
            "status": "pending",
            "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        }

        return {
            "target": target,
            "services": services,
            "findings": findings,
            "summary": summary,
            "report_html": self.render_html(target, services, findings),
        }

    def render_html(self, target: str, services: list[dict[str, Any]], findings: list[dict[str, Any]]) -> str:
        template = self.env.get_template("report.html")
        return template.render(target=target, services=services, findings=findings)
