from __future__ import annotations

from typing import Any


class AIAnalyzer:
    """Heuristic priority engine. Can be swapped for an LLM provider later."""

    def analyze(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(
            findings,
            key=lambda item: (
                self._severity_score(item.get("severity", "info")),
                item.get("confidence", 0),
            ),
            reverse=True,
        )

        summary = {
            "total_findings": len(findings),
            "high": sum(1 for f in findings if f.get("severity") == "high"),
            "medium": sum(1 for f in findings if f.get("severity") == "medium"),
            "low": sum(1 for f in findings if f.get("severity") == "low"),
        }

        return {
            "summary": summary,
            "findings": ordered,
            "evidence": [
                {"id": item.get("id"), "evidence": item.get("evidence", [])}
                for item in ordered
            ],
        }

    @staticmethod
    def _severity_score(severity: str) -> int:
        mapping = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        return mapping.get(severity.lower(), 0)
