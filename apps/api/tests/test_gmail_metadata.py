from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import func, select

from app.config import settings
from app.core.errors import IntegrationError
from app.integrations.gmail_metadata import (
    HEADERS,
    MAX_MESSAGES,
    MAX_RECIPIENTS,
    GmailSync,
    normalize_email,
    parse_message,
)
from app.integrations.google_client import SCOPES, GoogleIntegrationService
from app.models.entities import EmailContact, Integration, Interaction, JobRecord, Person
from app.services.person_context import delete_person_context
from app.services.relationships import RelationshipService
from tests.conftest import TestingSessionLocal

ME = 'me@example.test'
NOW = datetime.now(timezone.utc)


def ms(days_ago: float) -> int:
    return int((NOW - timedelta(days=days_ago)).timestamp() * 1000)


def mail(identifier, *, sender, to=(), cc=(), days_ago=1, labels=('INBOX',), extra=()):
    headers = [{'name': 'From', 'value': sender}, {'name': 'To', 'value': ', '.join(to)}, {'name': 'Cc', 'value': ', '.join(cc)}, *extra]
    return {'id': identifier, 'internalDate': str(ms(days_ago)), 'labelIds': list(labels), 'payload': {'headers': headers}}


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


def test_addresses_are_compared_the_way_gmail_compares_them():
    assert normalize_email(' Sarah.K+news@GMAIL.com ') == 'sarahk@gmail.com'
    assert normalize_email('sarahk@googlemail.com') == 'sarahk@gmail.com'
    assert normalize_email('Sarah.K+x@Work.example') == 'sarah.k+x@work.example'
    assert [normalize_email(item) for item in (None, '', 'nope', 'a@b', '+@gmail.com')] == [None] * 5


def test_sent_mail_counts_for_each_recipient_and_received_mail_for_the_sender():
    sent = parse_message(mail('1', sender=f'Taj <{ME}>', to=['Sarah K <sarah@example.test>'], cc=['omar@example.test', ME]), ME)
    assert [(item.email, item.direction) for item in sent] == [('sarah@example.test', 'sent'), ('omar@example.test', 'sent')]
    inbound = mail('2', sender='"Sarah K" <Sarah@Example.test>', to=[ME], cc=['omar@example.test'])
    received = parse_message(inbound, ME)
    assert [(item.email, item.direction) for item in received] == [('sarah@example.test', 'received')]
    assert received[0].at == datetime.fromtimestamp(int(inbound['internalDate']) / 1000, tz=timezone.utc)


@pytest.mark.parametrize('message', [
    mail('a', sender='shop@example.test', to=[ME], labels=('INBOX', 'CATEGORY_PROMOTIONS')),
    mail('b', sender='friend@example.test', to=[ME], labels=('SPAM',)),
    mail('c', sender=ME, to=['friend@example.test'], labels=('DRAFT',)),
    mail('d', sender='news@example.test', to=[ME], extra=[{'name': 'List-Unsubscribe', 'value': '<mailto:x@y.z>'}]),
    mail('e', sender='news@example.test', to=[ME], extra=[{'name': 'Precedence', 'value': 'Bulk'}]),
    mail('f', sender='bot@example.test', to=[ME], extra=[{'name': 'Auto-Submitted', 'value': 'auto-replied'}]),
    mail('g', sender=ME, to=[f'p{n}@example.test' for n in range(MAX_RECIPIENTS + 1)]),
    mail('h', sender=ME, to=[ME]),
    {'id': 'i', 'internalDate': 'garbage', 'payload': {'headers': [{'name': 'From', 'value': 'a@b.cc'}]}},
    {'id': 'j'},
])
def test_bulk_automated_junk_and_unreadable_mail_is_ignored(message):
    assert parse_message(message, ME) == []


def test_the_date_header_is_the_fallback_when_gmail_gives_no_internal_date():
    message = {'id': 'k', 'payload': {'headers': [{'name': 'From', 'value': 'sarah@example.test'}, {'name': 'To', 'value': ME},
                                                    {'name': 'Date', 'value': 'Tue, 6 Oct 2026 09:30:00 +0600'}]}}
    assert parse_message(message, ME)[0].at == datetime(2026, 10, 6, 3, 30, tzinfo=timezone.utc)


