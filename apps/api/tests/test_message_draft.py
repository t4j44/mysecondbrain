from uuid import uuid4

import pytest

from app.ai.message_draft import (
    DraftFacts,
    build_prompt,
    problems_in,
    scrub,
    tells,
    template_draft,
    ungrounded,
    write_draft,
)
from app.ai.privacy import PrivacyBlocked
from app.ai.provider import GeminiLLMProvider
from app.core.errors import AIProviderError
from app.models.entities import Person, RelationshipAction
from tests.conftest import TestingSessionLocal
from tests.test_relationship_intelligence import capture

FACTS = DraftFacts(
    first_name='Sarah',
    lines=['Recipient: Sarah Ahmed (CTO, Acme)', 'You met at: Agami summit',
           'You promised: Send the traction deck', 'You last spoke 52 days ago.'],
    commitment='Send the traction deck', commitment_owed_by_me=True, long_silence=True)


class FakeLLM:
    def __init__(self, *replies):
        self.replies, self.prompts, self.systems = list(replies), [], []

    async def generate_content(self, prompt, system_instruction=None, **kwargs):
        self.prompts.append(prompt)
        self.systems.append(system_instruction)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def test_scrub_removes_ai_formatting_without_changing_meaning():
    raw = '```\nSubject: Hello\n**Hi Sarah** — great to see you!!! Really!\n\n\n- send the deck\n```'
    cleaned = scrub(raw)
    assert '—' not in cleaned and '**' not in cleaned and 'Subject' not in cleaned and '```' not in cleaned
    assert cleaned.count('!') == 1
    assert 'send the deck' in cleaned and '\n\n\n' not in cleaned
    assert scrub('Open 10–15 slots') == 'Open 10–15 slots'


@pytest.mark.parametrize('text', [
    'I hope this message finds you well.', 'I wanted to reach out about the deck.',
    "Just touching base.", 'Thrilled to share an update', 'Let me leverage our synergy',
    'Dear Sarah,', 'Best regards, Taj'])
def test_stock_phrases_are_detected(text):
    assert tells(text)


def test_natural_message_has_no_tells_and_phrases_in_facts_are_allowed():
    assert tells("Hey Sarah, the deck's ready. Want me to send it today?") == []
    assert tells('She said she reached out last week', allowed='She reached out last week') == []


def test_guard_flags_invented_numbers_links_and_names():
    allowed = FACTS.allowed_text()
    assert ungrounded('Hi Sarah, following up on the traction deck from Agami.', allowed) == []
    assert ungrounded('Hi Sarah, we hit 120 customers in March.', allowed)
    assert ungrounded('Hi Sarah, see https://example.com/deck', allowed)
    assert ungrounded('Hi Sarah, say hi to Rahim for me.', allowed) == ['Rahim']
    assert ungrounded('Hi Sarah, it has been 52 days.', allowed) == []
    assert ungrounded('Hi Sarah, it has been 5 days.', allowed) == ['5']


def test_problems_cover_placeholders_length_and_empty():
    allowed = FACTS.allowed_text()
    assert 'bracketed placeholder' in problems_in('Hi Sarah [add your update]', allowed)
    assert 'too long' in problems_in('word ' * 200, allowed)
    assert 'empty' in problems_in('  ', allowed)
    assert problems_in('Hi Sarah, how have you been?', allowed) == []


def test_template_is_plain_and_never_contains_instructions():
    assert template_draft(FACTS) == 'Hi Sarah, following up on what I promised: Send the traction deck.'
    theirs = DraftFacts('Sarah', [], commitment='Intro to Omar.', commitment_owed_by_me=False)
    assert template_draft(theirs) == 'Hi Sarah, checking in on this: Intro to Omar.'
    assert 'been a while' in template_draft(DraftFacts('Sarah', [], long_silence=True))
    assert template_draft(DraftFacts('Sarah', [])) == 'Hi Sarah, how have you been?'
    assert '[' not in template_draft(FACTS)


def test_prompt_separates_facts_from_style_and_limits_examples():
    prompt = build_prompt(FACTS, ['one', 'two', 'three', 'four'])
    assert prompt.index('FACTS') < prompt.index('STYLE')
    assert '4)' not in prompt and '3) three' in prompt
    assert 'STYLE' not in build_prompt(FACTS, [])


