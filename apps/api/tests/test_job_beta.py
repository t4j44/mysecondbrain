from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.jobs.runner import JobRunner
from app.models.entities import ExportRecord, JobRecord
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_failed_export_retries_have_truthful_terminal_status(test_user_id, monkeypatch):
    monkeypatch.setattr(JobRunner, '_execute_payload', AsyncMock(side_effect=RuntimeError('private failure text')))
    async with TestingSessionLocal() as db:
        export = ExportRecord(user_id=test_user_id, status='pending')
        db.add(export)
        await db.flush()
        job = JobRecord(user_id=test_user_id, job_type='export_markdown', status='pending',
                        result_payload={'export_id': str(export.id)})
        db.add(job)
        await db.commit()
        identity = str(job.id)
    for attempt in range(1, 4):
        await JobRunner.run_job_by_id(identity)
        async with TestingSessionLocal() as db:
            current = await db.scalar(select(JobRecord).where(JobRecord.id == identity))
            record = await db.get(ExportRecord, export.id)
            assert current.retry_count == attempt
            assert current.status == ('failed' if attempt == 3 else 'pending')
            assert record.status == current.status
            assert 'private failure text' not in current.error_message
    await JobRunner.run_job_by_id(identity)
    assert JobRunner._execute_payload.await_count == 3
