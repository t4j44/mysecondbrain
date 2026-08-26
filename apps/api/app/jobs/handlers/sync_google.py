from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.errors import IntegrationError
from app.core.logging import logger


async def execute_google_sync_handler(
    db: AsyncSession, user_id: str, payload: dict, job_type: str = "sync_google_drive"
) -> dict:
    """
    Google sync jobs are deferred (Prompt 7).

    G0: never invent sync success metrics or mark jobs completed.
    """
    _ = (db, user_id, payload)
    logger.warning(
        "Google sync job %s refused for user %s — integration not implemented.",
        job_type,
        user_id,
    )
    raise IntegrationError(
        "Google Workspace sync is not implemented. Refusing simulated success metrics.",
        code=ErrorCode.INTEGRATION_NOT_IMPLEMENTED,
        status_code=501,
        details={"job_type": job_type},
    )
