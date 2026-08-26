import pytest


@pytest.mark.asyncio
async def test_google_oauth_callback_is_honestly_not_implemented(async_client, auth_headers):
    res = await async_client.post(
        "/api/v1/integrations/google/callback",
        json={"code": "mock_oauth_auth_code_9876", "state": "valid_oauth_state_string"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_implemented"
    assert data["status"] != "connected"
    assert data["provider"] == "google"
    assert data.get("code") == "INTEGRATION_NOT_IMPLEMENTED"
    assert not data.get("scopes_granted")

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
    assert drive_res.status_code == 501
    assert drive_res.json()["error"]["code"] == "INTEGRATION_NOT_IMPLEMENTED"

    cal_res = await async_client.post(
        "/api/v1/sync/calendar", json={"calendar_id": "primary"}, headers=auth_headers
    )
    assert cal_res.status_code == 501
    assert cal_res.json()["error"]["code"] == "INTEGRATION_NOT_IMPLEMENTED"


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
