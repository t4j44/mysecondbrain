import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Profile
from app.repositories.profiles import ProfileRepository
from app.utils.identifiers import generate_uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MCPCredentialRepository:
    """
    Repository managing MCP API credentials stored within Profile.settings["mcp_credentials"].
    Enforces strict security principles:
      - API keys generated with secure randomness and prefix 'sb_mcp_'
      - Salted SHA-256 cryptographic hashing
      - Constant-time secret comparison via hmac.compare_digest
      - Complete separation of plaintext generation from persisted records
    """

    def __init__(self, profile_repo: Optional[ProfileRepository] = None):
        self.profile_repo = profile_repo or ProfileRepository()

    def _generate_api_key_and_hash(self) -> Tuple[str, str, str, str]:
        """Returns (plaintext_key, prefix, salt, key_hash)."""
        raw_token = secrets.token_urlsafe(32)
        plaintext_key = f"sb_mcp_{raw_token}"
        prefix = plaintext_key[:12]
        salt = secrets.token_hex(16)
        payload = (salt + plaintext_key).encode("utf-8")
        key_hash = hashlib.sha256(payload).hexdigest()
        return plaintext_key, prefix, salt, key_hash

    def _hash_key_with_salt(self, plain_key: str, salt: str) -> str:
        payload = (salt + plain_key).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _get_settings_dict(self, profile: Optional[Profile]) -> Dict[str, Any]:
        if not profile or not profile.settings:
            return {}
        if isinstance(profile.settings, dict):
            return dict(profile.settings)
        if isinstance(profile.settings, str):
            import json

            try:
                parsed = json.loads(profile.settings)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    async def _get_profile_and_credentials(
        self, db: AsyncSession, user_id: str
    ) -> Tuple[Optional[Profile], List[Dict[str, Any]]]:
        profile = await self.profile_repo.get_by_user_id(db, user_id)
        if not profile:
            return None, []
        settings = self._get_settings_dict(profile)
        creds = list(settings.get("mcp_credentials", []))
        return profile, creds

    async def _save_credentials(
        self, db: AsyncSession, profile: Profile, creds: List[Dict[str, Any]]
    ) -> None:
        from sqlalchemy.orm.attributes import flag_modified

        new_settings = self._get_settings_dict(profile)
        new_settings["mcp_credentials"] = creds
        profile.settings = new_settings
        flag_modified(profile, "settings")
        await db.flush()
        await db.refresh(profile)

    def _sanitize_credential_meta(self, cred: Dict[str, Any]) -> Dict[str, Any]:
        """Strip cryptographic secret material before returning to callers or API endpoints."""
        sanitized = dict(cred)
        sanitized.pop("key_hash", None)
        sanitized.pop("salt", None)
        return sanitized

    async def list_credentials(self, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        _, creds = await self._get_profile_and_credentials(db, user_id)
        return [self._sanitize_credential_meta(c) for c in creds]

    async def get_credential_by_id(
        self, db: AsyncSession, user_id: str, credential_id: str
    ) -> Optional[Dict[str, Any]]:
        _, creds = await self._get_profile_and_credentials(db, user_id)
        for c in creds:
            if c.get("credential_id") == credential_id:
                return self._sanitize_credential_meta(c)
        return None

    async def create_credential(
        self,
        db: AsyncSession,
        user_id: str,
        client_name: str,
        client_type: str = "stdio",
        scopes: Optional[List[str]] = None,
        expires_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        profile, creds = await self._get_profile_and_credentials(db, user_id)
        if not profile:
            # Auto-create basic profile if absent during test environments or initialization
            profile = await self.profile_repo.create_or_update(
                db, user_id=user_id, email=f"{user_id}@founder.local"
            )
            creds = []

        plaintext_key, prefix, salt, key_hash = self._generate_api_key_and_hash()
        cred_record = {
            "credential_id": generate_uuid(),
            "user_id": user_id,
            "client_name": client_name,
            "client_type": client_type,
            "scopes": scopes or ["mcp:read"],
            "key_prefix": prefix,
            "key_hash": key_hash,
            "salt": salt,
            "status": "active",
            "created_at": utc_now_iso(),
            "last_used_at": None,
            "expires_at": expires_at,
            "revoked_at": None,
        }
        creds.append(cred_record)
        await self._save_credentials(db, profile, creds)

        result = self._sanitize_credential_meta(cred_record)
        result["plaintext_key"] = plaintext_key  # returned exactly once upon creation
        return result

    async def rotate_credential(
        self, db: AsyncSession, user_id: str, credential_id: str
    ) -> Optional[Dict[str, Any]]:
        profile, creds = await self._get_profile_and_credentials(db, user_id)
        if not profile:
            return None

        target_idx = None
        for i, c in enumerate(creds):
            if c.get("credential_id") == credential_id:
                target_idx = i
                break
        if target_idx is None:
            return None

        plaintext_key, prefix, salt, key_hash = self._generate_api_key_and_hash()
        creds[target_idx].update(
            {
                "key_prefix": prefix,
                "key_hash": key_hash,
                "salt": salt,
                "status": "active",
                "created_at": utc_now_iso(),
                "last_used_at": None,
                "revoked_at": None,
            }
        )
        await self._save_credentials(db, profile, creds)

        result = self._sanitize_credential_meta(creds[target_idx])
        result["plaintext_key"] = plaintext_key
        return result

    async def revoke_credential(
        self, db: AsyncSession, user_id: str, credential_id: str
    ) -> Optional[Dict[str, Any]]:
        profile, creds = await self._get_profile_and_credentials(db, user_id)
        if not profile:
            return None

        target_idx = None
        for i, c in enumerate(creds):
            if c.get("credential_id") == credential_id:
                target_idx = i
                break
        if target_idx is None:
            return None

        creds[target_idx]["status"] = "revoked"
        creds[target_idx]["revoked_at"] = utc_now_iso()
        await self._save_credentials(db, profile, creds)
        return self._sanitize_credential_meta(creds[target_idx])

    async def delete_credential(self, db: AsyncSession, user_id: str, credential_id: str) -> bool:
        profile, creds = await self._get_profile_and_credentials(db, user_id)
        if not profile:
            return False

        initial_len = len(creds)
        new_creds = [c for c in creds if c.get("credential_id") != credential_id]
        if len(new_creds) == initial_len:
            return False

        await self._save_credentials(db, profile, new_creds)
        return True

    async def verify_api_key(self, db: AsyncSession, plain_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify an MCP API key in real-time during tool/resource requests.
        Scans profiles with configured MCP credentials, matches prefix, performs constant-time
        HMAC comparison, verifies expiry and revocation status, and returns verified session context.
        """
        if not plain_key or not plain_key.startswith("sb_mcp_") or len(plain_key) < 16:
            return None
        prefix = plain_key[:12]

        stmt = select(Profile)
        result = await db.execute(stmt)
        profiles = list(result.scalars().all())

        for profile in profiles:
            settings = self._get_settings_dict(profile)
            creds = settings.get("mcp_credentials", [])
            for cred in creds:
                if cred.get("key_prefix") != prefix:
                    continue

                if cred.get("status") != "active":
                    continue

                # Check expiration timestamp if configured
                expires_at_str = cred.get("expires_at")
                if expires_at_str:
                    try:
                        exp = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                        if datetime.now(timezone.utc) >= exp:
                            continue
                    except Exception:
                        pass

                stored_hash = cred.get("key_hash", "")
                salt = cred.get("salt", "")
                computed_hash = self._hash_key_with_salt(plain_key, salt)

                # Constant-time comparison to prevent timing leaks
                if hmac.compare_digest(stored_hash, computed_hash):
                    # Update last_used_at timestamp
                    cred["last_used_at"] = utc_now_iso()
                    await self._save_credentials(db, profile, creds)
                    return {
                        "user_id": str(profile.id),
                        "credential_id": cred.get("credential_id"),
                        "client_name": cred.get("client_name"),
                        "scopes": cred.get("scopes", ["mcp:read"]),
                        "status": cred.get("status", "active"),
                    }

        return None
