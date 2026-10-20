"""Synthetic release regressions. Mocked AI is never live provider acceptance."""

import json
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.ai.indexing import meeting_chunks, record_text
from app.ai.meeting_evidence import ground_intelligence
from app.ai.meeting_provider import extract_intelligence, merge_digests
from app.ai.provider import GeminiLLMProvider
from app.core.config import settings
from app.core.errors import AIProviderError, NotFoundError
from app.mcp.tools import MCPDomainTools
from app.models.entities import Commitment, EntityEdge, Meeting, Task
from app.models.meeting_intelligence import MeetingCapture
from app.schemas.meeting_intelligence import Candidate, MeetingIntelligence
from tests.conftest import TestingSessionLocal
from tests.test_meeting_intelligence import (  # noqa: F401
    audio_stub,
    capture,
    process,
    processing_stub,
    uploaded,
)

pytestmark = pytest.mark.usefixtures("audio_stub", "processing_stub")


async def test_free_audio_requires_explicit_non_sensitive_attestation(async_client, auth_headers):
    response = await async_client.post('/api/v1/meetings/captures', headers=auth_headers,
        json={'request_id': str(uuid4()), 'title': 'Missing audio attestation',
            'meeting_date': '2026-10-20T10:00:00+06:00', 'recording_permission': True,
            'provider_terms_accepted': True})
    assert response.status_code == 409 and 'Text redaction does not sanitize audio' in response.text


async def test_old_notice_cannot_submit_or_resume_audio(async_client, auth_headers, test_user_id):
    meeting = await capture(async_client, auth_headers)
    path = '/api/v1/meetings/' + meeting['id']
    async with TestingSessionLocal() as db:
        row = await db.get(MeetingCapture, meeting['id'])
        row.receipt = {}
        await db.commit()
    await async_client.post(path + '/upload-authorization', headers=auth_headers, json={'mime_type':'audio/webm'})
    assert (await async_client.post(path + '/finalize-upload', headers=auth_headers)).status_code == 409


@pytest.mark.parametrize('empty_field', ['quote', 'evidence_text'])
def test_supplied_refs_cannot_ground_whitespace_only_quotes(empty_field):
    row = {'segment_id':'a','speaker_local_id':'alice','start_offset':0.,
        'end_offset':1.,'text':'I will send the report.'}
    candidate = {'description':'Arbitrary assertion','evidence_text':row['text'],
        'confidence':.9,'from_speaker':'alice','evidence':[{'segment_id':'a',
            'speaker_id':'alice','start_seconds':0.,'end_seconds':1.,'quote':row['text']}]}
    if empty_field == 'quote':
        candidate['evidence'][0]['quote'] = ' \n\t '
    else:
        candidate['evidence_text'] = ' \n\t '
    draft = MeetingIntelligence.model_validate({'schema_version':2,'summary':'Draft',
        'commitments':[candidate]})
    with pytest.raises(AIProviderError):
        ground_intelligence(draft, [row], ['alice'])


def test_conditional_proposals_cannot_replace_condition_with_whitespace():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match='Condition must contain source text'):
        Candidate(description='Send report', evidence_text='If approved, I will send it.',
            confidence=.9, condition=' \n\t ')


def test_legacy_conditional_proposals_preserve_full_quotation():
    from pydantic import ValidationError

    from app.schemas.meeting_intelligence import MeetingIntelligence
    quote = 'If approved, I will send the report.'
    old = {'summary': 'Review', 'commitments': [{'description': 'Send report',
        'evidence_text': quote, 'confidence': 0.9}]}
    assert MeetingIntelligence.model_validate(old).commitments[0].condition == quote
    assert 'condition' not in old['commitments'][0]
    with pytest.raises(ValidationError, match='preserve their condition'):
        MeetingIntelligence.model_validate(dict(old, schema_version=2))


