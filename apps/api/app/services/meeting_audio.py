"""Bounded private storage and server-measured audio. Never trust browser duration."""
import asyncio
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx

from app.core.config import settings
from app.core.errors import AppError, ValidationError
from app.integrations.storage_client import StorageService

MIMES = {'audio/webm': '.webm', 'audio/mpeg': '.mp3', 'audio/mp4': '.m4a',
         'audio/wav': '.wav', 'audio/aac': '.aac', 'audio/ogg': '.ogg',
         'audio/flac': '.flac', 'audio/opus': '.opus'}
ALIASES = {'audio/mp3': 'audio/mpeg', 'audio/x-m4a': 'audio/mp4',
           'audio/m4a': 'audio/mp4', 'audio/x-wav': 'audio/wav', 'audio/wave': 'audio/wav'}


def audio_mime(value: str) -> str:
    value = value.split(';', 1)[0].strip().lower()
    value = ALIASES.get(value, value)
    if value not in MIMES:
        raise ValidationError('Choose an MP3, M4A, WAV, WebM, AAC, OGG, Opus or FLAC recording.')
    return value


class AudioStorage(StorageService):
    def __init__(self):
        super().__init__(settings.MEETING_AUDIO_BUCKET)

    async def authorize(self, owner: str, meeting_id: str, mime: str) -> tuple[str, str | None]:
        path = f'{UUID(owner)}/{UUID(meeting_id)}-{uuid4().hex}{MIMES[audio_mime(mime)]}'
        self._validate_path(path)
        return path, await self.upload_url(path)

    async def upload_url(self, path: str) -> str | None:
        self._validate_path(path)
        if not self.use_supabase:
            return None
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f'{self._storage_url}/object/upload/sign/{self.bucket_name}/{quote(path, safe="/")}',
                headers=self._service_headers, json={})
            response.raise_for_status()
            url = response.json()['url']
            return f'{self._storage_url}{url}'

    async def local_upload(self, path: str, content: bytes):
        if self.use_supabase:
            raise ValidationError('Use the private upload authorization.')
        if not content or len(content) > settings.MEETING_AUDIO_MAX_BYTES:
            raise ValidationError('Recording is empty or too large (maximum 50 MB).')
        target = Path(self._validate_path(path))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(content).digest():
                raise ValidationError('This recording has already been uploaded.')
            return
        target.write_bytes(content)

    async def read_bounded(self, path: str) -> bytes:
        self._validate_path(path)
        if not self.use_supabase:
            target = Path(self._validate_path(path))
            if not target.exists():
                raise ValidationError('Upload the recording first.')
            if target.stat().st_size > settings.MEETING_AUDIO_MAX_BYTES:
                raise ValidationError('Recording is too large (maximum 50 MB).')
            return target.read_bytes()
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream('GET', f'{self._storage_url}/object/{self.bucket_name}/{quote(path, safe="/")}',
                headers=self._service_headers) as response:
                response.raise_for_status()
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > settings.MEETING_AUDIO_MAX_BYTES:
                        raise ValidationError('Recording is too large (maximum 50 MB).')
                return bytes(content)


async def run_audio_tool(*args: str) -> bytes:
    try:
        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise AppError('Audio processing is not configured. Your recording is preserved.',
            code='AUDIO_TOOLS_UNAVAILABLE', status_code=503) from exc
    try:
        async with asyncio.timeout(120):
            output, _ = await process.communicate()
        if process.returncode:
            raise ValidationError('This file could not be read as a recording.')
        return output
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


async def inspect_audio(content: bytes, mime: str) -> int:
    if not content or len(content) > settings.MEETING_AUDIO_MAX_BYTES:
        raise ValidationError('Recording is empty or too large (maximum 50 MB).')
    with tempfile.TemporaryDirectory(prefix='meeting-') as folder:
        source = Path(folder) / ('source' + MIMES[audio_mime(mime)])
        source.write_bytes(content)
        output = await run_audio_tool(settings.MEETING_FFPROBE, '-v', 'error', '-protocol_whitelist', 'file,pipe',
            '-show_entries', 'format=duration:stream=codec_type,duration', '-of', 'json', str(source))
        info = json.loads(output)
        streams = info.get('streams', [])
        if not streams or any(s.get('codec_type') != 'audio' for s in streams):
            raise ValidationError('Choose an audio-only recording.')
        # Container duration is editable input, too. Count decoded samples instead.
        # Streaming avoids holding hours of PCM in memory or trusting a forged header.
        return await measured_seconds(source)


async def measured_seconds(source: Path) -> int:
    try:
        process = await asyncio.create_subprocess_exec(settings.MEETING_FFMPEG,
            '-v', 'error', '-protocol_whitelist', 'file,pipe', '-i', str(source),
            '-map', '0:a:0', '-t', str(settings.MEETING_AUDIO_MONTHLY_LIMIT_SECONDS + 1),
            '-f', 's16le', '-ac', '1', '-ar', '16000', 'pipe:1',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise AppError('Audio processing is not configured. Your recording is preserved.',
            code='AUDIO_TOOLS_UNAVAILABLE', status_code=503) from exc
    total = 0
    try:
        async with asyncio.timeout(120):
            if process.stdout is None:
                raise AppError('Audio processing is not configured.', code='AUDIO_TOOLS_UNAVAILABLE', status_code=503)
            while chunk := await process.stdout.read(65536):
                total += len(chunk)
                if total > settings.MEETING_AUDIO_MONTHLY_LIMIT_SECONDS * 32000:
                    raise ValidationError('Recording is longer than the monthly allowance.')
            await process.wait()
        if process.returncode or total == 0 or total % 2:
            raise ValidationError('This file could not be read as a recording.')
        return (total + 31999) // 32000
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


async def audio_chunks(content: bytes, mime: str, duration: int):
    """Nonoverlapping 29 minute FLAC chunks; speaker ids remain chunk-local."""
    with tempfile.TemporaryDirectory(prefix='meeting-') as folder:
        source = Path(folder) / ('source' + MIMES[audio_mime(mime)])
        source.write_bytes(content)
        for index, start in enumerate(range(0, duration, 1740)):
            target = Path(folder) / f'chunk-{index}.flac'
            await run_audio_tool(settings.MEETING_FFMPEG, '-v', 'error', '-protocol_whitelist', 'file,pipe',
                '-ss', str(start), '-i', str(source), '-t', str(min(1740, duration - start)),
                '-vn', '-ac', '1', '-ar', '16000', '-y', str(target))
            yield index, start, target
