from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.core.errors import ValidationError
from app.models.entities import (
    JobRecord,
    Memory,
    Organization,
    Person,
    PersonOrganizationRole,
    PublicProfileClaim,
)
from app.services import public_sources
from tests.conftest import TestingSessionLocal


@pytest.mark.parametrize('url', ['http://example.com/p', 'https://127.0.0.1/p', 'https://169.254.169.254/', 'https://user:secret@example.com/', 'https://example.com:8443/', 'https://example.com/?token=secret', 'https://a.local/p'])
def test_research_rejects_private_or_credential_urls(url):
    with pytest.raises(ValidationError):
        public_sources.public_url(url)


def test_dns_private_answer_is_rejected(monkeypatch):
    monkeypatch.setattr(public_sources.socket, 'getaddrinfo', lambda *a, **kw: [(None, None, None, None, ('10.0.0.2', 443))])
    with pytest.raises(ValidationError):
        public_sources.resolve_public('public.example.com')


def test_robots_disallow_stops_before_reading_profile(monkeypatch):
    monkeypatch.setattr(public_sources, 'resolve_public', lambda host: '8.8.8.8')
    calls = []
    def request(host, address, path, deadline):
        calls.append(path)
        return 200, 'text/plain', 'User-agent: *\nDisallow: /'
    monkeypatch.setattr(public_sources, 'request_page', request)
    with pytest.raises(ValidationError):
        public_sources.read_public_page('https://example.com/team', 'Ahmed')
    assert calls == ['/robots.txt']


def test_public_text_tolerates_malformed_structured_metadata(monkeypatch):
    monkeypatch.setattr(public_sources, 'resolve_public', lambda host: '8.8.8.8')
    def request(host, address, path, deadline):
        if path == '/robots.txt':
            return 404, 'text/plain', ''
        return 200, 'text/html', '<script type="application/ld+json">{"@graph":42}</script><p>Ahmed works at Example.</p>'
    monkeypatch.setattr(public_sources, 'request_page', request)
    result = public_sources.read_public_page('https://example.com/team', 'Ahmed')
    assert result['text'] == 'Ahmed works at Example.' and result['candidates'] == []


@pytest.mark.asyncio
async def test_conflict_requires_review_owner_scope_and_removal(async_client, auth_headers, other_auth_headers, test_user_id, monkeypatch):
    async with TestingSessionLocal() as db:
        person = Person(user_id=test_user_id, name='Ahmed', company='ABC Ventures')
        db.add(person)
        await db.commit()
        person_id = str(person.id)
    fetch = AsyncMock(return_value={'text': 'Ahmed now works at XYZ Capital as a founder.', 'source_url': 'https://example.com/team', 'source_type': 'public_webpage', 'name_mentioned': True, 'candidates': [], 'notice': 'Check identity.'})
    monkeypatch.setattr('app.services.enrichment.fetch_public_page', fetch)
    path = f'/api/v1/relationships/people/{person_id}'
    assert (await async_client.post(path + '/research', headers=other_auth_headers, json={'source_url': 'https://example.com/team'})).status_code == 404
    fetch.assert_not_awaited()
    research = await async_client.post(path + '/research', headers=auth_headers, json={'source_url': 'https://example.com/team'})
    assert research.status_code == 200, research.text
    payload = {'source_id': research.json()['source_id'], 'confirmed_identity': True, 'identity_basis': 'Matching professional role and public portrait', 'field': 'company', 'value': 'XYZ Capital', 'source_quote': 'Ahmed now works at XYZ Capital as a founder.'}
    invalid = await async_client.post(path + '/claims', headers=auth_headers, json={**payload, 'value': 'Invented employer'})
    assert invalid.status_code == 400
    proposed = await async_client.post(path + '/claims', headers=auth_headers, json=payload)
    assert proposed.status_code == 200, proposed.text
    claim = proposed.json()
    assert claim['conflict'] and claim['current_value'] == 'ABC Ventures'
    claim_path = path + '/claims/' + claim['id']
    async with TestingSessionLocal() as db:
        assert (await db.get(Person, person_id)).company == 'ABC Ventures'
        assert await db.scalar(select(func.count()).select_from(Memory)) == 0
    assert (await async_client.post(claim_path + '/review', headers=other_auth_headers, json={'confirmed': True, 'decision': 'apply', 'expected_current': 'ABC Ventures'})).status_code == 404
    stale = await async_client.post(claim_path + '/review', headers=auth_headers, json={'confirmed': True, 'decision': 'apply', 'expected_current': 'Wrong value'})
    assert stale.status_code == 409
    verified = await async_client.post(claim_path + '/review', headers=auth_headers, json={'confirmed': True, 'decision': 'verify'})
    assert verified.status_code == 200 and verified.json()['current_value'] == 'ABC Ventures'
    applied = await async_client.post(claim_path + '/review', headers=auth_headers, json={'confirmed': True, 'decision': 'apply', 'expected_current': 'ABC Ventures'})
    assert applied.status_code == 200, applied.text
    assert applied.json()['current_value'] == 'XYZ Capital'
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Memory)) == 1
        affiliations = (await db.execute(select(Organization.name, PersonOrganizationRole.ended_at).join(
            PersonOrganizationRole, PersonOrganizationRole.organization_id == Organization.id).where(
            PersonOrganizationRole.person_id == person_id))).all()
        assert any(name == 'ABC Ventures' and ended is not None for name, ended in affiliations)
        assert any(name == 'XYZ Capital' and ended is None for name, ended in affiliations)
    assert (await async_client.delete(claim_path, headers=auth_headers)).status_code == 200
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(PublicProfileClaim)) == 0
        memory = await db.scalar(select(Memory))
        assert memory.deleted_at is not None
    # Cached public pages are invalidated with the person, too.
    await async_client.delete('/api/v1/people/' + person_id, headers=auth_headers)
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type == 'public_profile_source')) == 0
