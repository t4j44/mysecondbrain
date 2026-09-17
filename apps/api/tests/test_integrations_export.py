import pytest


@pytest.mark.asyncio
async def test_google_oauth_callback_requires_configuration(async_client, auth_headers):
    res = await async_client.post(
        "/api/v1/integrations/google/callback",
        json={"code": "mock_oauth_auth_code_9876", "state": "valid_oauth_state_string"},
        headers=auth_headers,
    )
    assert res.status_code == 503
    assert res.json()['error']['code'] == 'GOOGLE_NOT_CONFIGURED'

    # Must not create a falsely connected integration row
    list_res = await async_client.get("/api/v1/integrations", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["items"] == []


@pytest.mark.asyncio
async def test_google_sync_triggers_fail_closed(async_client, auth_headers):
    drive_res = await async_client.post(
        "/api/v1/sync/gdrive",
        json={"folder_id": "root_brain_folder", "sync_mode": "one_way"},
        headers=auth_headers,
    )
    assert drive_res.status_code == 409
    assert drive_res.json()["error"]["code"] == "INTEGRATION_NOT_CONNECTED"

    cal_res = await async_client.post(
        "/api/v1/sync/calendar", json={"calendar_id": "primary"}, headers=auth_headers
    )
    assert cal_res.status_code == 409
    assert cal_res.json()["error"]["code"] == "INTEGRATION_NOT_CONNECTED"


@pytest.mark.asyncio
async def test_markdown_export_workflow(async_client, auth_headers):
    # Enqueue Markdown archive export
    exp_res = await async_client.post(
        "/api/v1/export/markdown", json={"export_type": "full"}, headers=auth_headers
    )
    assert exp_res.status_code == 202
    data = exp_res.json()
    assert data["export_type"] == "full"
    assert data["status"] in {"pending", "processing", "completed"}

    # Retrieve export list history
    list_res = await async_client.get("/api/v1/exports", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) >= 1
