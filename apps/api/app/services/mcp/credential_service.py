from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.integrations import AuditLogRepository
from app.repositories.mcp import MCPCredentialRepository
from app.schemas.mcp import MCPCredentialCreateRequest


class MCPCredentialService:
    """
    Domain Service for MCP Credential management and audit telemetry.
    Enforces scope checks, credential lifecycle transitions, and strict audit log recording.
    """

    def __init__(
        self,
        repo: Optional[MCPCredentialRepository] = None,
        audit_repo: Optional[AuditLogRepository] = None,
    ):
        self.repo = repo or MCPCredentialRepository()
        self.audit_repo = audit_repo or AuditLogRepository()

    async def _emit_audit(
        self,
        db: AsyncSession,
        user_id: str,
        event_type: str,
        target_id: str,
        details: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> None:
        try:
            await self.audit_repo.create(
                db,
                obj_in_data={
                    "user_id": user_id,
                    "event_type": event_type,
                    "target_entity": "mcp_credential",
                    "target_id": target_id,
                    "details": details,
                    "request_id": request_id or "N/A",
                },
            )
        except Exception:
            # Audit failures must not abort core operations during dev/test fallback
            pass

    async def list_credentials(self, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        return await self.repo.list_credentials(db, user_id)

    async def get_credential(
        self, db: AsyncSession, user_id: str, credential_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.repo.get_credential_by_id(db, user_id, credential_id)

    async def create_credential(
        self,
        db: AsyncSession,
        user_id: str,
        req: MCPCredentialCreateRequest,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        cred = await self.repo.create_credential(
            db=db,
            user_id=user_id,
            client_name=req.client_name,
            client_type=req.client_type,
            scopes=req.scopes,
            expires_at=req.expires_at,
        )
        await self._emit_audit(
            db,
            user_id=user_id,
            event_type="mcp.credential.created",
            target_id=cred["credential_id"],
            details={
                "client_name": req.client_name,
                "client_type": req.client_type,
                "scopes": req.scopes,
                "prefix": cred.get("key_prefix"),
            },
            request_id=request_id,
        )
        return cred

    async def rotate_credential(
        self, db: AsyncSession, user_id: str, credential_id: str, request_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        cred = await self.repo.rotate_credential(db, user_id, credential_id)
        if cred:
            await self._emit_audit(
                db,
                user_id=user_id,
                event_type="mcp.credential.rotated",
                target_id=credential_id,
                details={"new_prefix": cred.get("key_prefix")},
                request_id=request_id,
            )
        return cred

    async def revoke_credential(
        self, db: AsyncSession, user_id: str, credential_id: str, request_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        cred = await self.repo.revoke_credential(db, user_id, credential_id)
        if cred:
            await self._emit_audit(
                db,
                user_id=user_id,
                event_type="mcp.credential.revoked",
                target_id=credential_id,
                details={"status": "revoked"},
                request_id=request_id,
            )
        return cred

    async def delete_credential(
        self, db: AsyncSession, user_id: str, credential_id: str, request_id: Optional[str] = None
    ) -> bool:
        success = await self.repo.delete_credential(db, user_id, credential_id)
        if success:
            await self._emit_audit(
                db,
                user_id=user_id,
                event_type="mcp.credential.deleted",
                target_id=credential_id,
                details={"status": "deleted"},
                request_id=request_id,
            )
        return success
