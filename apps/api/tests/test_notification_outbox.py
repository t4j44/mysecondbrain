import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import encrypt_token
from app.integrations.storage_client import StorageService
from app.models.assistant import AssistantPreferences, MessagingConnection, NotificationOutbox
from app.models.entities import Commitment
from app.schemas.commitment_actions import CommitmentActionInput
from app.services import notification_outbox as outbox
from app.services.account import close_account, portable_export, request_closure
from app.services.assistant_connections import identity_hash, revoke
from app.services.commitment_actions import act
from tests.conftest import TestingSessionLocal

NOW = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, 'ASSISTANT_OUTBOX_ENABLED', True)
    monkeypatch.setattr(outbox, 'linking_available', lambda: True)


async def seed(db, owner):
    preferences = AssistantPreferences(user_id=owner, timezone='Asia/Dhaka', quiet_enabled=False,
        telegram_enabled=True, consent_at=NOW, daily_cap=1)
    synthetic_id = str(1 + uuid4().int % (2**51))
    connection = MessagingConnection(user_id=owner, status='active', linked_at=NOW,
        external_chat_hash=identity_hash('chat', synthetic_id), external_user_hash=identity_hash('user', synthetic_id),
        encrypted_chat_id=encrypt_token(synthetic_id), encrypted_user_id=encrypt_token(synthetic_id))
    commitment = Commitment(user_id=owner, description='Synthetic check-in', status='snoozed',
        reminder_at=NOW, source_timezone='Asia/Dhaka')
    db.add_all([preferences, connection, commitment])
    await db.flush()
    row = await outbox.enqueue_check_in(db, owner, commitment)
    await db.commit()
    return row, commitment, preferences, connection


@pytest.mark.parametrize('stamp,start,end,expected', [
    ('2026-03-08T06:45:00+00:00', 60, 150, '2026-03-08T07:00:00+00:00'),
    ('2026-11-01T05:15:00+00:00', 60, 90, '2026-11-01T05:30:00+00:00'),
    ('2026-11-01T06:15:00+00:00', 60, 90, '2026-11-01T06:30:00+00:00'),
    ('2026-11-03T04:30:00+00:00', 1320, 480, '2026-11-03T13:00:00+00:00'),
    ('2026-11-03T15:00:00+00:00', 1320, 480, '2026-11-03T15:00:00+00:00'),
])
def test_quiet_hours_follow_real_instants_across_dst(stamp, start, end, expected):
    preferences = SimpleNamespace(timezone='America/New_York', quiet_enabled=True,
        quiet_start_minute=start, quiet_end_minute=end)
    assert outbox.next_allowed_time(datetime.fromisoformat(stamp), preferences).isoformat() == expected


async def test_default_off_and_schedule_dedup(test_user_id, enabled, monkeypatch):
    async with TestingSessionLocal() as db:
        row, commitment, _, _ = await seed(db, test_user_id)
        assert (await outbox.enqueue_check_in(db, test_user_id, commitment)).id == row.id
        monkeypatch.setattr(settings, 'ASSISTANT_OUTBOX_ENABLED', False)
        assert await outbox.claim(db, test_user_id, row.id, clock=NOW) is None
        assert await outbox.enqueue_check_in(db, test_user_id, commitment) is None


