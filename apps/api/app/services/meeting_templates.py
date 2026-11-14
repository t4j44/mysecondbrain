"""Read-only presentations of existing intelligence, with canonical source checks."""
from pydantic import ValidationError

from app.ai.meeting_evidence import normalize, validate_refs
from app.core.errors import AIProviderError
from app.schemas.meeting_intelligence import EvidenceRef

TEMPLATES = {
    'founder': ('Founder meeting', (
        ('Key decisions', ('decisions',)),
        ('Owners and next steps', ('action_items', 'commitments')),
        ('Milestones and dates', ('important_numbers_or_dates',)),
        ('Investor and contact context', ('people_mentions', 'relationship_updates')),
        ('Open risks', ('risks', 'questions_open')),
    )),
    'client': ('Client call', (
        ('Goals and requirements to verify', ('important_facts', 'customer_feedback')),
        ('Decisions', ('decisions',)),
        ('Open questions', ('questions_open',)),
        ('Promised deliverables and next steps', ('commitments', 'action_items')),
        ('Follow-up and next meeting', ('follow_ups', 'important_numbers_or_dates')),
    )),
    'interview': ('User interview', (
        ('Reported problems and workarounds', ('customer_feedback',)),
        ('Reported behavior — verify observations', ('important_facts',)),
        ('Ideas — not validated demand', ('ideas',)),
        ('Open questions', ('questions_open',)),
        ('Follow-up requests', ('follow_ups', 'commitments')),
    )),
}


def template_markdown(meeting, kind):
    # Import here to keep the existing export entrypoint and avoid a module cycle.
    from app.services.meeting_outputs import evidence_markdown

    title, sections = TEMPLATES[kind]
    capture = meeting.capture
    data, receipt = capture.intelligence or {}, capture.receipt or {}
    selected = set(receipt.get('selected', []))
    corrected = {c['candidate_id'] for c in receipt.get('corrections', [])}
    lines = [f'## {title} template',
        'Organized from existing AI suggestions and owner review. No new extraction or confirmation.',
        'A source quotation supports what was said; it does not prove the claim is true.']
    if kind == 'interview':
        lines += ['Interview statements are participant claims, not product facts. '
            'Verify observed behavior separately. Obtain permission before reusing quotations outside this private meeting.']
    for heading, fields in sections:
        lines += ['', '### ' + heading]
        included, withheld = 0, 0
        for field in fields:
            for index, item in enumerate(data.get(field, [])):
                candidate_id = f'{field}:{index}'
                if capture.confirmed_at and candidate_id not in selected:
                    continue
                try:
                    refs = [EvidenceRef.model_validate(ref) for ref in item.get('evidence', [])]
                    validate_refs(refs, capture.transcript_segments or [])
                    if not refs or not normalize(item.get('evidence_text', '')) or not any(
                        normalize(item['evidence_text']) in normalize(ref.quote)
                        and (not item.get('from_speaker') or item['from_speaker'] == ref.speaker_id)
                        for ref in refs
                    ):
                        raise AIProviderError('Unsupported quotation.')
                except (ValidationError, AIProviderError):
                    withheld += 1
                    continue
                status = 'Owner-corrected assertion' if candidate_id in corrected else (
                    'Confirmed selection' if capture.confirmed_at else 'Proposal — not confirmed')
                if item.get('interpretation'):
                    status += '; interpretation'
                mapping = capture.speaker_mappings.get(item.get('from_speaker'), {})
                speaker = 'You' if mapping.get('kind') == 'me' else mapping.get('person_name') or 'Unassigned speaker'
                lines += [f'- [{status}] {item["description"]}',
                    f'  Source speaker: {speaker} | Date: {item.get("due_at") or "Not specified"}']
                if item.get('condition'):
                    lines += ['  Condition: ' + item['condition']]
                lines += ['  Original quotation: ' + item['evidence_text'],
                    '  ' + evidence_markdown([ref.model_dump() for ref in refs])]
                included += 1
        if not included:
            lines += ['No supported information available. Add or review source material; do not infer missing details.']
        if withheld:
            lines += [f'{withheld} item(s) withheld because their evidence could not be verified.']
    return '\n'.join(lines).replace('{meeting_id}', str(meeting.id))
