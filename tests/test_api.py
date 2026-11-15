import pytest
from fastapi.testclient import TestClient

from app.database import get_scan
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_scan_endpoint_rejects_invalid_target():
    response = client.post('/api/scan', json={'target': 'ftp://example.com'})
    assert response.status_code == 400


def test_export_rejects_unsupported_format():
    response = client.get('/api/scans/missing/export/exe')
    assert response.status_code == 404


def test_database_not_found():
    assert get_scan('not-a-real-id') is None


def test_integrations_are_disabled():
    response = client.get('/api/integrations')
    assert response.status_code == 200
    assert response.json()['nuclei']['enabled'] is False
    assert response.json()['zap']['enabled'] is False
