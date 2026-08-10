from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode, IntegrationError
from app.core.security import encrypt_token
from app.models.entities import Integration, JobRecord
from app.repositories.integrations import IntegrationRepository, JobRepository


class GoogleIntegrationService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = IntegrationRepository()

    async def connect_oauth_callback(self, code: str, state: Optional[str]) -> Dict[str, Any]:
        if not code:
            raise IntegrationError(
                "Missing OAuth verification code.", code=ErrorCode.VALIDATION_FAILED
            )

        simulated_refresh_token = f"1//0e_simulated_refresh_token_for_{self.user_id}_{code[:10]}"
        encrypted = encrypt_token(simulated_refresh_token)

        existing = await self.repo.get_by_provider(self.db, self.user_id, "google")
        if existing:
            existing.encrypted_tokens = encrypted
            existing.is_connected = True
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
        else:
            new_integration = Integration(
                user_id=self.user_id,
                provider_name="google",
                account_identifier="founder.root@tajssecondbrain.ai",
                encrypted_tokens=encrypted,
                scopes=[
                    "https://www.googleapis.com/auth/drive.file",
                    "https://www.googleapis.com/auth/calendar",
                ],
                is_connected=True,
            )
            self.db.add(new_integration)
            await self.db.flush()

        return {
            "status": "connected",
            "provider": "google",
            "account_identifier": "founder.root@tajssecondbrain.ai",
            "scopes_granted": ["drive.file", "calendar"],
            "message": "Google integration connected and credentials encrypted successfully.",
        }

    async def disconnect_provider(self, provider_name: str) -> bool:
        integration = await self.repo.get_by_provider(self.db, self.user_id, provider_name)
        if not integration:
            return False
        integration.encrypted_tokens = None
        integration.is_connected = False
        await self.db.flush()
        return True

    async def trigger_drive_sync_job(
        self, folder_id: Optional[str], sync_mode: str = "one_way"
    ) -> JobRecord:
        integration = await self.repo.get_by_provider(self.db, self.user_id, "google")
        if not integration or not integration.is_connected:
            raise IntegrationError(
                "Google Drive integration is not connected.",
                code=ErrorCode.INTEGRATION_NOT_CONNECTED,
            )

        job_repo = JobRepository()
        job = await job_repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "job_type": "sync_google_drive",
                "status": "pending",
                "result_payload": {
                    "folder_id": folder_id or "default_brain_root",
                    "sync_mode": sync_mode,
                },
            },
        )
        return job

    async def trigger_calendar_sync_job(self, calendar_id: str = "primary") -> JobRecord:
        integration = await self.repo.get_by_provider(self.db, self.user_id, "google")
        if not integration or not integration.is_connected:
            raise IntegrationError(
                "Google Calendar integration is not connected.",
                code=ErrorCode.INTEGRATION_NOT_CONNECTED,
            )

        job_repo = JobRepository()
        job = await job_repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "job_type": "sync_google_calendar",
                "status": "pending",
                "result_payload": {"calendar_id": calendar_id},
            },
        )
        return job