async def test_ancient_check_in_expires_without_catch_up_send(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        row, _, _, _ = await seed(db, test_user_id)
        assert await outbox.claim(db, test_user_id, row.id, clock=NOW + timedelta(days=2)) is None
        assert row.status == 'cancelled' and row.error_code == 'CHECK_IN_EXPIRED'


async def test_action_transaction_enqueues_once_and_done_cancels_it(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        _, commitment, _, _ = await seed(db, test_user_id)
        request = CommitmentActionInput(request_id=uuid4(), expected_revision=commitment.revision,
            action='snooze', snoozed_until=datetime.now(timezone.utc) + timedelta(days=2), timezone='UTC')
        result = await act(db, test_user_id, commitment.id, request)
        await db.commit()
        assert await act(db, test_user_id, commitment.id, request) == result
        pending = (await db.scalars(select(NotificationOutbox).where(NotificationOutbox.status == 'queued'))).all()
        assert len(pending) == 1 and pending[0].commitment_revision == result['commitment']['revision']
        await act(db, test_user_id, commitment.id, CommitmentActionInput(request_id=uuid4(),
            expected_revision=result['commitment']['revision'], action='done'))
        await db.commit()
        assert pending[0].status == 'cancelled'


async def test_operational_lease_is_not_in_portable_export(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        row, _, _, _ = await seed(db, test_user_id)
        await outbox.claim(db, test_user_id, row.id, clock=NOW)
        await db.commit()
        with zipfile.ZipFile(io.BytesIO(await portable_export(db, test_user_id))) as archive:
            tables = json.loads(archive.read('data.json'))['tables']
            assert 'notification_outbox' not in tables
            assert len(tables['commitments']) == 1


async def test_quiet_deferral_and_lease_reserves_daily_capacity(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        first, _, preferences, connection = await seed(db, test_user_id)
        preferences.quiet_enabled = True
        preferences.quiet_start_minute, preferences.quiet_end_minute = 17 * 60, 19 * 60
        await db.commit()
        assert await outbox.claim(db, test_user_id, first.id, clock=NOW) is None
        assert first.available_at == NOW + timedelta(hours=1)
        preferences.quiet_enabled = False
        first.available_at = NOW
        other = Commitment(user_id=test_user_id, description='Second', status='snoozed', reminder_at=NOW, source_timezone='UTC')
        db.add(other)
        await db.flush()
        second = await outbox.enqueue_check_in(db, test_user_id, other)
        await db.commit()
        assert await outbox.claim(db, test_user_id, first.id, clock=NOW)
        await db.commit()
        assert await outbox.claim(db, test_user_id, second.id, clock=NOW) is None
        assert second.status == 'queued'


@pytest.mark.parametrize('changed', ['revision', 'completed', 'connection', 'preferences', 'consent'])
async def test_stale_or_revoked_context_cannot_dispatch(test_user_id, enabled, changed):
    async with TestingSessionLocal() as db:
        row, commitment, preferences, connection = await seed(db, test_user_id)
        token = await outbox.claim(db, test_user_id, row.id, clock=NOW)
        await db.commit()
        if changed == 'revision':
            commitment.description = 'Changed'
        elif changed == 'completed':
            commitment.status = 'completed'
        elif changed == 'connection':
            connection.revision += 1
        elif changed == 'preferences':
            preferences.version += 1
        else:
            preferences.telegram_enabled = False
        await db.commit()
        assert not await outbox.begin_dispatch(db, test_user_id, row.id, token, clock=NOW)
        assert row.status == 'cancelled'


async def test_worker_crash_before_dispatch_is_retryable_but_after_is_uncertain(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        row, _, _, _ = await seed(db, test_user_id)
        old_token = await outbox.claim(db, test_user_id, row.id, clock=NOW)
        await db.commit()
        later = NOW + timedelta(minutes=6)
        assert await outbox.recover_expired(db, test_user_id, clock=later) == 1
        assert row.status == 'queued'
        await db.commit()
        token = await outbox.claim(db, test_user_id, row.id, clock=later)
        assert token != old_token
        assert not await outbox.begin_dispatch(db, test_user_id, row.id, old_token, clock=later)
        assert await outbox.begin_dispatch(db, test_user_id, row.id, token, clock=later)
        await db.commit()
        assert await outbox.recover_expired(db, test_user_id, clock=later + timedelta(minutes=6)) == 1
        assert row.status == 'uncertain'
        assert await outbox.claim(db, test_user_id, row.id, clock=later + timedelta(minutes=7)) is None
        assert not await outbox.settle(db, test_user_id, row.id, token, 'delivered', provider_message_id='123')


async def test_delivery_needs_matching_lease_and_provider_id(test_user_id, other_user_id, enabled):
    async with TestingSessionLocal() as db:
        row, _, _, _ = await seed(db, test_user_id)
        assert await outbox.claim(db, other_user_id, row.id, clock=NOW) is None
        token = await outbox.claim(db, test_user_id, row.id, clock=NOW)
        assert await outbox.begin_dispatch(db, test_user_id, row.id, token, clock=NOW)
        with pytest.raises(ValueError):
            await outbox.settle(db, test_user_id, row.id, token, 'delivered')
        assert not await outbox.settle(db, test_user_id, row.id, 'wrong-token', 'uncertain')
        assert await outbox.settle(db, test_user_id, row.id, token, 'delivered', provider_message_id='123', clock=NOW)
        assert row.status == 'delivered' and row.delivered_at == NOW
        assert not await outbox.settle(db, test_user_id, row.id, token, 'uncertain')


async def test_revoke_cancels_pending_and_erasure_preserves_other_owner(test_user_id, other_user_id, enabled, monkeypatch):
    monkeypatch.setattr(StorageService, 'delete_owner_files', AsyncMock(return_value=0))
    monkeypatch.setattr('app.services.account.delete_auth_user', AsyncMock())
    async with TestingSessionLocal() as db:
        own, _, _, _ = await seed(db, test_user_id)
        await seed(db, other_user_id)
        await outbox.claim(db, test_user_id, own.id, clock=NOW)
        await revoke(db, test_user_id)
        await db.commit()
        assert own.status == 'cancelled'
    await request_closure(test_user_id)
    await close_account(test_user_id)
    async with TestingSessionLocal() as db:
        remaining = (await db.scalars(select(NotificationOutbox))).all()
        assert len(remaining) == 1 and str(remaining[0].user_id) == other_user_id