@pytest.mark.parametrize('deadline_speaker', ['alice','bob'])
def test_legacy_deadline_in_separate_utterance_gets_canonical_references(deadline_speaker):
    quote, deadline = 'I will send the report.', 'The deadline is 2026-10-22.'
    rows = [{'segment_id':str(i),'speaker_local_id':'alice','start_offset':float(i),
        'end_offset':float(i + 1),'text':text} for i, text in enumerate([quote, deadline])]
    # Another participant can state the deadline; it must be referenced without
    # changing who spoke the primary promise, matching the v2 contract.
    rows[1]['speaker_local_id'] = deadline_speaker
    draft = MeetingIntelligence.model_validate({'summary':'Review','commitments':[
        {'description':'Send report','evidence_text':quote,'confidence':.9,'from_speaker':'alice',
         'due_at':'2026-10-22T00:00:00Z','due_evidence':deadline}]})
    ground_intelligence(draft, rows, ['alice','bob'])
    assert {ref.segment_id for ref in draft.commitments[0].evidence} == {'0','1'}


def test_two_genuine_refs_cannot_attribute_another_speakers_quote():
    from app.schemas.meeting_intelligence import EvidenceRef
    rows = [{'segment_id':'a','speaker_local_id':'alice','start_offset':0.,'end_offset':1.,'text':'Hello.'},
        {'segment_id':'b','speaker_local_id':'bob','start_offset':1.,'end_offset':4.,'text':'I will send the report.'}]
    refs = [EvidenceRef(segment_id=r['segment_id'], speaker_id=r['speaker_local_id'],
        start_seconds=r['start_offset'], end_seconds=r['end_offset'], quote=r['text']) for r in rows]
    draft = MeetingIntelligence(summary='Draft', commitments=[Candidate(description='Send report',
        evidence_text='I will send the report.', from_speaker='alice', confidence=.9, evidence=refs)])
    with pytest.raises(AIProviderError, match='same source reference'):
        ground_intelligence(draft, rows, ['alice','bob'])


async def test_optional_hosted_features_fail_closed_but_revocation_stays_available(async_client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, 'APP_ENV', 'staging')
    monkeypatch.setattr(settings, 'GOOGLE_INTEGRATIONS_RELEASE_VERIFIED', False)
    monkeypatch.setattr(settings, 'PORTFOLIO_PUBLISHING_RELEASE_VERIFIED', False)
    caps = await async_client.get('/api/v1/release-capabilities', headers=auth_headers)
    assert caps.json()['google_integrations'] is False and caps.json()['portfolio_publishing'] is False
    denied = await async_client.post('/api/v1/integrations/google/authorize?provider=google_drive', headers=auth_headers)
    assert denied.status_code == 409 and 'disabled' in denied.text
    assert (await async_client.post('/api/v1/sync/gdrive', headers=auth_headers)).status_code == 409
    assert (await async_client.get('/api/v1/public/portfolio/' + 'a' * 43)).status_code == 409
    # Disconnect must remain usable even while connection/sync is gated.
    assert (await async_client.delete('/api/v1/integrations/google/google_drive', headers=auth_headers)).status_code == 200


def long_segments():
    """90 synthetic one-minute sections; bilingual side topic and final unique fact."""
    rows = []
    for minute in range(90):
        topic = (
            "UAE expansion: দুবাইয়ের বাজার পরীক্ষা করব, যদি অনুমতি পাই।"
            if minute == 45
            else "Last-chunk retention: cobalt invoice 417."
            if minute == 89
            else f"Fundraising discussion {minute}: cost, alternatives, objections and uncertainty."
        )
        rows.append(
            {
                "segment_id": f"c{minute // 29}:{minute}",
                "chunk_index": minute // 29,
                "speaker_local_id": f"c{minute // 29}:spk_1",
                "start_offset": float(minute * 60),
                "end_offset": float((minute + 1) * 60),
                "text": topic + " Supporting discussion. " * 45,
            }
        )
    return rows


def digest(rows):
    sections = []
    for row in rows:
        evidence = {
            "segment_id": row["segment_id"],
            "speaker_id": row["speaker_local_id"],
            "start_seconds": row["start_offset"],
            "end_seconds": row["end_offset"],
            "quote": row["text"][:100],
        }
        sections.append(
            {
                "id": row["segment_id"],
                "title": row["text"].split(":")[0][:100],
                "kind": "secondary" if "UAE" in row["text"] else "primary",
                "summary": row["text"],
                "key_points": [{"text": row["text"][:100], "evidence": [evidence]}],
                "evidence": [evidence],
            }
        )
    return {
        "summary": "Discussed financing options.",
        "executive_summary": "Financing, alternatives and conditional market exploration.",
        "discussion_sections": sections,
    }


