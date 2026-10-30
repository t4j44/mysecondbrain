import json
import logging

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.integrations import telegram_client as telegram

SYNTHETIC_TOKEN = '12345:synthetic_test_token_not_a_real_bot'


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, 'TELEGRAM_DELIVERY_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_BOT_TOKEN', SecretStr(SYNTHETIC_TOKEN))
    monkeypatch.setattr(settings, 'FRONTEND_URL', 'https://brain.example.test')
    monkeypatch.setattr(telegram, 'outbox_enabled', lambda: True)


def receipt(**changes):
    return {'message_id': 19, 'chat': {'id': 777, 'type': 'private'},
        'from': {'id': 12345, 'is_bot': True}, **changes}


async def test_default_off_never_calls_transport(enabled, monkeypatch):
    monkeypatch.setattr(settings, 'TELEGRAM_DELIVERY_ENABLED', False)
    def handler(request):
        raise AssertionError('Disabled transport must never open a connection.')
    result = await telegram.TelegramClient(transport=httpx.MockTransport(handler)).send(777, 'Private task', [])
    assert result.status == 'failed' and result.code == 'DELIVERY_DISABLED'
    assert SYNTHETIC_TOKEN not in repr(settings.TELEGRAM_BOT_TOKEN)


async def test_real_matching_receipt_required_and_token_logs_suppressed(enabled, caplog):
    requests = []
    def handler(request):
        requests.append(request)
        logging.getLogger('httpcore.connection').debug('Secret URL %s', request.url)
        return httpx.Response(200, json={'ok': True, 'result': receipt()})
    with caplog.at_level(logging.DEBUG):
        result = await telegram.TelegramClient(transport=httpx.MockTransport(handler)).send(777, 'Private task', [])
    assert result.status == 'delivered' and result.message_id == '19' and len(requests) == 1
    assert SYNTHETIC_TOKEN not in caplog.text and 'Private task' not in caplog.text
    assert str(requests[0].url).startswith('https://api.telegram.org/bot')
    sent = json.loads(requests[0].content)
    assert 'allow_paid_broadcast' not in sent and 'parse_mode' not in sent
    assert sent['link_preview_options']['is_disabled'] is True


@pytest.mark.parametrize('body', [
    {'ok': True, 'result': receipt(chat={'id': 888, 'type': 'private'})},
    {'ok': True, 'result': receipt(chat={'id': 777, 'type': 'group'})},
    {'ok': True, 'result': receipt(message_id=True)},
    {'ok': True, 'result': receipt(**{'from': {'id': 888, 'is_bot': True}})},
    {'ok': True, 'result': True},
    {'ok': 1, 'result': receipt()},
])
async def test_mismatched_or_malformed_receipt_is_uncertain(enabled, body):
    result = await telegram.TelegramClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=body))).send(777, 'Check-in', [])
    assert result.status == 'uncertain' and result.message_id is None


@pytest.mark.parametrize('mode', ['timeout', 'redirect', 'server', 'invalid', 'oversized'])
async def test_ambiguous_failure_is_not_retried(enabled, mode):
    calls = []
    def handler(request):
        calls.append(request)
        if mode == 'timeout':
            raise httpx.ReadTimeout('Synthetic timeout', request=request)
        if mode == 'redirect':
            return httpx.Response(302, headers={'Location': 'https://elsewhere.example.test'}, json={})
        if mode == 'server':
            return httpx.Response(500, json={'ok': False, 'error_code': 500})
        return httpx.Response(200, content=b'{' if mode == 'invalid' else b'x' * 65537)
    result = await telegram.TelegramClient(transport=httpx.MockTransport(handler)).send(777, 'Check-in', [])
    assert result.status == 'uncertain' and len(calls) == 1


async def test_explicit_rejection_is_sanitized_and_not_retried(enabled):
    client = telegram.TelegramClient(transport=httpx.MockTransport(lambda request:
        httpx.Response(429, json={'ok': False, 'error_code': 429, 'description': SYNTHETIC_TOKEN,
            'parameters': {'retry_after': 30}})))
    result = await client.send(777, 'Check-in', [])
    assert result.status == 'failed' and result.code == 'RATE_LIMITED'
    assert SYNTHETIC_TOKEN not in repr(result)
    with pytest.raises(ValueError):
        await client._request('sendMessage', {'chat_id': 777, 'allow_paid_broadcast': True})


async def test_acknowledgement_and_edit_use_bounded_methods(enabled):
    methods = []
    def handler(request):
        methods.append(request.url.path.rsplit('/', 1)[1])
        return httpx.Response(200, json={'ok': True, 'result': True if methods[-1] == 'answerCallbackQuery' else receipt()})
    client = telegram.TelegramClient(transport=httpx.MockTransport(handler))
    assert (await client.acknowledge('query', 'Saved')).status == 'delivered'
    assert (await client.edit(777, 19, 'Marked done based on your confirmation.', [])).status == 'delivered'
    assert methods == ['answerCallbackQuery', 'editMessageText']
