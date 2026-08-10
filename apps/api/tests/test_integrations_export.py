import pytest


@pytest.mark.asyncio
async def test_google_oauth_callback(async_client, auth_headers):
    res = await async_client.post(
        "/api/v1/integrations/google/callback",
        json={"code": "mock_oauth_auth_code_9876", "state": "valid_oauth_state_string"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "connected"
    assert data["provider"] == "google"
    assert "drive.file" in data["scopes_granted"]

    # Verify integration status listed
    list_res = await async_client.get("/api/v1/integrations", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) == 1
    # Ensure encrypted token is never exposed in schema response!
    assert "encrypted_tokens" not in list_res.json()["items"][0]


@pytest.mark.asyncio
async def test_google_sync_triggers(async_client, auth_headers):
    # Ensure integration is connected
    await async_client.post(
        "/api/v1/integrations/google/callback",
        json={"code": "mock_code", "state": "mock_state"},
        headers=auth_headers,
    )

    # Trigger Drive Sync
    drive_res = await async_client.post(
        "/api/v1/sync/gdrive",
        json={"folder_id": "root_brain_folder", "sync_mode": "one_way"},
        headers=auth_headers,
    )
    assert drive_res.status_code == 202  # Accepted
    assert drive_res.json()["job_type"] == "sync_google_drive"

    # Trigger Calendar Sync
    cal_res = await async_client.post(
        "/api/v1/sync/calendar", json={"calendar_id": "primary"}, headers=auth_headers
    )
    assert cal_res.status_code == 202
    assert cal_res.json()["job_type"] == "sync_google_calendar"


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
