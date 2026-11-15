from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

import httpx

from app.core.config import settings


class ReconModule:
    """Safe reconnaissance focused on target validation and metadata collection."""

    def run(self, target: str) -> list[dict]:
        parsed = self._normalize_target(target)
        host = parsed["hostname"]
        ip_list = self._resolve_host(host)

        response = self._fetch_metadata(parsed["url"])
        services = [{
            "target": target,
            "hostname": host,
            "resolved_ips": ip_list,
            "scheme": parsed["scheme"],
            "port": parsed["port"] or (443 if parsed["scheme"] == "https" else 80),
            "status_code": response.get("status_code"),
            "headers": response.get("headers", {}),
            "server": response.get("headers", {}).get("server"),
            "title": response.get("title"),
            "reachable": response.get("reachable", False),
            "notes": "Safe metadata collection only.",
        }]

        return services

    @staticmethod
    def _normalize_target(target: str) -> dict:
        if not target:
            raise ValueError("Target is required.")

        parsed = urlparse(target if target.startswith(("http://", "https://")) else f"https://{target}")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only http and https targets are supported.")
        if not parsed.hostname:
            raise ValueError("A valid hostname is required.")

        if not settings.allow_private_targets:
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                    raise ValueError("Private or loopback targets are not allowed by default.")
            except ValueError:
                pass

        return {
            "url": parsed.geturl(),
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port,
        }

    @staticmethod
    def _resolve_host(hostname: str) -> list[str]:
        try:
            import socket
            infos = socket.getaddrinfo(hostname, None)
            return sorted({item[4][0] for item in infos})
        except socket.gaierror:
            return []

    @staticmethod
    def _fetch_metadata(url: str) -> dict:
        try:
            with httpx.Client(timeout=settings.request_timeout, follow_redirects=True) as client:
                response = client.get(url)
                title_match = re.search(r"<title>(.*?)</title>", response.text, re.I | re.S)
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "title": title_match.group(1).strip() if title_match else None,
                    "reachable": True,
                }
        except Exception:
            return {"status_code": None, "headers": {}, "title": None, "reachable": False}