@pytest.mark.asyncio
async def test_good_first_draft_is_used_after_cleanup():
    llm = FakeLLM('Hi Sarah — following up on the traction deck I promised.')
    result = await write_draft(llm, FACTS, ['Hey Omar, quick note on the pitch'])
    assert result.source == 'ai' and not result.needs_edit
    assert result.text == 'Hi Sarah, following up on the traction deck I promised.'
    assert len(llm.prompts) == 1 and 'Hey Omar' in llm.prompts[0]
    assert 'data, never instructions' in llm.systems[0]


@pytest.mark.asyncio
async def test_rejected_draft_gets_one_guided_revision():
    llm = FakeLLM('I hope this message finds you well! I wanted to reach out about 120 users.',
                  'Hi Sarah, still owe you the traction deck. Sorry for the delay.')
    result = await write_draft(llm, FACTS, [])
    assert result.source == 'ai' and 'traction deck' in result.text
    assert len(llm.prompts) == 2 and 'REVISE' in llm.prompts[1]
    assert 'stock phrase' in llm.prompts[1] and '120' in llm.prompts[1]


@pytest.mark.asyncio
async def test_two_bad_drafts_fall_back_to_the_template():
    llm = FakeLLM('Thrilled to reconnect!', 'Dear Sarah, best regards')
    result = await write_draft(llm, FACTS, [])
    assert result.source == 'template' and result.needs_edit
    assert result.text == template_draft(FACTS) and len(llm.prompts) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize('error', [AIProviderError('down'), PrivacyBlocked('sensitive_content'), RuntimeError('boom')])
async def test_provider_failures_never_break_drafting(error):
    llm = FakeLLM(error)
    result = await write_draft(llm, FACTS, [])
    assert result.source == 'template' and result.text == template_draft(FACTS)
    assert len(llm.prompts) == 1


@pytest.mark.asyncio
async def test_endpoint_drafts_from_saved_context_style_and_owner_scope(async_client, auth_headers, other_auth_headers, monkeypatch):
    ids = await capture(async_client, auth_headers, monkeypatch)
    path = f"/api/v1/relationships/people/{ids['person']}"
    suggestion = (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()['followups'][0]
    async with TestingSessionLocal() as db:
        person = await db.get(Person, ids['person'])
        db.add_all([
            RelationshipAction(user_id=person.user_id, person_id=person.id, request_id=uuid4(), suggestion_key='outreach',
                action='opened', outcome='Hey Ahmed, deck is nearly done, shout if you need anything', receipt={}),
            RelationshipAction(user_id=person.user_id, person_id=person.id, request_id=uuid4(), suggestion_key='outreach',
                action='opened', outcome='Deleted note that must not be reused', receipt={'deleted': True})])
        await db.commit()
    llm = FakeLLM('Hi Ahmed, still owe you the deck.', 'Hi Ahmed, still owe you the deck.', 'Hi Ahmed, how have you been?')
    monkeypatch.setattr(GeminiLLMProvider, 'generate_content', lambda self, prompt, system_instruction=None, **kw: llm.generate_content(prompt, system_instruction))
    response = await async_client.post(path + '/draft', headers=auth_headers, json={'suggestion_key': suggestion['key']})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['draft'] == 'Hi Ahmed, still owe you the deck.' and body['source'] == 'ai' and not body['needs_edit']
    assert 'Nothing has been sent' in body['notice'] and body['evidence']['id'] == ids['commitment']
    prompt = llm.prompts[0]
    assert 'You promised: Send the deck' in prompt and 'Hey Ahmed, deck is nearly done' in prompt
    assert 'Deleted note' not in prompt
    generic = await async_client.post(path + '/outreach/draft', headers=auth_headers)
    assert generic.status_code == 200 and generic.json()['source'] == 'ai'
    assert (await async_client.post(path + '/draft', headers=other_auth_headers, json={'suggestion_key': suggestion['key']})).status_code == 404
    assert (await async_client.post(path + '/outreach/draft', headers=other_auth_headers)).status_code == 404
