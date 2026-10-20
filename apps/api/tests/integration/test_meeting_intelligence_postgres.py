"""Real authenticated-role RLS and simultaneous usage reservations; never service-role proof."""
import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.errors import AppError
from app.db.rls import identity_statements
from app.models.meeting_intelligence import MeetingCapture, UsageCounter
from app.services.meeting_usage import charge, month_start
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]


async def identity(db, owner):
    for sql, params in identity_statements(owner):
        await db.execute(text(sql), params)


@pytest.fixture
async def meeting_fixture(pg_engine):
    ids = {key: str(uuid4()) for key in ('owner', 'other', 'meeting', 'second')}
    async with pg_engine.begin() as conn:
        for owner in (ids['owner'], ids['other']):
            await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'), {'id':owner,'email':owner+'@meeting.test'})
        for key in ('meeting','second'):
            await conn.execute(text("INSERT INTO public.meetings(id,user_id,title,start_time,end_time) VALUES(CAST(:id AS uuid),CAST(:owner AS uuid),'Synthetic',now(),now())"), {'id':ids[key],'owner':ids['owner']})
            await conn.execute(text("INSERT INTO public.meeting_captures(meeting_id,user_id,request_id,period_start,consent_at,data_mode) VALUES(CAST(:id AS uuid),CAST(:owner AS uuid),gen_random_uuid(),date_trunc('month',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC',now(),'free_redacted')"), {'id':ids[key],'owner':ids['owner']})
    try:
        yield ids
    finally:
        async with pg_engine.begin() as conn:
            for owner in (ids['owner'],ids['other']):
                await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:owner AS uuid)'), {'owner':owner})


async def test_audio_transcript_and_counter_owner_rls(pg_engine,meeting_fixture):
    ids=meeting_fixture
    for owner, expected in ((ids['owner'],2),(ids['other'],0)):
        async with pg_engine.begin() as conn:
            await identity(conn,owner)
            assert await conn.scalar(text('SELECT count(*) FROM public.meeting_captures WHERE user_id=CAST(:owner AS uuid)'),ids)==expected
            assert await conn.scalar(text('SELECT count(*) FROM public.meetings WHERE user_id=CAST(:owner AS uuid)'),ids)==expected
            assert await conn.scalar(text('SELECT current_user'))=='authenticated'
            if owner==ids['other']:
                assert (await conn.execute(text("UPDATE public.meeting_captures SET intelligence='{}' WHERE meeting_id=CAST(:meeting AS uuid)"),ids)).rowcount==0


async def test_concurrent_reservations_cannot_exceed_18000(pg_engine,meeting_fixture):
    ids=meeting_fixture
    factory=async_sessionmaker(pg_engine,expire_on_commit=False)
    async def reserve(meeting_id):
        async with factory() as db:
            await identity(db,ids['owner'])
            assert await db.scalar(text('SELECT current_user'))=='authenticated'
            row=await db.scalar(select(MeetingCapture).where(MeetingCapture.meeting_id==meeting_id).with_for_update())
            try:
                await charge(db,row,10000)
                await db.commit()
                return True
            except AppError as error:
                await db.rollback()
                assert error.code=='MEETING_QUOTA_EXCEEDED'
                return False
    assert sorted(await asyncio.gather(reserve(ids['meeting']),reserve(ids['second'])))==[False,True]
    async with factory() as db:
        await identity(db,ids['owner'])
        assert await db.scalar(select(UsageCounter.quantity).where(UsageCounter.user_id==ids['owner'],UsageCounter.period_start==month_start()))==10000


