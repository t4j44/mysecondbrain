"""Exercise the official JSON-RPC transport, credential verifier and tool scopes."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.mcp.security import READ_SCOPES
from app.mcp.server import mcp_server
from app.models.entities import Memory
from app.repositories.mcp import MCPCredentialRepository
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_official_transport_initialize_search_scope_and_revoke(test_user_id, other_user_id):
    repo = MCPCredentialRepository()
    async with TestingSessionLocal() as db:
        key = await repo.create_credential(db, test_user_id, 'Beta protocol test', scopes=sorted(READ_SCOPES))
        db.add_all([Memory(user_id=test_user_id, title='Protocol evidence', content='oranges owned context'),
                    Memory(user_id=other_user_id, title='Foreign evidence', content='oranges foreign context')])
        await db.commit()
    headers = {'Authorization': 'Bearer ' + key['plaintext_key'], 'Accept': 'application/json, text/event-stream'}
    async with mcp_server.session_manager.run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://localhost') as client:
            initialize = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
                'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'beta-test', 'version': '1'}}}
            assert (await client.post('/mcp', json=initialize, headers={'Accept': headers['Accept']})).status_code == 401
            response = await client.post('/mcp', json=initialize, headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()['result']['serverInfo']['name'] == 'tajs-second-brain'
            listed = await client.post('/mcp', headers=headers, json={'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
            assert {'search_context', 'find_relevant_contacts', 'search_documents'} <= {tool['name'] for tool in listed.json()['result']['tools']}
            found = await client.post('/mcp', headers=headers, json={'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                'params': {'name': 'search_context', 'arguments': {'query': 'oranges'}}})
            assert found.status_code == 200 and not found.json()['result'].get('isError'), found.text
            assert 'owned context' in found.text and 'foreign context' not in found.text
            denied = await client.post('/mcp', headers=headers, json={'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                'params': {'name': 'capture_context', 'arguments': {'text': 'should not be saved'}}})
            assert denied.json()['result']['isError'] is True
            async with TestingSessionLocal() as db:
                await repo.revoke_credential(db, test_user_id, key['credential_id'])
                await db.commit()
            assert (await client.post('/mcp', headers=headers, json=initialize)).status_code == 401
