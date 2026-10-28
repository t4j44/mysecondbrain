import hmac

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.errors import AuthenticationError, ValidationError
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.models.assistant import AssistantPreferences
from app.schemas.assistant import AssistantPreferencesUpdate, TelegramUpdate
from app.services import assistant_connections as service

router = APIRouter(tags=['Assistant'])


def private_response(value):
    return JSONResponse(value, headers={'Cache-Control': 'private, no-store'})


@router.get('/assistant/connections/telegram')
async def connection(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    row = await service.connection_for(db, user.id)
    return private_response({'available': service.linking_available(), **service.connection_view(row)})


@router.post('/assistant/connections/telegram/start')
async def start(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    result = await service.start_link(db, user.id)
    await db.commit()
    return private_response(result)


@router.delete('/assistant/connections/telegram')
async def disconnect(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    result = await service.revoke(db, user.id)
    await db.commit()
    return private_response(result)


@router.get('/assistant/preferences')
async def preferences(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return private_response(service.preferences_view(await db.get(AssistantPreferences, user.id)))


@router.put('/assistant/preferences')
async def update_preferences(payload: AssistantPreferencesUpdate, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    result = await service.save_preferences(db, user.id, payload)
    await db.commit()
    return private_response(result)


@router.post('/integrations/telegram/webhook')
async def webhook(request: Request):
    supplied = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if len(expected) < 32 or not expected.isascii() or not supplied.isascii() or not hmac.compare_digest(supplied, expected):
        raise AuthenticationError('Invalid webhook authentication.')
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            raise ValidationError('Webhook update is too large.')
    try:
        update = TelegramUpdate.model_validate_json(body)
    except (PydanticValidationError, ValueError):
        raise ValidationError('Invalid webhook update.') from None
    await service.process_update(update)
    return private_response({'ok': True})
