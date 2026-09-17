"""Private, authenticated Markdown exports over current canonical records."""
from sqlalchemy import select

from app.ai.indexing import SOURCES, record_text
from app.core.errors import NotFoundError, ValidationError
from app.integrations.storage_client import StorageService
from app.repositories.integrations import ExportRepository


async def execute_export_handler(db, user_id: str, payload: dict) -> dict:
    export_id = payload.get('export_id')
    if not isinstance(export_id, str):
        raise ValidationError('An export ID is required.')
    record = await ExportRepository().get_by_id(db, user_id, export_id)
    if record is None:
        raise NotFoundError('Export not found.')
    if record.status == 'completed' and record.file_path:
        return {'status': 'completed', 'download_path': f'/api/v1/exports/{record.id}/download'}
    record.status = 'processing'
    await db.flush()
    export_type = payload.get('export_type', 'full')
    module = payload.get('target_module')
    module = module[:-1] if module and module not in SOURCES and module.endswith('s') else module
    if export_type != 'full' and module not in SOURCES:
        raise ValidationError('Choose a supported source type for this export.')
    if export_type == 'record' and not payload.get('record_id'):
        raise ValidationError('Choose a record to export.')
    lines = ['# Second Brain private archive', '', 'Export of your saved records. Claims have not been independently verified.', '']
    for kind, (model, _) in SOURCES.items():
        if export_type != 'full' and kind != module:
            continue
        query = select(model).where(model.user_id == user_id, model.deleted_at.is_(None))
        if hasattr(model, 'archived_at'):
            query = query.where(model.archived_at.is_(None))
        if export_type == 'record':
            query = query.where(model.id == payload['record_id'])
        rows = (await db.execute(query)).scalars().all()
        lines.append('## ' + kind)
        for source in rows:
            lines.extend([record_text(source, kind), ''])
    storage = StorageService()
    _, _, _, _, path = await storage.save_upload(user_id, f'export-{record.id}.md', '\n\n'.join(lines).encode(), 'text/markdown')
    record.file_path, record.status = path, 'completed'
    record.signed_url, record.expires_at = None, None
    await db.commit()
    return {'status': 'completed', 'download_path': f'/api/v1/exports/{record.id}/download'}
