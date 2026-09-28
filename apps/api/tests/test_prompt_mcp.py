"""Both MCP transports, real credential paths, owner filtering and revocation."""
import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.mcp.server import mcp_server
from app.models.entities import ContextEvent, Document, EntityEdge, Memory, Person, Project, Task
from app.repositories.mcp import MCPCredentialRepository
from app.services.prompt_context import retrieve_prompt_context
from tests.conftest import TestingSessionLocal
from tests.test_mcp_oauth import authorize, exchange, register
from tests.test_prompt_enhancer import echo_provider as shared_echo_provider

echo_provider = shared_echo_provider

pytestmark = pytest.mark.asyncio
DRAFT = 'mcp:content:draft'
MEMORY = 'mcp:memory:read'


async def seed(owner, other):
    async with TestingSessionLocal() as db:
        db.add_all([Memory(user_id=owner, title='Justor evidence', content='Justor owned competitor research'),
                    Memory(user_id=other, title='Foreign evidence', content='Justor foreign competitor research'),
                    Memory(user_id=owner, title='Deleted evidence', content='Justor deleted', deleted_at=datetime.now(timezone.utc))])
        await db.commit()


async def snapshot():
    async with TestingSessionLocal() as db:
        return {model.__tablename__: [tuple(row) for row in (await db.execute(select(model.__table__))).all()]
                for model in (Memory, Task, Person, Project, EntityEdge, ContextEvent, Document)}


@pytest.mark.parametrize('scopes,use_context,status', [
    ([DRAFT], False, 200), ([DRAFT], True, 403), ([DRAFT, MEMORY], True, 200),
    ([MEMORY], False, 403), ([DRAFT, 'mcp:people:read'], True, 403),
])
async def test_legacy_scopes_owner_no_mutation(async_client, test_user_id, other_user_id, echo_provider, scopes, use_context, status):
    await seed(test_user_id, other_user_id)
    repo = MCPCredentialRepository()
    async with TestingSessionLocal() as db:
        credential = await repo.create_credential(db, test_user_id, 'Prompt synthetic', scopes=scopes)
        await db.commit()
    before = await snapshot()
    response = await async_client.post('/mcp/tools/invoke', headers={'X-MCP-API-KEY': credential['plaintext_key']},
        json={'tool': 'enhance_prompt', 'arguments': {'text': 'research competitors for Justor and decide what to test next',
            'use_context': use_context, 'target': 'claude'}})
    assert response.status_code == status, response.text
    assert await snapshot() == before
    if status == 200:
        result = response.json()['result']
        assert result['context_items_used'] == (1 if use_context else 0)
        assert 'Foreign evidence' not in response.text and 'Deleted evidence' not in response.text
        assert all(set(item) == {'id', 'entity_type', 'title'} for item in result['context_used'])
    else:
        assert not echo_provider


async def oauth_token(client, headers, scopes):
    registered = await register(client, scope=' '.join(scopes))
    response = await authorize(client, registered, scope=' '.join(scopes))
    pending = parse_qs(urlparse(response.headers['location']).fragment)['request'][0]
    assert (await client.post('/oauth/consent/details', headers=headers, json={'request': pending})).status_code == 200
    decision = await client.post('/oauth/consent/decision', headers=headers,
        json={'request': pending, 'confirmed': True, 'approve': True, 'scopes': scopes})
    assert decision.status_code == 200, decision.text
    code = parse_qs(urlparse(decision.json()['redirect_to']).query)['code'][0]
    response = await exchange(client, registered, code)
    assert response.status_code == 200, response.text
    return response.json()['access_token']


