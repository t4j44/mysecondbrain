"""Only canonical segments may substantiate meeting proposals; no cross-speaker quotes."""
from app.core.errors import AIProviderError
from app.schemas.meeting_intelligence import CANDIDATE_FIELDS, EvidenceRef, MeetingIntelligence


def normalize(value: str) -> str:
    return ' '.join(value.split())


def resolve_quote(quote: str, segments: list[dict], speaker: str | None = None) -> list[EvidenceRef]:
    needle = normalize(quote)
    if not needle:
        raise AIProviderError('Meeting evidence is empty.')
    matches = [s for s in segments if needle in normalize(s['text'])
        and (speaker is None or s['speaker_local_id'] == speaker)]
    if not matches:
        raise AIProviderError('Meeting details contained unsupported segment evidence.')
    # Keep repeated utterances explicit; never silently choose a different speaker.
    return [EvidenceRef(segment_id=s['segment_id'], speaker_id=s['speaker_local_id'],
        start_seconds=s['start_offset'], end_seconds=s.get('end_offset'), quote=quote) for s in matches[:20]]


def validate_refs(refs: list[EvidenceRef], segments: list[dict]) -> None:
    by_id = {s['segment_id']: s for s in segments}
    for ref in refs:
        segment = by_id.get(ref.segment_id)
        if (not normalize(ref.quote) or not segment or ref.speaker_id != segment['speaker_local_id']
            or ref.start_seconds != segment['start_offset']
            or ref.end_seconds != segment.get('end_offset')
            or normalize(ref.quote) not in normalize(segment['text'])):
            raise AIProviderError('Meeting evidence does not match the canonical segment.')


def ground_intelligence(draft: MeetingIntelligence, segments: list[dict], speakers: list[str]) -> MeetingIntelligence:
    for field in CANDIDATE_FIELDS:
        for item in getattr(draft, field):
            if not normalize(item.evidence_text):
                raise AIProviderError('Candidate quotation must contain source text.')
            if any(s and s not in speakers for s in (item.from_speaker, item.to_speaker)):
                raise AIProviderError('Meeting details contained an unknown speaker.')
            if not item.evidence:
                item.evidence = resolve_quote(item.evidence_text, segments, item.from_speaker)
                if draft.schema_version == 1 and item.due_evidence:
                    # Legacy JSON had quotations but no reference array. A
                    # deadline may be in a separate utterance by that speaker.
                    due_refs = resolve_quote(item.due_evidence, segments, item.from_speaker)
                    item.evidence = [*item.evidence[:10], *due_refs[:10]]
            validate_refs(item.evidence, segments)
            # A genuine quote elsewhere does not substantiate this candidate's quote.
            if not any(normalize(item.evidence_text) in normalize(ref.quote)
                and (not item.from_speaker or ref.speaker_id == item.from_speaker)
                for ref in item.evidence):
                raise AIProviderError('Candidate quotation and speaker must match the same source reference.')
            if item.due_evidence:
                if not any(normalize(item.due_evidence) in normalize(ref.quote) for ref in item.evidence):
                    raise AIProviderError('Deadline evidence must be attached to the candidate source references.')
            if item.condition:
                if not normalize(item.condition) or not any(normalize(item.condition) in normalize(ref.quote) for ref in item.evidence):
                    raise AIProviderError('Condition evidence must be attached to the candidate source references.')
    for value in (draft.suggested_title, draft.purpose, *draft.agenda_items):
        if value:
            validate_refs(value.evidence, segments)
    for section in draft.discussion_sections:
        validate_refs(section.evidence, segments)
        for point in section.key_points:
            validate_refs(point.evidence, segments)
    return draft