class FakeGmail:
    def __init__(self, messages, status=200):
        self.messages, self.status, self.calls = messages, status, []

    def install(self, monkeypatch):
        async def request(_client, method, url, **kwargs):
            return await self.handle(method, url, **kwargs)
        monkeypatch.setattr(httpx.AsyncClient, 'request', request)

    async def handle(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        assert kwargs['headers']['Authorization'] == 'Bearer test-access'
        if self.status != 200:
            return httpx.Response(self.status, json={}, request=httpx.Request(method, url))
        if url.endswith('/messages'):
            params = kwargs['params']
            start, size = int(params.get('pageToken', 0)), int(params['maxResults'])
            page = self.messages[start:start + size]
            body = {'messages': [{'id': item['id']} for item in page]}
            if start + size < len(self.messages):
                body['nextPageToken'] = str(start + size)
        else:
            body = next(item for item in self.messages if item['id'] == url.rsplit('/', 1)[1])
        return httpx.Response(200, json=body, request=httpx.Request(method, url))

    @property
    def message_reads(self):
        return [call for call in self.calls if not call[1].endswith('/messages')]

    @property
    def list_calls(self):
        return [call for call in self.calls if call[1].endswith('/messages')]


@pytest.fixture
async def mailbox(monkeypatch, test_user_id):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    async with TestingSessionLocal() as db:
        integration = Integration(user_id=test_user_id, provider_name='gmail', account_identifier=ME, scopes=[SCOPES['gmail']])
        sarah = Person(user_id=test_user_id, name='Sarah K', email='Sarah@Example.test')
        omar = Person(user_id=test_user_id, name='Omar', email='omar@example.test')
        nobody = Person(user_id=test_user_id, name='No Email')
        db.add_all([integration, sarah, omar, nobody])
        await db.commit()
        yield {'db': db, 'integration': str(integration.id), 'sarah': str(sarah.id), 'omar': str(omar.id), 'owner': test_user_id}


async def contacts(db):
    rows = (await db.execute(select(EmailContact))).scalars().all()
    return {str(row.person_id): (aware(row.last_sent_at), aware(row.last_received_at)) for row in rows}


@pytest.mark.asyncio
async def test_sync_records_dates_only_and_requests_only_headers(monkeypatch, mailbox):
    fake = FakeGmail([
        mail('m1', sender='Omar <omar@example.test>', to=[ME], days_ago=2),
        mail('m2', sender=ME, to=['sarah@example.test'], days_ago=5),
        mail('m3', sender='sarah@example.test', to=[ME], days_ago=9),
        mail('m4', sender='stranger@example.test', to=[ME], days_ago=10),
        mail('m5', sender=ME, to=['sarah@example.test'], days_ago=20)])
    fake.install(monkeypatch)
    db = mailbox['db']
    result = await GmailSync(db, mailbox['owner']).run({'integration_id': mailbox['integration']})
    await db.commit()
    assert result == {'messages_checked': 5, 'people_with_email': 2, 'people_updated': 2, 'complete': True}
    stored = await contacts(db)
    sarah_sent, sarah_received = stored[mailbox['sarah']]
    assert abs((sarah_sent - (NOW - timedelta(days=5))).total_seconds()) < 5 and sarah_sent > sarah_received
    assert stored[mailbox['omar']][0] is None and stored[mailbox['omar']][1] is not None
    assert len(stored) == 2  # strangers and people without an address leave no trace

    for _, url, kwargs in fake.calls:
        params = kwargs['params']
        names = parse_qs(urlparse(url + '?' + httpx.QueryParams(params).__str__()).query)
        assert 'q' not in names and 'snippet' not in names.get('fields', [''])[0] and 'body' not in names.get('fields', [''])[0]
    reads = fake.message_reads
    assert len(reads) == 5
    for _, _, kwargs in reads:
        params = httpx.QueryParams(kwargs['params'])
        assert params['format'] == 'metadata' and params.get_list('metadataHeaders') == list(HEADERS)
        assert 'Subject' not in HEADERS and 'snippet' not in params['fields'] and 'body' not in params['fields']
    assert {column.name for column in EmailContact.__table__.columns} == {
        'integration_id', 'person_id', 'user_id', 'last_sent_at', 'last_received_at', 'updated_at'}


@pytest.mark.asyncio
async def test_a_second_sync_stops_at_what_it_already_knows_and_never_moves_dates_backwards(monkeypatch, mailbox):
    db, owner = mailbox['db'], mailbox['owner']
    history = [mail(f'old{n}', sender='sarah@example.test', to=[ME], days_ago=n) for n in range(1, 61)]
    first = FakeGmail(history)
    first.install(monkeypatch)
    result = await GmailSync(db, owner).run({'integration_id': mailbox['integration']})
    await db.commit()
    assert result['messages_checked'] == 60 and result['complete'] is True and len(first.list_calls) == 3
    before = await contacts(db)
    cursor = await db.scalar(select(JobRecord).where(JobRecord.job_type == f"gmail_sync_cursor:{mailbox['integration']}"))
    assert int(cursor.result_payload['internal_date_ms']) == int(history[0]['internalDate'])
    assert before[mailbox['sarah']][0] is None  # nothing was ever sent to her

    second = FakeGmail([mail('new', sender=ME, to=['sarah@example.test'], days_ago=0.5), *history])
    second.install(monkeypatch)
    result = await GmailSync(db, owner).run({'integration_id': mailbox['integration']})
    await db.commit()
    assert result['complete'] is True and len(second.list_calls) == 1 and len(second.message_reads) == 25
    after = await contacts(db)
    assert after[mailbox['sarah']][0] is not None and after[mailbox['sarah']][1] == before[mailbox['sarah']][1]

    # Re-reading identical mail, or meeting older mail, never moves a date backwards or changes it.
    again = await GmailSync(db, owner).run({'integration_id': mailbox['integration']})
    older = FakeGmail([mail('older', sender=ME, to=['sarah@example.test'], days_ago=40)])
    older.install(monkeypatch)
    await GmailSync(db, owner).run({'integration_id': mailbox['integration']})
    await db.commit()
    assert again == {'messages_checked': 1, 'people_with_email': 2, 'people_updated': 0, 'complete': True}
    assert (await contacts(db)) == after


@pytest.mark.asyncio
async def test_a_very_large_mailbox_is_read_in_part_and_reported_as_incomplete(monkeypatch, mailbox):
    flood = FakeGmail([mail(f'm{n}', sender='sarah@example.test', to=[ME], days_ago=1 + n / 10000) for n in range(MAX_MESSAGES + 20)])
    flood.install(monkeypatch)
    db = mailbox['db']
    result = await GmailSync(db, mailbox['owner']).run({'integration_id': mailbox['integration']})
    await db.commit()
    assert result['messages_checked'] == MAX_MESSAGES and result['complete'] is False
    assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type.like('gmail_sync_cursor%'))) == 0


