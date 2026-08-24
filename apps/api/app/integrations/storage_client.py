import os
from datetime import datetime, timedelta, timezone
from typing import Tuple
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.utils.files import calculate_checksum, validate_upload_file


class StorageService:
    def __init__(self, bucket_name: str = settings.STORAGE_BUCKET_DOCUMENTS):
        self.bucket_name = bucket_name
        supabase_url = (settings.SUPABASE_URL or "").lower()
        # CI/local often set mock.supabase.co — never treat that as a live Storage host.
        is_mock_host = any(
            marker in supabase_url
            for marker in ("mock.supabase", "example.com", "localhost", "127.0.0.1")
        )
        self.use_supabase = bool(
            settings.SUPABASE_URL and settings.supabase_secret and not is_mock_host
        )
        if settings.is_production() and not self.use_supabase:
            raise RuntimeError(
                "Production document storage requires SUPABASE_URL and "
                "SUPABASE_SECRET_KEY (or legacy SUPABASE_SERVICE_ROLE_KEY)."
            )

        # Local disk is an explicit development fallback only. Production uses
        # private Supabase Storage because Render's filesystem is ephemeral.
        self.base_path = os.path.join(os.getcwd(), ".storage_buckets", bucket_name)
        if not self.use_supabase:
            os.makedirs(self.base_path, exist_ok=True)

    @property
    def _storage_url(self) -> str:
        return f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1"

    @property
    def _service_headers(self) -> dict[str, str]:
        secret_key = settings.supabase_secret
        return {
            "apikey": secret_key,
            "Authorization": f"Bearer {secret_key}",
        }

    async def save_upload(
        self, user_id: str, raw_filename: str, content: bytes, content_type: str
    ) -> Tuple[str, str, int, str, str]:
        """
        Validate file safety, compute SHA256 checksum, persist to user isolation path, and return attributes.
        Returns: sanitized_filename, ext, size_bytes, checksum, storage_path
        """
        sanitized, ext, valid_mime, size = validate_upload_file(raw_filename, content, content_type)
        checksum = calculate_checksum(content)

        unique_name = f"{checksum[:12]}_{sanitized}"
        relative_path = f"{user_id}/{unique_name}"

        if self.use_supabase:
            object_path = quote(relative_path, safe="/")
            headers = {**self._service_headers, "Content-Type": valid_mime, "x-upsert": "false"}
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._storage_url}/object/{self.bucket_name}/{object_path}",
                    headers=headers,
                    content=content,
                )
            response.raise_for_status()
        else:
            user_dir = os.path.join(self.base_path, user_id)
            os.makedirs(user_dir, exist_ok=True)
            file_path = os.path.join(user_dir, unique_name)
            with open(file_path, "wb") as file_handle:
                file_handle.write(content)

        return sanitized, ext, size, checksum, relative_path

    async def get_signed_url(self, relative_path: str, expires_seconds: int = 3600) -> str:
        """Generate short-lived signed access URL for private attachment reading."""
        if self.use_supabase:
            object_path = quote(relative_path, safe="/")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self._storage_url}/object/sign/{self.bucket_name}/{object_path}",
                    headers=self._service_headers,
                    json={"expiresIn": expires_seconds},
                )
            response.raise_for_status()
            signed_path = response.json()["signedURL"]
            if signed_path.startswith("http"):
                return signed_path
            return f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1{signed_path}"

        expires = (datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)).isoformat()
        return f"{settings.FRONTEND_URL}/api/storage/{self.bucket_name}/{relative_path}?token=sig_{relative_path[:8]}&expires={expires}"

    async def read_file(self, relative_path: str) -> bytes:
        """Read raw bytes of uploaded file from Supabase storage or local directory fallback."""
        if self.use_supabase:
            object_path = quote(relative_path, safe="/")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._storage_url}/object/{self.bucket_name}/{object_path}",
                    headers=self._service_headers,
                )
            response.raise_for_status()
            return response.content

        full_path = os.path.join(self.base_path, relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Storage file not found at: {full_path}")
        with open(full_path, "rb") as f:
            return f.read()

    async def delete_file(self, relative_path: str) -> bool:
        if self.use_supabase:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.request(
                    "DELETE",
                    f"{self._storage_url}/object/{self.bucket_name}",
                    headers=self._service_headers,
                    json={"prefixes": [relative_path]},
                )
            response.raise_for_status()
            return True

        full_path = os.path.join(self.base_path, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