async def test_90_minute_outline_preserves_middle_secondary_topic_and_last_chunk(monkeypatch):
    rows = long_segments()
    calls, checkpoints = [], {}

    async def generate(self, prompt, **kwargs):
        part = json.loads(prompt.split("<segments>\n")[1].split("\n</segments>")[0])
        calls.append(part)
        assert len(prompt) <= settings.AI_MAX_INPUT_CHARS
        return json.dumps(digest(part), ensure_ascii=False)

    async def save(index, batch, total):
        checkpoints[str(index)] = batch

    monkeypatch.setattr(GeminiLLMProvider, "generate_content", generate)
    result = await extract_intelligence(
        "canonical",
        date="2026-10-20",
        speakers=sorted({r["speaker_local_id"] for r in rows}),
        segments=rows,
        save_checkpoint=save,
    )
    assert len(calls) > 1
    assert len(result.discussion_sections) == 90
    assert len(result.detailed_summary) > 4000
    assert "cobalt invoice 417" in result.detailed_summary
    assert any(s.kind == "secondary" and "UAE" in s.summary for s in result.discussion_sections)
    assert "দুবাইয়ের" in result.detailed_summary
    assert len(merge_digests([result, result]).discussion_sections) == 90
    before = len(calls)
    retried = await extract_intelligence(
        "canonical",
        date="2026-10-20",
        speakers=sorted({r["speaker_local_id"] for r in rows}),
        segments=rows,
        checkpoints=checkpoints,
    )
    assert len(calls) == before and retried == result


async def test_failed_extraction_batch_reuses_checkpoint_and_rejects_truncated_success(monkeypatch):
    rows, checkpoints = long_segments(), {}
    calls = 0
    fail = True

    async def generate(self, prompt, **kwargs):
        nonlocal calls
        calls += 1
        if fail and calls == 2:
            raise AIProviderError("Synthetic quota failure")
        return json.dumps(
            digest(json.loads(prompt.split("<segments>\n")[1].split("\n</segments>")[0]))
        )

    async def save(index, batch, total):
        checkpoints[str(index)] = batch

    monkeypatch.setattr(GeminiLLMProvider, "generate_content", generate)
    speakers = sorted({r["speaker_local_id"] for r in rows})
    with pytest.raises(AIProviderError):
        await extract_intelligence(
            "", date="2026-10-20", speakers=speakers, segments=rows, save_checkpoint=save
        )
    assert len(checkpoints) == 1
    fail = False
    result = await extract_intelligence(
        "",
        date="2026-10-20",
        speakers=speakers,
        segments=rows,
        checkpoints=checkpoints,
        save_checkpoint=save,
    )
    assert len(result.discussion_sections) == 90

    async def incomplete(*args, **kwargs):
        return '{"summary":"short only"}'

    monkeypatch.setattr(GeminiLLMProvider, "generate_content", incomplete)
    with pytest.raises(AIProviderError, match="incomplete"):
        await extract_intelligence("", date="2026-10-20", speakers=speakers, segments=rows)


@pytest.mark.parametrize("mutation", ["segment", "speaker", "time", "quote"])
def test_forged_segment_references_are_rejected(mutation):
    rows = long_segments()[:1]
    data = digest(rows)
    ref = data["discussion_sections"][0]["evidence"][0]
    if mutation == "segment":
        ref["segment_id"] = "another-owner:0"
    elif mutation == "speaker":
        ref["speaker_id"] = "fabricated"
    elif mutation == "time":
        ref["start_seconds"] = 3
    else:
        ref["quote"] = "Made up quote"
    with pytest.raises(AIProviderError):
        ground_intelligence(
            MeetingIntelligence.model_validate(data), rows, [rows[0]["speaker_local_id"]]
        )


