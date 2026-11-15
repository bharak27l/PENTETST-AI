from __future__ import annotations

import os
from pathlib import Path


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scan_endpoint_rejects_invalid_target():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/scan", json={"target": "ftp://example.com"})
    assert response.status_code == 400
