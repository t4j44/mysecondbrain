"""Test isolation must not bypass the real limiter within an HTTP scenario."""
import pytest

from app.middleware.rate_limiting import DEFAULT_RATE_LIMIT, RateLimitingMiddleware


@pytest.mark.asyncio
async def test_http_rate_limit_still_enforced_within_one_test(async_client):
    from app.main import app

    # Build the real stack, then put this test's IP at the actual limit.
    assert (await async_client.get('/mcp/info')).status_code == 200
    middleware = app.middleware_stack
    while not isinstance(middleware, RateLimitingMiddleware):
        middleware = middleware.app
    bucket = next(key for key in middleware.tracker if key.endswith(':normal'))
    _, window_start = middleware.tracker[bucket]
    middleware.tracker[bucket] = (DEFAULT_RATE_LIMIT, window_start)
    denied = await async_client.get('/mcp/info')
    assert denied.status_code == 429
    assert denied.json()['error']['code'] == 'RATE_LIMITED'
    assert denied.json()['error']['details']['limit'] == DEFAULT_RATE_LIMIT
    assert 'Retry-After' in denied.headers