def test_cross_speaker_quote_and_false_speaker_are_not_canonical_evidence():
    rows = [
        {
            "segment_id": "s0",
            "speaker_local_id": "a",
            "start_offset": 0.0,
            "end_offset": 1.0,
            "text": "Send the",
        },
        {
            "segment_id": "s1",
            "speaker_local_id": "b",
            "start_offset": 1.0,
            "end_offset": 2.0,
            "text": "report tomorrow.",
        },
    ]
    for quote, speaker in [("Send the report tomorrow.", None), ("report tomorrow.", "a")]:
        value = MeetingIntelligence(
            summary="Draft",
            commitments=[
                Candidate(
                    description="Send report",
                    evidence_text=quote,
                    from_speaker=speaker,
                    confidence=0.8,
                )
            ],
        )
        with pytest.raises(AIProviderError):
            ground_intelligence(value, rows, ["a", "b"])


async def test_note_history_conflict_and_retry_keep_user_edits(
    async_client, auth_headers, test_user_id
):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting["id"], test_user_id)
    path = "/api/v1/meetings/" + meeting["id"]
    first = await async_client.put(
        path + "/notes",
        headers=auth_headers,
        json={"expected_version": 0, "markdown": "# My own notes\nCobalt observation"},
    )
    assert first.status_code == 200 and first.json()["author"] == "user"
    stale = await async_client.put(
        path + "/notes",
        headers=auth_headers,
        json={"expected_version": 0, "markdown": "Lost update"},
    )
    assert stale.status_code == 409
    second = await async_client.put(
        path + "/notes",
        headers=auth_headers,
        json={"expected_version": 1, "markdown": "Reviewed notes v2"},
    )
    assert second.json()["version"] == 2 and len(second.json()["revisions"]) == 2
    async with TestingSessionLocal() as db:
        row = await db.get(MeetingCapture, meeting["id"])
        row.state = "failed"
        await db.commit()
    await process(meeting["id"], test_user_id)
    restored = (await async_client.get(path + "/notes", headers=auth_headers)).json()
    assert restored["markdown"] == "Reviewed notes v2" and restored["version"] == 2
    assert "Cobalt observation" in restored["revisions"][0]["markdown"]
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Commitment)) == 0
        assert await db.scalar(select(func.count()).select_from(Task)) == 0
    response = await async_client.patch(
        path, headers=auth_headers, json={"transcript_text": "Pretend audio evidence"}
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "suffix,method,body",
    [
        ("/notes", "get", None),
        ("/notes", "put", {"expected_version": 0, "markdown": "intrusion"}),
        ("/review", "put", {"expected_version": 0, "title": "intrusion"}),
        ("/export/markdown", "get", None),
    ],
)
async def test_new_outputs_are_owner_scoped_and_anonymous_denied(
    async_client, auth_headers, other_auth_headers, suffix, method, body
):
    meeting = await capture(async_client, auth_headers)
    path = "/api/v1/meetings/" + meeting["id"] + suffix
    kwargs = {"json": body} if body else {}
    assert (
        await getattr(async_client, method)(path, headers=other_auth_headers, **kwargs)
    ).status_code == 404
    assert (await getattr(async_client, method)(path, **kwargs)).status_code == 401


