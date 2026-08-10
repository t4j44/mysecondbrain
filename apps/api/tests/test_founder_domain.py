import pytest


@pytest.mark.asyncio
async def test_profile_read_and_update(async_client, auth_headers):
    # 1. Read auto-created profile
    res = await async_client.get("/api/v1/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "taj@founder.local"

    # 2. Update bio and preferences
    update_res = await async_client.patch(
        "/api/v1/me",
        json={"bio": "Founder of Taj's Second Brain", "preferences": {"theme": "terminal-dark"}},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["bio"] == "Founder of Taj's Second Brain"


@pytest.mark.asyncio
async def test_venture_lifecycle_and_slug_conflict(async_client, auth_headers):
    # 1. Create Venture
    v_data = {"name": "Venture One", "slug": "venture-one", "priority": "high"}
    res = await async_client.post("/api/v1/ventures", json=v_data, headers=auth_headers)
    assert res.status_code == 201
    v_id = res.json()["id"]

    # 2. Attempt duplicate slug creation -> should fail with 409 Conflict (Task 12)
    dup_res = await async_client.post("/api/v1/ventures", json=v_data, headers=auth_headers)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "DUPLICATE_RESOURCE"

    # 3. Update Venture
    up_res = await async_client.patch(
        f"/api/v1/ventures/{v_id}", json={"status": "paused"}, headers=auth_headers
    )
    assert up_res.status_code == 200
    assert up_res.json()["status"] == "paused"

    # 4. Delete / Archive Venture
    del_res = await async_client.delete(f"/api/v1/ventures/{v_id}", headers=auth_headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_project_and_task_management(async_client, auth_headers):
    # 1. Create Project
    p_res = await async_client.post(
        "/api/v1/projects",
        json={"name": "MVP Launch", "status": "in_progress", "priority": "urgent"},
        headers=auth_headers,
    )
    assert p_res.status_code == 201
    p_id = p_res.json()["id"]

    # 2. Create Task linked to Project
    t_res = await async_client.post(
        "/api/v1/tasks",
        json={
            "title": "Design Database Schema",
            "project_id": p_id,
            "priority": "high",
            "status": "todo",
        },
        headers=auth_headers,
    )
    assert t_res.status_code == 201
    t_id = t_res.json()["id"]

    # 3. Update Task Status to 'done' -> verification of completion state transition
    patch_res = await async_client.patch(
        f"/api/v1/tasks/{t_id}", json={"status": "done"}, headers=auth_headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "done"


@pytest.mark.asyncio
async def test_kpi_tracking_and_entries(async_client, auth_headers):
    # 1. Define KPI
    kpi_res = await async_client.post(
        "/api/v1/kpis",
        json={
            "name": "Weekly Active Users",
            "category": "founder",
            "unit": "users",
            "target": 1000.0,
        },
        headers=auth_headers,
    )
    assert kpi_res.status_code == 201
    kpi_id = kpi_res.json()["id"]

    # 2. Add KPI Datapoint Entry
    entry_res = await async_client.post(
        f"/api/v1/kpis/{kpi_id}/entries", json={"numeric_value": 450.0}, headers=auth_headers
    )
    assert entry_res.status_code == 201
    assert entry_res.json()["numeric_value"] == 450.0


@pytest.mark.asyncio
async def test_dashboard_summary_and_insights(async_client, auth_headers):
    res_sum = await async_client.get("/api/v1/dashboard/summary?timezone=UTC", headers=auth_headers)
    assert res_sum.status_code == 200
    data = res_sum.json()
    assert "active_ventures_count" in data
    assert "tasks_today" in data

    res_ins = await async_client.get("/api/v1/dashboard/insights", headers=auth_headers)
    assert res_ins.status_code == 200
    ins_data = res_ins.json()
    assert "ai_summary" in ins_data
    assert "recommendations" in ins_data
