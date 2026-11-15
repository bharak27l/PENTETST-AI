from __future__ import annotations

from io import BytesIO
from typing import Any


class ReportExporter:
    """Create downloadable PDF and DOCX reports from persisted scan results."""

    def export(self, report: dict[str, Any], format: str) -> tuple[bytes, str, str]:
        normalized = format.lower()
        if normalized == "pdf":
            return self._pdf(report), "application/pdf", "pdf"
        if normalized == "docx":
            return self._docx(report), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"
        if normalized == "json":
            import json
            return json.dumps(report, indent=2, ensure_ascii=False).encode(), "application/json", "json"
        raise ValueError("Unsupported format. Choose pdf, docx, or json.")

    @staticmethod
    def _pdf(report: dict[str, Any]) -> bytes:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from xml.sax.saxutils import escape

        output = BytesIO()
        document = SimpleDocTemplate(output, pagesize=letter, title="PENTETST-AI Security Report")
        styles = getSampleStyleSheet()
        story = [Paragraph("PENTETST-AI Security Report", styles["Title"]), Spacer(1, 12)]
        story.append(Paragraph(f"Target: {escape(str(report.get('target', '')))}", styles["Normal"]))
        summary = report.get("summary", {})
        story.append(Paragraph(f"Findings: {summary.get('total_findings', 0)}", styles["Normal"]))
        story.append(Spacer(1, 12))
        findings = report.get("prioritized_findings", report.get("findings", []))
        if findings:
            data = [["Severity", "Finding", "Recommendation"]]
            for finding in findings:
                data.append([
                    escape(str(finding.get("severity", "info")).upper()),
                    escape(str(finding.get("title", "Untitled"))),
                    escape(str(finding.get("recommendation", ""))),
                ])
            table = Table(data, repeatRows=1, colWidths=[72, 180, 240])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No findings were detected by the configured safe checks.", styles["Normal"]))
        document.build(story)
        return output.getvalue()

    @staticmethod
    def _docx(report: dict[str, Any]) -> bytes:
        from docx import Document

        document = Document()
        document.add_heading("PENTETST-AI Security Report", 0)
        document.add_paragraph(f"Target: {report.get('target', '')}")
        summary = report.get("summary", {})
        document.add_paragraph(f"Findings: {summary.get('total_findings', 0)}")
        findings = report.get("prioritized_findings", report.get("findings", []))
        if findings:
            table = document.add_table(rows=1, cols=3)
            table.style = "Light Shading Accent 1"
            for cell, label in zip(table.rows[0].cells, ("Severity", "Finding", "Recommendation")):
                cell.text = label
            for finding in findings:
                cells = table.add_row().cells
                cells[0].text = str(finding.get("severity", "info")).upper()
                cells[1].text = str(finding.get("title", "Untitled"))
                cells[2].text = str(finding.get("recommendation", ""))
        else:
            document.add_paragraph("No findings were detected by the configured safe checks.")
        output = BytesIO()
        document.save(output)
        return output.getvalue()