@pytest.mark.asyncio
async def test_nothing_is_read_when_no_saved_person_has_an_email_address(monkeypatch, test_user_id):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    fake = FakeGmail([])
    fake.install(monkeypatch)
    async with TestingSessionLocal() as db:
        db.add_all([Integration(user_id=test_user_id, provider_name='gmail', account_identifier=ME, scopes=[SCOPES['gmail']]),
                    Person(user_id=test_user_id, name='No Email')])
        await db.commit()
        result = await GmailSync(db, test_user_id).run({})
    assert result == {'messages_checked': 0, 'people_with_email': 0, 'people_updated': 0, 'complete': True}
    assert fake.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize('status, code', [(401, 'GOOGLE_RECONNECT'), (403, 'GMAIL_ACCESS_DENIED')])
async def test_revoked_or_denied_access_is_reported_plainly(monkeypatch, mailbox, status, code):
    FakeGmail([], status).install(monkeypatch)
    with pytest.raises(IntegrationError) as error:
        await GmailSync(mailbox['db'], mailbox['owner']).run({'integration_id': mailbox['integration']})
    assert error.value.code == code


@pytest.mark.asyncio
async def test_an_account_that_was_never_identified_cannot_sync(monkeypatch, test_user_id):
    async with TestingSessionLocal() as db:
        db.add(Integration(user_id=test_user_id, provider_name='gmail', account_identifier=None, scopes=[SCOPES['gmail']]))
        await db.commit()
        with pytest.raises(IntegrationError) as error:
            await GmailSync(db, test_user_id).run({})
        assert error.value.code == 'GOOGLE_ACCOUNT_UNKNOWN'


