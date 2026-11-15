from fastapi.testclient import TestClient

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.database import create_scan_job, create_user, get_scan, get_scan_job, initialize_database, list_scan_jobs
from app.main import app

client = TestClient(app)


def _auth_headers(monkeypatch, username='test-user', role='user'):
    monkeypatch.setattr(settings, 'auth_secret', 'test-secret-with-more-than-32-characters')
    user = create_user(username, hash_password(f'{username}-password-123'), role=role)
    return user, {'Authorization': f'Bearer {create_access_token(user)}'}


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_scan_requires_authentication():
    assert client.get('/api/scans').status_code == 401


def test_admin_user_password_uses_supported_hash(monkeypatch):
    _, headers = _auth_headers(monkeypatch, 'admin-test', 'admin')
    response = client.post('/api/admin/users', json={
        'username': 'new-analyst', 'password': 'a-long-strong-password', 'role': 'user',
    }, headers=headers)
    assert response.status_code == 201
    from app.database import get_user_by_username
    user = get_user_by_username('new-analyst')
    assert user is not None
    assert verify_password('a-long-strong-password', user['password_hash'])


def test_admin_endpoint_rejects_regular_user(monkeypatch):
    _, headers = _auth_headers(monkeypatch, 'regular-test', 'user')
    assert client.get('/api/admin/users', headers=headers).status_code == 403


def test_owner_scoped_scan_lookup(monkeypatch):
    user, _ = _auth_headers(monkeypatch, 'owner-test')
    from app.database import save_scan
    saved = save_scan({'target': 'https://example.com', 'status': 'completed', 'summary': {}}, user['id'])
    assert get_scan(saved['id'], user['id']) is not None
    assert get_scan(saved['id'], 'different-owner') is None


def test_jobs_are_owner_scoped_and_disabled_by_default(monkeypatch):
    user, headers = _auth_headers(monkeypatch, 'job-test')
    monkeypatch.setattr(settings, 'scheduler_enabled', False)
    response = client.post('/api/jobs', json={'target': 'https://example.com'}, headers=headers)
    assert response.status_code == 400
    created = create_scan_job(user['id'], 'https://example.com', 3600)
    assert get_scan_job(created['id'], user['id']) is not None
    assert get_scan_job(created['id'], 'other-user') is None
    assert created in list_scan_jobs(user['id'])


def test_existing_schema_migration_is_repeatable():
    initialize_database()
    initialize_database()


def test_integration_status_does_not_claim_unimplemented_scanners(monkeypatch):
    _, headers = _auth_headers(monkeypatch, 'integration-test')
    monkeypatch.setattr(settings, 'nuclei_enabled', True, raising=False)
    monkeypatch.setattr(settings, 'zap_enabled', True, raising=False)
    result = client.get('/api/integrations', headers=headers).json()
    assert result['nuclei']['enabled'] is False
    assert result['zap']['enabled'] is False
