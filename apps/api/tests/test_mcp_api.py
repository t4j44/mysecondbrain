import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.mcp.router import MCP_ALL_TOOLS, MCP_WRITE_TOOLS_MANIFEST
from app.models.entities import Profile


@pytest_asyncio.fixture
async def sample_profile(prepare_database, test_user_id: str):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        profile = Profile(id=test_user_id, email="taj@founder.local", settings={})
        session.add(profile)
        await session.commit()
    return test_user_id


@pytest.mark.asyncio
async def test_mcp_credentials_rest_endpoints(
    async_client: AsyncClient, auth_headers: dict, sample_profile
):
    # 1. Create a new MCP API key
    create_payload = {
        "client_name": "Claude Desktop Integration",
        "client_type": "stdio",
        "scopes": [
            "mcp:people:read",
            "mcp:memory:read",
            "mcp:projects:read",
            "mcp:tasks:read",
            "mcp:content:draft",
        ],
    }
    response = await async_client.post(
        "/api/v1/mcp/credentials", headers=auth_headers, json=create_payload
    )
    assert response.status_code == 201, response.text
    res_data = response.json()["data"]
    assert "plaintext_key" in res_data
    assert res_data["plaintext_key"].startswith("sb_mcp_")
    assert res_data["client_name"] == "Claude Desktop Integration"
    plaintext_key = res_data["plaintext_key"]
    cred_id = res_data["credential_id"]

    # 2. List credentials
    list_resp = await async_client.get("/api/v1/mcp/credentials", headers=auth_headers)
    assert list_resp.status_code == 200, list_resp.text
    list_data = list_resp.json()["data"]
    assert len(list_data) == 1
    assert list_data[0]["credential_id"] == cred_id

    # 3. Test /mcp status and tools list
    mcp_info = await async_client.get("/mcp")
    assert mcp_info.status_code == 200
    assert mcp_info.json()["status"] == "online"

    tools_resp = await async_client.get("/mcp/tools")
    assert tools_resp.status_code == 200
    advertised = tools_resp.json()["tools"]
    assert len(advertised) == len(MCP_ALL_TOOLS)
    assert len([t for t in advertised if t.get("write")]) == len(MCP_WRITE_TOOLS_MANIFEST)

    # 4. Invoke MCP tool with valid key
    mcp_headers = {"X-MCP-API-KEY": plaintext_key}
    invoke_resp = await async_client.post(
        "/mcp/tools/invoke",
        headers=mcp_headers,
        json={"tool": "search_people", "arguments": {"query": "Yousuf"}},
    )
    assert invoke_resp.status_code == 200, invoke_resp.text
    assert invoke_resp.json()["status"] == "success"

    # 5. Rotate credential
    rotate_resp = await async_client.post(
        f"/api/v1/mcp/credentials/{cred_id}/rotate", headers=auth_headers
    )
    assert rotate_resp.status_code == 200, rotate_resp.text
    rotate_data = rotate_resp.json()["data"]
    new_secret = rotate_data["plaintext_key"]
    assert new_secret.startswith("sb_mcp_")
    assert new_secret != plaintext_key

    # 6. Revoke credential
    revoke_resp = await async_client.post(
        f"/api/v1/mcp/credentials/{cred_id}/revoke", headers=auth_headers
    )
    assert revoke_resp.status_code == 200, revoke_resp.text
    revoke_data = revoke_resp.json()["data"]
    assert revoke_data["status"] == "revoked"

    # 7. Confirm access stops with revoked key
    denied_resp = await async_client.post(
        "/mcp/tools/invoke",
        headers={"X-MCP-API-KEY": new_secret},
        json={"tool": "search_people", "arguments": {}},
    )
    assert denied_resp.status_code == 401
