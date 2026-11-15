from fastapi.testclient import TestClient

from app.core.auth import create_access_token, hash_password
from app.database import create_user, get_scan
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_scan_requires_authentication():
    response = client.get('/api/scans')
    assert response.status_code == 401


def test_scan_endpoint_rejects_invalid_target_with_auth(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'auth_secret', 'test-secret-with-more-than-32-characters')
    user = create_user('test-user', hash_password('test-password-123'))
    token = create_access_token(user)
    response = client.post('/api/scan', json={'target': 'ftp://example.com'}, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400


def test_export_requires_authentication():
    response = client.get('/api/scans/missing/export/pdf')
    assert response.status_code == 401


def test_database_not_found():
    assert get_scan('not-a-real-id', 'not-a-real-user') is None


def test_integrations_are_disabled_after_auth(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'auth_secret', 'test-secret-with-more-than-32-characters')
    user = create_user('integration-user', hash_password('test-password-456'))
    token = create_access_token(user)
    response = client.get('/api/integrations', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json()['nuclei']['enabled'] is False
    assert response.json()['zap']['enabled'] is False