async def test_review_export_confirm_typed_edges_and_delete(
    async_client, auth_headers, other_auth_headers, test_user_id
):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting["id"], test_user_id)
    path = "/api/v1/meetings/" + meeting["id"]
    person = (
        await async_client.post(
            "/api/v1/people", headers=auth_headers, json={"name": "Synthetic Ahmed"}
        )
    ).json()
    foreign = (
        await async_client.post(
            "/api/v1/people", headers=other_auth_headers, json={"name": "Another owner"}
        )
    ).json()
    assert (
        await async_client.put(
            path + "/review",
            headers=auth_headers,
            json={"expected_version": 0, "project_id": foreign["id"]},
        )
    ).status_code == 404
    assert (
        await async_client.put(
            path + "/review",
            headers=auth_headers,
            json={
                "expected_version": 0,
                "title": "Manual title retained",
                "purpose": "Reviewed purpose",
                "agenda": "Owner agenda",
                "timezone": "Asia/Dhaka",
            },
        )
    ).status_code == 200
    assert (
        await async_client.put(
            path + "/review",
            headers=auth_headers,
            json={"expected_version": 0, "title": "Stale rename"},
        )
    ).status_code == 409
    assert (
        await async_client.post(
            path + "/speakers",
            headers=auth_headers,
            json={
                "speaker": "c0:spk_2",
                "kind": "person",
                "person_id": person["id"],
                "confirmed": True,
            },
        )
    ).status_code == 200
    assert (await async_client.post(path + '/speakers', headers=auth_headers,
        json={'speaker':'c0:spk_1','kind':'me','confirmed':True})).status_code == 200
    before_confirm = await async_client.get(path + '/export/markdown?kind=minutes', headers=auth_headers)
    assert 'Attendees: Not confirmed' in before_confirm.text
    receipts = [
        await async_client.post(path + "/confirm", headers=auth_headers, json={"confirmed": True})
        for _ in range(2)
    ]
    assert all(r.status_code == 200 for r in receipts) and receipts[0].json() == receipts[1].json()
    exported = await async_client.get(path + "/export/markdown", headers=auth_headers)
    assert exported.status_code == 200 and exported.headers["cache-control"] == "no-store"
    assert (
        "Manual title retained" in exported.text
        and "Asia/Dhaka" in exported.text
        and "Owner agenda" in exported.text
    )
    assert "#segment-c0%3A0" in exported.text and "I will send the report." in exported.text
    assert 'Attendees: You, Synthetic Ahmed' in exported.text
    assert "token=" not in exported.text and "meeting-audio/" not in exported.text
    async with TestingSessionLocal() as db:
        edges = (
            await db.scalars(select(EntityEdge).where(EntityEdge.source_entity_type == "meeting"))
        ).all()
        assert {e.relationship_type for e in edges} == {"produced", "participated_in_by"}
        assert all(
            str(e.user_id) == test_user_id and e.source_event_id and e.valid_from for e in edges
        )
        assert sum(e.target_entity_type == "person" for e in edges) == 1
    assert (await async_client.delete(path, headers=auth_headers)).status_code == 204
    assert (await async_client.get(path + "/notes", headers=auth_headers)).status_code == 404
    async with TestingSessionLocal() as db:
        assert not (
            await db.scalars(select(EntityEdge).where(EntityEdge.source_entity_type == "meeting"))
        ).all()
        assert (await db.get(Meeting, meeting["id"])).meta == {}
        with pytest.raises(NotFoundError):
            await MCPDomainTools(db=db, user_id=test_user_id).get_meeting_segments(meeting["id"])


async def test_mcp_bounded_segments_and_last_chunk_keyword_retrieval(
    async_client, auth_headers, test_user_id, other_user_id
):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting["id"], test_user_id)
    async with TestingSessionLocal() as db:
        row = await db.get(Meeting, meeting["id"])
        row.capture.transcript_segments = long_segments()
        row.notes = "\n".join(s["text"] for s in row.capture.transcript_segments)
        row.capture.intelligence = merge_digests(
            [MeetingIntelligence.model_validate(digest(long_segments()))]
        ).model_dump(mode="json")
        await db.commit()
        assert "cobalt invoice 417" in record_text(row, "meeting")
        assert any(c["metadata"].get("segment_id") == "c3:89" for c in meeting_chunks(row))
        tool = MCPDomainTools(db=db, user_id=test_user_id)
        result = await tool.get_meeting_segments(meeting["id"], limit=100)
        assert len(result["segments"]) == 10 and result["next_offset"] == 10
        assert (await tool.get_meeting_segments(meeting["id"], segment_id="c3:89"))["segments"][0][
            "start_offset"
        ] == 5340
        with pytest.raises(NotFoundError):
            await MCPDomainTools(db=db, user_id=other_user_id).get_meeting_segments(meeting["id"])
    found = await async_client.get(
        "/api/v1/search", headers=auth_headers, params={"query": "cobalt invoice 417"}
    )
    assert found.status_code == 200 and "cobalt invoice 417" in found.text


async def test_review_rejects_unknown_timezone_and_foreign_link(async_client, auth_headers):
    meeting = await capture(async_client, auth_headers)
    path = "/api/v1/meetings/" + meeting["id"]
    assert (
        await async_client.put(
            path + "/review",
            headers=auth_headers,
            json={"expected_version": 0, "timezone": "Made/Up"},
        )
    ).status_code == 422
    assert (
        await async_client.put(
            path + "/review",
            headers=auth_headers,
            json={"expected_version": 0, "venture_id": str(uuid4())},
        )
    ).status_code == 404
