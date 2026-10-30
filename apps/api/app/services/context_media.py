"""Private, bounded, re-encoded photos; original bytes and EXIF are never persisted."""
import io
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select

from app.core.errors import ConflictError, NotFoundError
from app.integrations.storage_client import StorageService
from app.models.entities import ContextMedia, JobRecord
from app.services.context_events import erase_media, get_event


def compress_photo(content):
    if not content or len(content) > 2 * 1024**2:
        raise ConflictError('Choose a compressed photo up to 2 MB.')
    try:
        with Image.open(io.BytesIO(content)) as original:
            if original.format not in {'JPEG', 'PNG', 'WEBP'} or original.width * original.height > 16000000:
                raise ValueError('Unsupported image')
            original.load()
            oriented = ImageOps.exif_transpose(original).convert('RGB')
            # Fresh pixel container has no metadata (including EXIF/XMP/ICC).
            clean = Image.new('RGB', oriented.size)
            clean.paste(oriented)
            clean.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            def encode(image, target):
                for quality in (84, 74, 64, 54):
                    output = io.BytesIO()
                    image.save(output, format='WEBP', quality=quality, method=4)
                    if output.tell() <= target:
                        break
                return output.getvalue()
            photo = encode(clean, 500 * 1024)
            dimensions = clean.size
            clean.thumbnail((320, 320), Image.Resampling.LANCZOS)
            thumb = encode(clean, 50 * 1024)
            return photo, thumb, dimensions
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ConflictError('Could not decode this image safely. Type the details or use a smaller JPG, PNG or WebP.') from exc


async def upload_media(db, owner, draft_id, request_id, kind, content):
    draft = (await db.execute(select(JobRecord).where(JobRecord.user_id == owner,
        JobRecord.id == str(draft_id), JobRecord.job_type == 'capture_draft').with_for_update())).scalar_one_or_none()
    if not draft:
        raise NotFoundError('Capture draft not available.')
    existing = (await db.execute(select(ContextMedia).where(ContextMedia.user_id == owner,
        ContextMedia.request_id == str(request_id)))).scalar_one_or_none()
    if existing:
        if str(existing.draft_id) != str(draft_id) or existing.kind != kind:
            raise ConflictError('This upload identifier belongs to a different photo.')
        return {'id': str(existing.id), 'kind': existing.kind}
    if draft.status != 'awaiting_confirmation':
        raise ConflictError('This capture is already saved.')
    rows = (await db.execute(select(ContextMedia).where(ContextMedia.user_id == owner,
        ContextMedia.draft_id == str(draft_id)))).scalars().all()
    if len(rows) >= 2:
        raise ConflictError('A capture supports up to two photos. Remove one before adding another.')
    from starlette.concurrency import run_in_threadpool
    photo, thumb, (width, height) = await run_in_threadpool(compress_photo, content)
    storage = StorageService()
    uploaded = []
    try:
        main = await storage.save_upload(owner, 'context.webp', photo, 'image/webp')
        uploaded.append(main[4])
        small = await storage.save_upload(owner, 'thumbnail.webp', thumb, 'image/webp')
        uploaded.append(small[4])
        row = ContextMedia(user_id=owner, draft_id=str(draft_id), request_id=str(request_id), kind=kind,
            storage_path=main[4], thumbnail_path=small[4], mime_type='image/webp', size_bytes=len(photo),
            thumbnail_bytes=len(thumb), width=width, height=height, content_hash=main[3])
        db.add(row)
        await db.commit()
        return {'id': str(row.id), 'kind': kind}
    except Exception:
        await db.rollback()
        # Persist compensating deletion before attempting any external cleanup. If the
        # database itself is unavailable, account closure still sweeps the owner prefix.
        for path in uploaded:
            db.add(JobRecord(user_id=owner, job_type='storage_delete', status='pending',
                result_payload={'bucket': storage.bucket_name, 'path': path}))
        await db.commit()
        raise


async def media_record(db, owner, identity):
    row = (await db.execute(select(ContextMedia).where(ContextMedia.user_id == owner,
        ContextMedia.id == str(identity)))).scalar_one_or_none()
    if not row:
        raise NotFoundError('Photo is not available.')
    if row.event_id:
        await get_event(db, owner, row.event_id)
    return row


async def expire_draft_media(db):
    """Called by the existing queue worker; abandoned uploads expire after one day."""
    rows = (await db.execute(select(ContextMedia).where(ContextMedia.event_id.is_(None),
        ContextMedia.created_at < datetime.now(timezone.utc) - timedelta(days=1))
        .limit(50).with_for_update(skip_locked=True))).scalars().all()
    for row in rows:
        erase_media(db, row)
        await db.delete(row)
