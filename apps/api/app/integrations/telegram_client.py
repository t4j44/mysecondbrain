"""Bounded Telegram transport; no retries, paid broadcasts or provider payload logs."""
import asyncio
import json
import logging
import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.services.notification_outbox import enabled as outbox_enabled

_private_request: ContextVar[bool] = ContextVar('telegram_private_request', default=False)


class TelegramTransportLogFilter(logging.Filter):
    def filter(self, record):
        # Telegram places the credential in its URL. HTTP libraries must not log it.
        return not (_private_request.get() and record.name.startswith(('httpx', 'httpcore')))


def _protect_http_logs():
    for target in [logging.getLogger('httpx'), *logging.getLogger().handlers]:
        if not any(isinstance(item, TelegramTransportLogFilter) for item in target.filters):
            target.addFilter(TelegramTransportLogFilter())


def bot_identity():
    match = re.fullmatch(r'([1-9][0-9]{0,15}):[A-Za-z0-9_-]{20,100}',
        settings.TELEGRAM_BOT_TOKEN.get_secret_value())
    return int(match.group(1)) if match and int(match.group(1)) < 2**52 else None


def delivery_available():
    origin = urlsplit(settings.FRONTEND_URL)
    return bool(settings.TELEGRAM_DELIVERY_ENABLED and outbox_enabled() and bot_identity()
        and origin.scheme == 'https' and origin.hostname and not origin.username
        and not origin.password and not origin.query and not origin.fragment)


@dataclass(frozen=True)
class TelegramResult:
    status: Literal['delivered', 'failed', 'uncertain']
    code: str
    message_id: str | None = None
    retry_after: int | None = None


class TelegramClient:
    def __init__(self, *, transport=None):
        self._transport = transport  # Isolated tests inject MockTransport; production uses TLS.

    async def _request(self, method, payload):
        if not delivery_available():
            return TelegramResult('failed', 'DELIVERY_DISABLED'), None
        allowed = {
            'sendMessage': {'chat_id', 'text', 'reply_markup', 'protect_content', 'link_preview_options'},
            'answerCallbackQuery': {'callback_query_id', 'text', 'show_alert', 'cache_time'},
            'editMessageText': {'chat_id', 'message_id', 'text', 'reply_markup', 'link_preview_options'},
            'editMessageReplyMarkup': {'chat_id', 'message_id', 'reply_markup'},
        }
        if method not in allowed or set(payload) - allowed[method]:
            raise ValueError('Unsupported Telegram operation.')
        _protect_http_logs()
        context = _private_request.set(True)
        try:
            async with asyncio.timeout(12):
                async with httpx.AsyncClient(transport=self._transport, timeout=5,
                        follow_redirects=False, trust_env=False) as client:
                    endpoint = 'https://api.telegram.org/bot' + settings.TELEGRAM_BOT_TOKEN.get_secret_value() + '/' + method
                    async with client.stream('POST', endpoint, json=payload) as response:
                        body = bytearray()
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            body.extend(chunk)
                            if len(body) > 65536:
                                return TelegramResult('uncertain', 'RESPONSE_TOO_LARGE'), None
                        data = json.loads(body)
                        if not isinstance(data, dict):
                            return TelegramResult('uncertain', 'INVALID_RESPONSE'), None
                        if response.status_code in (200, 400, 401, 403, 404, 429) and data.get('ok') is False and type(data.get('error_code')) is int and data['error_code'] in (400, 401, 403, 404, 429):
                            parameters = data.get('parameters')
                            retry = parameters.get('retry_after') if isinstance(parameters, dict) else None
                            retry = retry if type(retry) is int and 1 <= retry <= 86400 else None
                            return TelegramResult('failed', 'RATE_LIMITED' if data['error_code'] == 429 else 'PROVIDER_REJECTED', retry_after=retry), None
                        if response.status_code != 200 or data.get('ok') is not True:
                            return TelegramResult('uncertain', 'DELIVERY_UNKNOWN'), None
                        return None, data.get('result')
        except (httpx.RequestError, TimeoutError, ValueError):
            return TelegramResult('uncertain', 'DELIVERY_UNKNOWN'), None
        finally:
            _private_request.reset(context)

    async def send(self, chat_id: int, text: str, keyboard: list):
        if type(chat_id) is not int or not 0 < chat_id < 2**52 or not 0 < len(text) <= 4096:
            raise ValueError('Invalid private notification.')
        failure, message = await self._request('sendMessage', {'chat_id': chat_id, 'text': text,
            'reply_markup': {'inline_keyboard': keyboard}, 'protect_content': True,
            'link_preview_options': {'is_disabled': True}})
        if failure:
            return failure
        if (not isinstance(message, dict) or type(message.get('message_id')) is not int
                or message['message_id'] <= 0 or not isinstance(message.get('chat'), dict)
                or type(message['chat'].get('id')) is not int or message['chat']['id'] != chat_id
                or message['chat'].get('type') != 'private' or not isinstance(message.get('from'), dict)
                or message['from'].get('is_bot') is not True or type(message['from'].get('id')) is not int
                or message['from']['id'] != bot_identity()):
            return TelegramResult('uncertain', 'INVALID_RECEIPT')
        return TelegramResult('delivered', 'PROVIDER_ACCEPTED', str(message['message_id']))

    async def acknowledge(self, callback_id: str, text: str):
        if not 0 < len(callback_id) <= 256 or len(text) > 200:
            raise ValueError('Invalid callback acknowledgement.')
        failure, result = await self._request('answerCallbackQuery',
            {'callback_query_id': callback_id, 'text': text, 'cache_time': 0})
        return failure or TelegramResult('delivered' if result is True else 'uncertain', 'CALLBACK_ACKNOWLEDGEMENT')

    async def edit(self, chat_id: int, message_id: int, text: str, keyboard: list):
        if type(chat_id) is not int or not 0 < chat_id < 2**52 or type(message_id) is not int or message_id <= 0 or not 0 < len(text) <= 4096:
            raise ValueError('Invalid message edit.')
        failure, result = await self._request('editMessageText', {'chat_id': chat_id, 'message_id': message_id,
            'text': text, 'reply_markup': {'inline_keyboard': keyboard},
            'link_preview_options': {'is_disabled': True}})
        return failure or TelegramResult('delivered' if isinstance(result, dict) and result.get('message_id') == message_id else 'uncertain', 'MESSAGE_EDIT')
