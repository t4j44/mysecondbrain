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


@pytest.mark.parametrize('runtime_sha', ['b' * 40, None])
def test_release_metadata_prefers_runtime_commit_over_pinned_label(monkeypatch, runtime_sha):
    from app.config import Settings

    monkeypatch.setenv('RELEASE_SHA', 'a' * 40)
    if runtime_sha:
        monkeypatch.setenv('RENDER_GIT_COMMIT', runtime_sha)
    else:
        monkeypatch.delenv('RENDER_GIT_COMMIT', raising=False)
    configuration = Settings(_env_file=None)
    assert configuration.verified_release_sha == (runtime_sha or 'a' * 40)
