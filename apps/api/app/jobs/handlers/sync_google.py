from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.errors import IntegrationError


async def execute_google_sync_handler(
    db: AsyncSession, user_id: str, payload: dict, job_type: str = "sync_google_drive"
) -> dict:
    """
    Google sync jobs are deferred (Prompt 7).

    G0: never invent sync success metrics or mark jobs completed.
    """
    from app.integrations.google_client import GoogleIntegrationService
    service = GoogleIntegrationService(db, user_id)
    if job_type == "sync_google_drive":
        return await service.export_drive(payload)
    if job_type == "sync_google_calendar":
        return await service.sync_calendar(payload)
    raise IntegrationError("Unknown sync operation.", code=ErrorCode.VALIDATION_FAILED)
