import pytest


@pytest.mark.asyncio
async def test_root_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_v1_health_check(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_liveness_probe(async_client):
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_readiness_probe(async_client):
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@pytest.mark.asyncio
@pytest.mark.parametrize('configured,expected', [('a' * 40, 'a' * 40), ('private-misconfigured-value', None)])
async def test_health_exposes_only_valid_release_sha(async_client, monkeypatch, configured, expected):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'RELEASE_SHA', configured)
    response = await async_client.get('/health')
    assert response.json()['release_sha'] == expected
    if expected is None:
        assert configured not in response.text
