"""Wire-level language contract; no claim about real model accuracy."""
import httpx
import pytest

from app.ai.provider import GeminiLLMProvider
from app.core.config import settings


@pytest.mark.parametrize('instruction', [None, 'Answer using only the supplied sources.'])
async def test_generation_defaults_to_english_without_rewriting_source(monkeypatch, instruction):
    monkeypatch.setattr(settings, 'AI_DATA_MODE', 'paid_private')
    source = 'Original source: আগামীকাল দেখা হবে। Explicit user request: summarize in English.'
    seen = []

    async def post(_self, url, **kwargs):
        seen.append(kwargs['json'])
        return httpx.Response(200, request=httpx.Request('POST', url), json={
            'candidates': [{'content': {'parts': [{'text': 'Meeting planned; date needs review.'}]}}]})

    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    result = await GeminiLLMProvider(api_key='configured-for-wire-test').generate_content(source, system_instruction=instruction)
    assert result == 'Meeting planned; date needs review.'
    assert seen[0]['contents'][0]['parts'][0]['text'] == source
    policy = seen[0]['system_instruction']['parts'][0]['text']
    assert 'English by default' in policy
    assert 'only when the user explicitly requests' in policy
    assert 'Do not translate evidence quotes' in policy
    assert 'cannot be understood reliably' in policy
    if instruction:
        assert instruction in policy


def test_calendar_uses_neutral_default_and_preserves_explicit_zone():
    from app.api.v1.endpoints.system import CalendarSchedule
    assert CalendarSchedule(start='2026-10-29T12:00:00Z').timezone == 'UTC'
    assert CalendarSchedule(start='2026-10-29T12:00:00Z', timezone='Asia/Dhaka').timezone == 'Asia/Dhaka'


def test_transcription_keeps_non_english_source_verbatim():
    from app.ai.meeting_provider import parse_transcription
    original = 'আগামীকাল দেখা হবে।'
    segments = parse_transcription({'output_text': original}, 0, 0)
    assert segments[0]['text'] == original
    assert segments[0]['speaker_local_id'] == 'c0:unknown'
