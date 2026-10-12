from unittest.mock import AsyncMock

import pytest

from app.ai.capsule import (
    CONTEXT_CHARS,
    Capsule,
    CapsuleSource,
    capsule_context,
    followup_query,
    make_capsule,
)
from app.ai.provider import GeminiLLMProvider

CITATIONS = [{'id': f'id-{n}', 'entity_type': 'memory', 'title': f'Record {n}', 'snippet': 'x' * 900, 'uri': '/sources/x'}
             for n in range(6)]


def test_capsule_keeps_the_gist_and_drops_citations_markup_and_ids():
    capsule = make_capsule(
        'Who is Ahmed? Also what did we agree about the Agami summit and the deck timing for next month please?',
        '**Ahmed** is the CTO of ABC Ventures [1]. You met him at Agami [2]. ' + 'Filler sentence. ' * 40, CITATIONS)
    assert capsule['question'].startswith('Who is Ahmed?') and len(capsule['question']) <= 160
    assert capsule['answer'].startswith('Ahmed is the CTO of ABC Ventures. You met him at Agami.')
    assert '[1]' not in capsule['answer'] and '**' not in capsule['answer'] and len(capsule['answer']) <= 280
    assert capsule['sources'] == [{'entity_type': 'memory', 'title': f'Record {n}'} for n in range(3)]
    assert 'id-0' not in str(capsule) and 'xxxx' not in str(capsule)


def test_ungrounded_answers_are_reduced_to_titles_not_an_excerpt_dump():
    capsule = make_capsule('Ahmed?', 'AI synthesis is unavailable. These are matching saved excerpts:\n\n' + 'dump ' * 400,
                           CITATIONS, grounded=False)
    assert capsule['answer'] == 'No AI answer was available. Matching records: Record 0; Record 1; Record 2'
    plain = make_capsule('Anything on Zed?', 'I could not find supporting records.', [], grounded=False)
    assert plain['answer'] == 'I could not find supporting records.' and plain['sources'] == []


def test_context_block_is_ordered_bounded_and_labelled_untrusted():
    assert capsule_context([]) == '' and capsule_context(None) == ''
    assert capsule_context([Capsule(question=' ', answer='')]) == ''
    notes = [Capsule(question=f'Question {n}', answer=f'Answer {n}', sources=[CapsuleSource(entity_type='person', title=f'Person {n}')])
             for n in range(6)]
    block = capsule_context(notes)
    assert 'never evidence' in block and 'Question 0' not in block and 'Question 1' not in block
    assert block.index('Question 2') < block.index('Question 5') and 'Person 5 (person)' in block
    bulky = [Capsule(question='q' * 600, answer='a' * 600) for _ in range(4)]
    assert len(capsule_context(bulky)) <= CONTEXT_CHARS + 500


def test_followups_borrow_titles_but_standalone_questions_do_not():
    previous = [Capsule(question='Tell me about Ahmed', answer='CTO.',
                        sources=[CapsuleSource(entity_type='person', title='Ahmed Rahman'), CapsuleSource(entity_type='meeting', title='Agami call'),
                                 CapsuleSource(entity_type='memory', title='Third')])]
    assert followup_query('what about him?', previous) == 'what about him? Ahmed Rahman Agami call'
    assert followup_query('and what did she promise me last time we spoke about it', previous).endswith('Ahmed Rahman Agami call')
    standalone = 'Which investors did I meet in Dhaka during the summit season last year and what did each of them ask'
    assert followup_query(standalone, previous) == standalone
    assert followup_query('what about Ahmed Rahman?', previous) == 'what about Ahmed Rahman? Agami call Third'
    assert followup_query('what about him?', []) == 'what about him?'
    assert followup_query('what about him?', [Capsule(question='q', answer='a')]) == 'what about him?'


@pytest.mark.asyncio
async def test_ask_returns_a_capsule_and_uses_one_to_resolve_a_followup(async_client, auth_headers, monkeypatch):
    created = await async_client.post('/api/v1/memories', headers=auth_headers, json={
        'title': 'Ahmed Rahman fundraising update', 'type': 'note',
        'body': 'Ahmed Rahman asked for the traction deck before the Agami summit.'})
    assert created.status_code == 201, created.text
    generate = AsyncMock(return_value='Ahmed Rahman asked for the traction deck before the summit [1]. He also wants metrics.')
    monkeypatch.setattr(GeminiLLMProvider, 'generate_content', generate)
    first = await async_client.post('/api/v1/ai/content-generate', headers=auth_headers, json={'prompt': 'Tell me about Ahmed Rahman'})
    assert first.status_code == 200, first.text
    capsule = first.json()['capsule']
    assert capsule['question'] == 'Tell me about Ahmed Rahman'
    assert capsule['answer'] == 'Ahmed Rahman asked for the traction deck before the summit. He also wants metrics.'
    assert capsule['sources'] == [{'entity_type': 'memory', 'title': 'Ahmed Rahman fundraising update'}]
    assert 'EARLIER IN THIS CONVERSATION' not in generate.await_args.args[0]

    alone = await async_client.post('/api/v1/ai/content-generate', headers=auth_headers, json={'prompt': 'what about him?'})
    assert alone.json()['provider_used'] == 'local' and alone.json()['source_citations'] == []

    generate.reset_mock()
    follow = await async_client.post('/api/v1/ai/content-generate', headers=auth_headers,
                                     json={'prompt': 'what about him?', 'conversation': [capsule]})
    assert follow.status_code == 200, follow.text
    assert follow.json()['provider_used'] == 'google_gemini' and len(follow.json()['source_citations']) == 1
    sent, instruction = generate.await_args.args[0], generate.await_args.kwargs['system_instruction']
    assert sent.startswith('EARLIER IN THIS CONVERSATION') and 'Asked: Tell me about Ahmed Rahman' in sent
    assert 'QUESTION: what about him?' in sent and 'never cite or restate them as facts' in instruction


@pytest.mark.asyncio
async def test_oversized_or_excess_conversation_is_rejected(async_client, auth_headers):
    too_many = [{'question': 'q', 'answer': 'a'}] * 9
    assert (await async_client.post('/api/v1/ai/content-generate', headers=auth_headers,
        json={'prompt': 'hello there', 'conversation': too_many})).status_code == 422
    huge = [{'question': 'q' * 601, 'answer': 'a'}]
    assert (await async_client.post('/api/v1/ai/content-generate', headers=auth_headers,
        json={'prompt': 'hello there', 'conversation': huge})).status_code == 422
