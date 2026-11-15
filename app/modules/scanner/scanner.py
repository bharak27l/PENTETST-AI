from __future__ import annotations

from typing import Any


class ScannerModule:
    """Safe, read-only checks for common security misconfigurations."""

    def run(self, target: str, services: list[dict[str, Any]]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        service = services[0]
        headers = service.get("headers", {})

        checks = {
            "missing_hsts": not headers.get("strict-transport-security"),
            "missing_xframe": not headers.get("x-frame-options"),
            "missing_csp": not headers.get("content-security-policy"),
            "missing_xcontent": not headers.get("x-content-type-options"),
            "server_header_exposure": bool(headers.get("server")),
        }

        for key, enabled in checks.items():
            if not enabled:
                continue

            finding = self._build_finding(key, target, headers)
            if finding:
                findings.append(finding)

        if service.get("status_code") and service["status_code"] >= 500:
            findings.append({
                "id": "server-error-state",
                "title": "Server error state detected",
                "severity": "medium",
                "confidence": 0.8,
                "category": "availability",
                "target": target,
                "evidence": [f"HTTP {service['status_code']} returned by target."],
                "recommendation": "Review application logs and deployment health checks.",
            })

        return findings

    @staticmethod
    def _build_finding(key: str, target: str, headers: dict) -> dict | None:
        mapping = {
            "missing_hsts": {
                "title": "HTTP Strict Transport Security is missing",
                "severity": "medium",
                "confidence": 0.85,
                "category": "transport_security",
                "recommendation": "Enable HSTS for all authenticated and high-risk pages via HTTPS.",
            },
            "missing_xframe": {
                "title": "Clickjacking protection is missing",
                "severity": "medium",
                "confidence": 0.8,
                "category": "security_headers",
                "recommendation": "Add X-Frame-Options or Content-Security-Policy frame-ancestors.",
            },
            "missing_csp": {
                "title": "Content Security Policy is missing",
                "severity": "medium",
                "confidence": 0.75,
                "category": "security_headers",
                "recommendation": "Define a restrictive CSP to reduce XSS exposure.",
            },
            "missing_xcontent": {
                "title": "X-Content-Type-Options is missing",
                "severity": "low",
                "confidence": 0.7,
                "category": "security_headers",
                "recommendation": "Set X-Content-Type-Options: nosniff.",
            },
            "server_header_exposure": {
                "title": "Server header reveals implementation details",
                "severity": "low",
                "confidence": 0.6,
                "category": "information_disclosure",
                "recommendation": "Reduce or normalize server banner information when possible.",
            },
        }

        detail = mapping.get(key)
        if not detail:
            return None

        evidence = [
            f"Missing security header or exposed metadata on {target}.",
            f"Observed headers: {', '.join(sorted(headers.keys())) or 'none'}",
        ]
        return {
            "id": key,
            "title": detail["title"],
            "severity": detail["severity"],
            "confidence": detail["confidence"],
            "category": detail["category"],
            "target": target,
            "evidence": evidence,
            "recommendation": detail["recommendation"],
        }