@pytest.mark.parametrize('credential_kind', ['oauth', 'legacy'])
async def test_sdk_acceptance_permission_revocation_and_annotations(async_client, auth_headers, test_user_id,
        other_user_id, fresh_mcp_transport, echo_provider, credential_kind):
    await seed(test_user_id, other_user_id)
    async def token(scopes):
        if credential_kind == 'oauth':
            return await oauth_token(async_client, auth_headers, scopes)
        async with TestingSessionLocal() as db:
            result = await MCPCredentialRepository().create_credential(db, test_user_id, 'SDK synthetic', scopes=scopes)
            await db.commit()
            return result['plaintext_key']
    keys = [await token(scopes) for scopes in ([DRAFT], [DRAFT, 'mcp:people:read'], [MEMORY], [DRAFT, MEMORY])]
    before = await snapshot()
    async with mcp_server.session_manager.run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://localhost') as client:
            async def call(key, method='tools/call', **arguments):
                return await client.post('/mcp', headers={'Authorization': 'Bearer ' + key,
                    'Accept': 'application/json, text/event-stream'}, json={'jsonrpc': '2.0', 'id': 1, 'method': method,
                    **({'params': {'name': 'enhance_prompt', 'arguments': {'text': 'research competitors for Justor and decide what we should test next', **arguments}}}
                       if method == 'tools/call' else {})})
            listed = (await call(keys[0], method='tools/list')).json()['result']['tools']
            tool = next(item for item in listed if item['name'] == 'enhance_prompt')
            assert tool['annotations']['readOnlyHint'] and not tool['annotations']['destructiveHint']
            assert not (await call(keys[0])).json()['result'].get('isError')
            for key in keys[:3]:
                assert (await call(key, use_context=True)).json()['result']['isError']
            allowed = await call(keys[3], use_context=True, target='claude')
            assert not allowed.json()['result'].get('isError'), allowed.text
            assert 'Justor evidence' in allowed.text and 'Foreign evidence' not in allowed.text and 'Deleted evidence' not in allowed.text
            assert (await call(keys[0], use_context='false')).json()['result']['isError']
            if credential_kind == 'oauth':
                listing = (await async_client.get('/api/v1/mcp/oauth/connections', headers=auth_headers)).json()
                for grant in listing:
                    assert (await async_client.delete('/api/v1/mcp/oauth/connections/' + grant['id'], headers=auth_headers)).status_code == 200
                assert (await call(keys[3], use_context=True)).status_code == 401
            else:
                async with TestingSessionLocal() as db:
                    repo = MCPCredentialRepository()
                    verified = await repo.verify_api_key(db, keys[3])
                    await repo.revoke_credential(db, test_user_id, verified['credential_id'])
                    await db.commit()
                assert (await call(keys[3], use_context=True)).status_code == 401
    assert await snapshot() == before


async def test_legacy_invalid_options_safe_response(async_client, test_user_id, echo_provider):
    async with TestingSessionLocal() as db:
        key = await MCPCredentialRepository().create_credential(db, test_user_id, 'Validation', scopes=[DRAFT])
        await db.commit()
    response = await async_client.post('/mcp/tools/invoke', headers={'X-MCP-API-KEY': key['plaintext_key']},
        json={'tool': 'enhance_prompt', 'arguments': {'text': 'private body must not echo', 'use_context': 'false'}})
    assert response.status_code == 422 and 'private body' not in response.text
    assert not echo_provider


async def test_retrieval_graph_events_and_normalized_document_owner_filters(test_user_id, other_user_id, monkeypatch):
    from app.core.errors import AIProviderError
    async def offline(*args, **kwargs):
        raise AIProviderError('Synthetic offline embedding')
    monkeypatch.setattr('app.services.prompt_context.semantic_search', offline)
    async with TestingSessionLocal() as db:
        project = Project(user_id=test_user_id, name='Justor', description='competitor experiments')
        person = Person(user_id=test_user_id, name='A useful advisor')
        foreign = Person(user_id=other_user_id, name='Foreign advisor')
        event = ContextEvent(user_id=test_user_id, event_type='moment', title='Justor workshop',
            summary='Workshop evidence', occurred_at=datetime.now(timezone.utc), source_type='manual')
        restricted = ContextEvent(user_id=test_user_id, event_type='moment', title='Justor restricted',
            privacy_class='restricted', occurred_at=datetime.now(timezone.utc), source_type='manual')
        db.add_all([project, person, foreign, event, restricted])
        await db.flush()
        for target in (person, foreign):
            db.add(EntityEdge(user_id=test_user_id, source_entity_type='project', source_entity_id=project.id,
                target_entity_type='person', target_entity_id=target.id, relationship_type='related_to', source_event_id=event.id))
        db.add(Document(user_id=test_user_id, filename='evidence.md', sanitized_filename='evidence.md', mime_type='text/markdown',
            extension='md', size_bytes=123, checksum=str(uuid4()), storage_bucket='private', storage_path='private.md',
            extracted_text='# Justor\nCompetitor normalized evidence.\n' + 'Unneeded appendix. ' * 1000))
        await db.commit()
        results = await retrieve_prompt_context(db, test_user_id, 'Justor', 8)
        identities = {item['id'] for item in results}
        assert {str(project.id), str(person.id), str(event.id)} <= identities
        assert str(foreign.id) not in identities and str(restricted.id) not in identities
        docs = [item for item in results if item['entity_type'] == 'document']
        assert len(docs) == 1 and len(docs[0]['snippet']) <= 900
        assert 'normalized evidence' in docs[0]['snippet']
        assert len(results) <= 8 and 'Foreign advisor' not in json.dumps(results)


async def test_recognized_temporal_query_does_not_fall_back_to_undated_facts(monkeypatch, test_user_id):
    from unittest.mock import AsyncMock
    monkeypatch.setattr('app.services.prompt_context.structured_answer', AsyncMock(return_value={'citations': []}))
    fallback = AsyncMock(side_effect=AssertionError('Undated fallback is forbidden'))
    monkeypatch.setattr('app.services.prompt_context.perform_keyword_search', fallback)
    async with TestingSessionLocal() as db:
        assert await retrieve_prompt_context(db, test_user_id, 'what happened on an invalid date', 5) == []
    fallback.assert_not_called()