@pytest.mark.asyncio
async def test_gmail_is_not_connected_unless_google_names_the_account(monkeypatch, test_user_id):
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_ID', 'test-client')
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setattr(GoogleIntegrationService, '_store_tokens', AsyncMock())

    async def post(_client, url, **kwargs):
        return httpx.Response(200, request=httpx.Request('POST', url), json={'access_token': 'a', 'refresh_token': 'r', 'scope': SCOPES['gmail']})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    async with TestingSessionLocal() as db:
        service = GoogleIntegrationService(db, test_user_id)
        authorization = await service.authorize('gmail')
        params = parse_qs(urlparse(authorization['url']).query)
        assert params['scope'] == [f"openid email {SCOPES['gmail']}"]
        with pytest.raises(IntegrationError):
            await service.connect_oauth_callback('code', params['state'][0])
        assert await db.scalar(select(func.count()).select_from(Integration)) == 0


class _NoVault:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, *args, **kwargs):
        return None

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_disconnecting_gmail_forgets_the_imported_dates(monkeypatch, mailbox):
    monkeypatch.setattr('app.integrations.google_client.admin_db_session', lambda reason: _NoVault())
    FakeGmail([mail('m1', sender='sarah@example.test', to=[ME])]).install(monkeypatch)
    db = mailbox['db']
    await GmailSync(db, mailbox['owner']).run({'integration_id': mailbox['integration']})
    await db.commit()
    assert await db.scalar(select(func.count()).select_from(EmailContact)) == 1
    assert await GoogleIntegrationService(db, mailbox['owner']).disconnect_provider('gmail', mailbox['integration']) is True
    assert await db.scalar(select(func.count()).select_from(EmailContact)) == 0
    assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type.like('gmail_sync_cursor%'))) == 0


@pytest.mark.asyncio
async def test_recent_email_stops_a_quiet_contact_being_flagged_and_appears_on_the_profile(mailbox):
    db = mailbox['db']
    db.add(Interaction(user_id=mailbox['owner'], person_id=mailbox['sarah'], interaction_type='meeting', title='Coffee', date=NOW - timedelta(days=100)))
    await db.commit()
    service = RelationshipService(db, mailbox['owner'])
    quiet = await service.followups(mailbox['sarah'])
    assert len(quiet) == 1 and quiet[0]['recency']['label'] == 'Dormant'

    db.add(EmailContact(user_id=mailbox['owner'], integration_id=mailbox['integration'], person_id=mailbox['sarah'],
                        last_sent_at=NOW - timedelta(days=4), last_received_at=NOW - timedelta(days=12)))
    await db.commit()
    assert await service.followups(mailbox['sarah']) == []
    profile = await service.profile(mailbox['sarah'])
    assert profile['recency']['label'] == 'Active' and profile['recency']['days_since'] == 4
    assert abs((aware(profile['email_contact']['last_sent_at']) - (NOW - timedelta(days=4))).total_seconds()) < 5
    draft_facts = await service._draft_facts(await service.person(mailbox['sarah']))
    assert any(line.startswith('You last emailed them on') for line in draft_facts.lines)
    assert any(line.startswith('They last emailed you on') for line in draft_facts.lines)


@pytest.mark.asyncio
async def test_deleting_a_contact_removes_their_email_dates(mailbox):
    db = mailbox['db']
    db.add_all([EmailContact(user_id=mailbox['owner'], integration_id=mailbox['integration'], person_id=mailbox['sarah'], last_sent_at=NOW),
                EmailContact(user_id=mailbox['owner'], integration_id=mailbox['integration'], person_id=mailbox['omar'], last_sent_at=NOW)])
    await db.commit()
    await delete_person_context(db, await db.get(Person, mailbox['sarah']))
    await db.commit()
    assert set(await contacts(db)) == {mailbox['omar']}


@pytest.mark.asyncio
async def test_sync_endpoint_pins_the_account_and_gmail_can_be_authorized(async_client, auth_headers, test_user_id, monkeypatch):
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_ID', 'test-client')
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    async with TestingSessionLocal() as db:
        row = Integration(user_id=test_user_id, provider_name='gmail', account_identifier=ME, scopes=[SCOPES['gmail']])
        db.add(row)
        await db.commit()
        integration = str(row.id)
    queued = await async_client.post('/api/v1/sync/gmail', headers=auth_headers, json={})
    assert queued.status_code == 202, queued.text
    async with TestingSessionLocal() as db:
        job = await db.get(JobRecord, queued.json()['id'])
        assert job.job_type == 'sync_gmail' and job.result_payload['integration_id'] == integration
    authorize = await async_client.post('/api/v1/integrations/google/authorize?provider=gmail', headers=auth_headers)
    assert authorize.status_code == 200, authorize.text
    assert parse_qs(urlparse(authorize.json()['url']).query)['scope'] == [f"openid email {SCOPES['gmail']}"]