async def test_quota_changes_are_not_exposed_through_postgrest_login(pg_engine,meeting_fixture):
    from sqlalchemy.exc import DBAPIError
    # A separate NOINHERIT login emulates PostgREST, then SET ROLE authenticates
    # the real owner. No service-role or application-login access proves this gate.
    role = 'meeting_test_browser_' + uuid4().hex
    async with pg_engine.begin() as conn:
        await conn.execute(text(f'CREATE ROLE {role} NOLOGIN NOINHERIT'))
        await conn.execute(text(f'GRANT authenticated TO {role}'))
        try:
            await conn.execute(text(f'SET LOCAL SESSION AUTHORIZATION {role}'))
            await identity(conn,meeting_fixture['owner'])
            assert await conn.scalar(text('SELECT current_user')) == 'authenticated'
            assert await conn.scalar(text('SELECT public.meeting_server_connection()')) is False
            assert await conn.scalar(text('SELECT count(*) FROM public.meeting_captures WHERE user_id=CAST(:owner AS uuid)'),meeting_fixture) == 2
            changed = await conn.execute(text("UPDATE public.meeting_captures SET state='completed' WHERE user_id=CAST(:owner AS uuid)"),meeting_fixture)
            assert changed.rowcount == 0
            with pytest.raises(DBAPIError):
                async with conn.begin_nested():
                    await conn.execute(text("INSERT INTO public.usage_counters(user_id,metric,period_start,quantity) VALUES(CAST(:owner AS uuid),'forged',now(),0)"),meeting_fixture)
        finally:
            await conn.execute(text('RESET ROLE'))
            await conn.execute(text('RESET SESSION AUTHORIZATION'))
            await conn.execute(text(f'DROP ROLE {role}'))


async def test_concurrent_user_note_edits_preserve_one_winner_and_owner_rls(pg_engine, meeting_fixture):
    from app.core.errors import ConflictError, NotFoundError
    from app.schemas.meeting_intelligence import NotesUpdate
    from app.services.meeting_intelligence import capture_for
    from app.services.meeting_outputs import notes_view, save_notes
    ids = meeting_fixture
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async def edit(markdown):
        async with factory() as db:
            await identity(db, ids['owner'])
            try:
                meeting, _ = await capture_for(db, ids['owner'], ids['meeting'], lock=True)
                await save_notes(db, meeting, NotesUpdate(expected_version=0, markdown=markdown))
                await db.commit()
                return True
            except ConflictError:
                await db.rollback()
                return False
    assert sorted(await asyncio.gather(edit('First synthetic edit'), edit('Second synthetic edit'))) == [False, True]
    async with factory() as db:
        await identity(db, ids['owner'])
        meeting, _ = await capture_for(db, ids['owner'], ids['meeting'])
        notes = notes_view(meeting)
        assert notes['version'] == 1 and len(notes['revisions']) == 1
        assert notes['markdown'] in {'First synthetic edit', 'Second synthetic edit'}
    async with factory() as db:
        await identity(db, ids['other'])
        with pytest.raises(NotFoundError):
            await capture_for(db, ids['other'], ids['meeting'], lock=True)


async def test_concurrent_confirmation_creates_one_receipt_and_temporal_graph(pg_engine, meeting_fixture):
    import json

    from app.models.entities import EntityEdge
    from app.schemas.meeting_intelligence import ConfirmIntelligence
    from app.services.meeting_intelligence import confirm_intelligence
    ids = meeting_fixture
    async with pg_engine.begin() as db:
        await db.execute(text("""UPDATE public.meeting_captures SET state='awaiting_review',
            transcript_segments=CAST(:segments AS jsonb), intelligence=CAST(:intelligence AS jsonb)
            WHERE meeting_id=CAST(:meeting AS uuid)"""), {**ids,
                'segments': json.dumps([{'segment_id':'c0:0','chunk_index':0,'speaker_local_id':'c0:unknown',
                    'start_offset':0,'end_offset':4,'text':'We decided to test the beta.'}]),
                'intelligence': json.dumps({'summary':'Beta test decision','decisions':[{'description':'Test the beta',
                    'evidence_text':'We decided to test the beta.','confidence':.9}]})})
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async def confirm_once():
        async with factory() as db:
            await identity(db, ids['owner'])
            receipt = await confirm_intelligence(db, ids['owner'], ids['meeting'], ConfirmIntelligence(confirmed=True))
            await db.commit()
            return receipt
    first, second = await asyncio.gather(confirm_once(), confirm_once())
    assert first == second and len(first['decisions']) == 1
    async with factory() as db:
        await identity(db, ids['owner'])
        edges = (await db.scalars(select(EntityEdge).where(EntityEdge.source_entity_type == 'meeting',
            EntityEdge.source_entity_id == ids['meeting']))).all()
        assert len(edges) == 1 and edges[0].relationship_type == 'produced'
        assert edges[0].valid_from and edges[0].source_event_id
