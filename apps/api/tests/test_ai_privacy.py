import json

import httpx
import pytest

from app.ai.privacy import PrivacyBlocked, PrivateContext, prepare_text, private_ai_scope
from app.ai.provider import GeminiLLMProvider
from app.config import settings


def test_placeholders_are_stable_and_owner_specific():
    a, again, b = PrivateContext("a"), PrivateContext("a"), PrivateContext("b")
    token = a.alias("Ahmed", "PERSON", "123")
    assert token == again.alias("Ahmed", "PERSON", "123")
    assert token != b.alias("Ahmed", "PERSON", "123")
    safe = a.minimize("Ahmed: ahmed@example.com +880 1712345678 https://private.example/deck")
    assert "Ahmed" not in safe and "example.com" not in safe and "1712345678" not in safe
    assert "Ahmed" in a.restore(safe)
    assert b.restore(token) == token


@pytest.mark.asyncio
async def test_missing_scope_and_sensitive_content_never_leave(monkeypatch):
    monkeypatch.setattr(settings, "AI_DATA_MODE", "free_redacted")
    with pytest.raises(PrivacyBlocked):
        await prepare_text("a normal note")
    with private_ai_scope("a"):
        with pytest.raises(PrivacyBlocked):
            await prepare_text("password: never-send-this")
    with pytest.raises(PrivacyBlocked):
        await prepare_text("scope was reset")


@pytest.mark.asyncio
async def test_generation_minimizes_wire_payload_and_restores(monkeypatch):
    monkeypatch.setattr(settings, "AI_DATA_MODE", "free_redacted")
    seen = []

    async def post(_self, url, **kwargs):
        seen.append((url, kwargs))
        safe = kwargs["json"]["contents"][0]["parts"][0]["text"]
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "candidates": [{"content": {"parts": [{"text": safe}]}}]})

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    with private_ai_scope("a") as context:
        context.alias("Ahmed", "PERSON", "123")
        result = await GeminiLLMProvider(api_key="configured-for-wire-test").generate_content(
            "Ahmed discusses product design. Email ahmed@example.com")
    wire = json.dumps(seen[0][1]["json"])
    assert "Ahmed" not in wire and "ahmed@example.com" not in wire
    assert "key=" not in seen[0][0]
    assert "Ahmed" in result


@pytest.mark.asyncio
async def test_paid_mode_switch_is_configuration_only(monkeypatch):
    monkeypatch.setattr(settings, "AI_DATA_MODE", "paid_private")
    assert await prepare_text("an explicitly authorized private request") == (
        "an explicitly authorized private request", None)


def test_free_mode_refuses_raw_attachments(monkeypatch):
    from app.services.gemini_client import GoogleGenAIClient
    monkeypatch.setattr(settings, "AI_DATA_MODE", "free_redacted")
    with pytest.raises(PrivacyBlocked):
        GoogleGenAIClient().analyze_document_inline(b"private attachment", "application/pdf")


def test_only_sent_aliases_restore_and_json_names_remain_valid():
    context = PrivateContext('owner')
    sent = context.alias('Acme "Lab"', 'ORG', 'one')
    unsent = context.alias('Unmentioned private person', 'PERSON', 'two')
    context.minimize('Acme "Lab" built a prototype')
    result = json.loads(context.restore(json.dumps({'name': sent, 'other': unsent})))
    assert result == {'name': 'Acme "Lab"', 'other': unsent}


@pytest.mark.asyncio
async def test_embedding_minimizes_outbound_text_and_requests_real_dimensions(monkeypatch):
    monkeypatch.setattr(settings, 'AI_DATA_MODE', 'free_redacted')
    async def post(_client, url, **kwargs):
        payload = kwargs['json']
        assert payload['outputDimensionality'] == 768
        assert payload['taskType'] == 'RETRIEVAL_QUERY'
        assert 'Ahmed' not in json.dumps(payload) and 'example.com' not in json.dumps(payload)
        return httpx.Response(200, request=httpx.Request('POST', url), json={'embedding': {'values': [2.0] + [0.0] * 767}})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    with private_ai_scope('owner') as context:
        context.alias('Ahmed', 'PERSON', 'one')
        vector = await GeminiLLMProvider(api_key='wire-test-key').embed_text('Ahmed ahmed@example.com', task_type='RETRIEVAL_QUERY')
    assert vector == [1.0] + [0.0] * 767


@pytest.mark.asyncio
async def test_unconfigured_provider_never_returns_fake_success():
    from app.core.errors import AIProviderError
    provider = GeminiLLMProvider(api_key='placeholder')
    with pytest.raises(AIProviderError):
        await provider.generate_content('Anything')
    with pytest.raises(AIProviderError):
        await provider.embed_text('Anything')
