from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.errors import IntegrationError
from app.models.entities import JobRecord
from app.repositories.integrations import IntegrationRepository

_GOOGLE_DEFERRED_MESSAGE = (
    "Google Workspace OAuth and sync are not implemented (v0.1 deferred). "
    "The API will not report connected or invent sync metrics."
)


class GoogleIntegrationService:
    """Google integration surface preserved for Prompt 7 — fail-closed in G0."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = IntegrationRepository()

    async def connect_oauth_callback(self, code: str, state: Optional[str]) -> Dict[str, Any]:
        if not code:
            raise IntegrationError(
                "Missing OAuth verification code.", code=ErrorCode.VALIDATION_FAILED
            )

        # G0: never invent tokens, identities, or is_connected=True.
        return {
            "status": "not_implemented",
            "provider": "google",
            "account_identifier": None,
            "scopes_granted": [],
            "message": _GOOGLE_DEFERRED_MESSAGE,
            "code": ErrorCode.INTEGRATION_NOT_IMPLEMENTED.value,
        }

    async def disconnect_provider(self, provider_name: str) -> bool:
        integration = await self.repo.get_by_provider(self.db, self.user_id, provider_name)
        if not integration:
            return False
        integration.encrypted_tokens = None
        integration.is_connected = False
        integration.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def trigger_drive_sync_job(
        self, folder_id: Optional[str], sync_mode: str = "one_way"
    ) -> JobRecord:
        raise IntegrationError(
            _GOOGLE_DEFERRED_MESSAGE,
            code=ErrorCode.INTEGRATION_NOT_IMPLEMENTED,
            status_code=501,
            details={"provider": "google", "operation": "sync_google_drive"},
        )

    async def trigger_calendar_sync_job(self, calendar_id: str = "primary") -> JobRecord:
        raise IntegrationError(
            _GOOGLE_DEFERRED_MESSAGE,
            code=ErrorCode.INTEGRATION_NOT_IMPLEMENTED,
            status_code=501,
            details={"provider": "google", "operation": "sync_google_calendar"},
        )
