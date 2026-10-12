"""Migration 34: email contact dates are owner-only, owner-referenced and removed with their parents."""
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.db.rls import identity_statements
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]

INSERT = ("INSERT INTO public.email_contacts(user_id,integration_id,person_id,last_sent_at,last_received_at) "
          "VALUES(CAST(:user AS uuid),CAST(:integration AS uuid),CAST(:person AS uuid),:sent,:received)")


async def identity(conn, owner):
    for sql, params in identity_statements(owner):
        await conn.execute(text(sql), params)


@pytest.fixture
async def mail(pg_engine):
    ids = {key: str(uuid4()) for key in ('owner', 'other', 'person', 'foreign_person', 'integration', 'foreign_integration')}
    async with pg_engine.begin() as conn:
        for owner in (ids['owner'], ids['other']):
            await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                               {'id': owner, 'email': owner + '@email-contacts.test'})
        for person, owner in ((ids['person'], ids['owner']), (ids['foreign_person'], ids['other'])):
            await conn.execute(text("INSERT INTO public.people(id,user_id,name) VALUES(CAST(:id AS uuid),CAST(:owner AS uuid),'Synthetic')"),
                               {'id': person, 'owner': owner})
        for integration, owner in ((ids['integration'], ids['owner']), (ids['foreign_integration'], ids['other'])):
            await conn.execute(text("INSERT INTO public.integrations(id,user_id,provider,external_account_identifier) "
                                    "VALUES(CAST(:id AS uuid),CAST(:owner AS uuid),'gmail','synthetic@example.test')"),
                               {'id': integration, 'owner': owner})
    try:
        yield ids
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM public.account_closures WHERE user_id=CAST(:owner AS uuid)'), ids)
            for owner in (ids['owner'], ids['other']):
                await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})


def row(ids, **overrides):
    return {'user': ids['owner'], 'integration': ids['integration'], 'person': ids['person'],
            'sent': '2026-10-01T10:00:00+00', 'received': None, **overrides}


async def save(pg_engine, params):
    async with pg_engine.begin() as conn:
        await conn.execute(text(INSERT), params)


async def test_only_the_owner_can_see_or_change_their_email_dates(pg_engine, mail):
    async with pg_engine.begin() as conn:
        await identity(conn, mail['owner'])
        await conn.execute(text(INSERT), row(mail))
    for owner, expected in ((mail['owner'], 1), (mail['other'], 0)):
        async with pg_engine.begin() as conn:
            await identity(conn, owner)
            assert await conn.scalar(text('SELECT count(*) FROM public.email_contacts'), {}) == expected
            if owner == mail['other']:
                assert (await conn.execute(text("UPDATE public.email_contacts SET last_sent_at=now()"))).rowcount == 0
                assert (await conn.execute(text('DELETE FROM public.email_contacts'))).rowcount == 0


async def test_a_user_cannot_write_a_row_for_someone_else(pg_engine, mail):
    with pytest.raises(DBAPIError):
        async with pg_engine.begin() as conn:
            await identity(conn, mail['other'])
            await conn.execute(text(INSERT), row(mail))


@pytest.mark.parametrize('overrides', [
    {'person': 'foreign_person'},
    {'integration': 'foreign_integration'},
])
async def test_rows_cannot_point_at_another_users_person_or_connection(pg_engine, mail, overrides):
    params = row(mail, **{key: mail[value] for key, value in overrides.items()})
    with pytest.raises(IntegrityError):
        await save(pg_engine, params)


async def test_a_row_must_carry_at_least_one_date(pg_engine, mail):
    with pytest.raises(IntegrityError):
        await save(pg_engine, row(mail, sent=None, received=None))


@pytest.mark.parametrize('parent, sql', [
    ('person', "DELETE FROM public.people WHERE id=CAST(:person AS uuid)"),
    ('connection', "DELETE FROM public.integrations WHERE id=CAST(:integration AS uuid)"),
])
async def test_dates_disappear_with_the_person_or_the_connection(pg_engine, mail, parent, sql):
    await save(pg_engine, row(mail))
    async with pg_engine.begin() as conn:
        await conn.execute(text(sql), mail)
        assert await conn.scalar(text('SELECT count(*) FROM public.email_contacts WHERE user_id=CAST(:owner AS uuid)'), mail) == 0


async def test_closing_the_account_hides_the_dates(pg_engine, mail):
    await save(pg_engine, row(mail))
    async with pg_engine.begin() as conn:
        await conn.execute(text('INSERT INTO public.account_closures(user_id) VALUES(CAST(:owner AS uuid))'), mail)
    async with pg_engine.begin() as conn:
        await identity(conn, mail['owner'])
        assert await conn.scalar(text('SELECT count(*) FROM public.email_contacts'), {}) == 0
