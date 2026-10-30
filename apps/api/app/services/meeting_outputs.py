"""Readable derived outputs and separately versioned owner-authored notes."""
from datetime import datetime, timezone
from urllib.parse import quote

from app.core.errors import ConflictError
from app.jobs.index_queue import queue_index
from app.schemas.meeting_intelligence import CANDIDATE_FIELDS


def evidence_markdown(refs):
    return ' '.join(f'[{ref["speaker_id"]} @ {ref["start_seconds"]:g}s '
        f'({ref["segment_id"]})](/meetings/{{meeting_id}}#segment-{quote(ref["segment_id"], safe="")})'
        for ref in refs)


def draft_notes(meeting):
    data = meeting.capture.intelligence or {}
    sections = data.get('discussion_sections', [])
    lines = ['AI draft notes — review against the source transcript.']
    for section in sections:
        lines += ['', '## ' + section['title']]
        points = section.get('key_points', [])
        lines += ['- ' + point['text'] + ' ' + evidence_markdown(point['evidence']) for point in points]
        if not points:
            lines += ['- ' + section['summary']]
        lines += [evidence_markdown(section['evidence'])]
    for key in ('questions_open', 'risks', 'ideas', 'customer_feedback'):
        if data.get(key):
            lines += ['', '## ' + key.replace('_', ' ').title()]
            lines += ['- ' + item['description'] + ' ' + evidence_markdown(item.get('evidence', [])) for item in data[key]]
    if not sections:
        lines += ['', data.get('summary', 'Processing has not produced notes yet.')]
    return '\n'.join(lines).replace('{meeting_id}', str(meeting.id))


def notes_view(meeting):
    stored = (meeting.meta or {}).get('meeting_notes', {})
    return {'version': stored.get('version', 0), 'markdown': stored.get('markdown', draft_notes(meeting)),
        'author': 'user' if stored else 'ai_draft', 'updated_at': stored.get('updated_at'),
        'revisions': stored.get('revisions', []), 'ai_draft': draft_notes(meeting)}


async def save_notes(db, meeting, payload):
    stored = (meeting.meta or {}).get('meeting_notes', {})
    if stored.get('version', 0) != payload.expected_version:
        raise ConflictError('Notes changed in another tab. Your edit is not saved; reload and compare before retrying.')
    revisions = stored.get('revisions', [])
    if len(revisions) >= 50:
        raise ConflictError('This meeting has reached its 50 note revisions. Further edits are unavailable; existing history can still be exported.')
    now = datetime.now(timezone.utc).isoformat()
    revision = {'version': payload.expected_version + 1, 'markdown': payload.markdown,
        'author': 'user', 'updated_at': now}
    meeting.meta = {**(meeting.meta or {}), 'meeting_notes': {**revision,
        'revisions': [*revisions, revision]}}
    queue_index(db, meeting)
    await db.flush()
    return notes_view(meeting)


def minutes_markdown(meeting):
    capture = meeting.capture
    data, meta = capture.intelligence or {}, meeting.meta or {}
    confirmed = bool(capture.confirmed_at)
    selected = set((capture.receipt or {}).get('selected', []))
    attendees = list(meta.get('participant_names', [])) if confirmed else []
    if confirmed and any(mapping.get('kind') == 'me' for mapping in capture.speaker_mappings.values()):
        attendees.insert(0, 'You')
    lines = ['## Meeting minutes',
        'Status: ' + ('Reviewed selections confirmed by owner' if confirmed else 'Proposed — not confirmed'),
        'Date/time: ' + meeting.start_time.isoformat(),
        'Meeting timezone: ' + (meta.get('timezone') or 'Unknown'),
        'Location: ' + (meeting.location or 'Unknown'),
        'Attendees: ' + (', '.join(attendees) if attendees else 'Not confirmed'),
        'Roles: Not recorded', '', '### Agenda', meta.get('agenda') or 'Not provided']
    for key in ('decisions', 'commitments', 'action_items', 'follow_ups'):
        lines += ['', '### ' + key.replace('_', ' ').title()]
        values = [(i, v) for i, v in enumerate(data.get(key, [])) if not confirmed or f'{key}:{i}' in selected]
        for _, item in values:
            status = 'Interpretation' if item.get('interpretation') else 'Confirmed selection' if confirmed else 'Proposal'
            mapping = capture.speaker_mappings.get(item.get('from_speaker'), {})
            owner = 'You' if mapping.get('kind') == 'me' else mapping.get('person_name') or ('Linked person' if mapping.get('person_id') else 'Unassigned')
            lines += [f'- [{status}] {item["description"]} | Responsible: {owner} | Due: {item.get("due_at") or "Not specified"}']
            if item.get('condition'):
                lines += ['  Condition: ' + item['condition']]
            lines += ['  Quote: ' + item['evidence_text'], '  ' + evidence_markdown(item.get('evidence', []))]
        if not values:
            lines += ['None confirmed.' if confirmed else 'None proposed.']
    return '\n'.join(lines).replace('{meeting_id}', str(meeting.id))


def export_markdown(meeting, kind):
    data, meta = meeting.capture.intelligence or {}, meeting.meta or {}
    lines = ['# ' + meeting.title, '', f'Meeting ID: {meeting.id}',
        'Source: owner-authorized canonical meeting transcript',
        'Meeting date: ' + meeting.start_time.isoformat(),
        'Meeting timezone: ' + (meta.get('timezone') or 'Unknown'), '']
    corrections = (meeting.capture.receipt or {}).get('corrections', [])
    if corrections:
        lines += ['## Owner corrections', 'These are owner assertions. Original quotations are preserved; outdated summaries are withdrawn.']
        for correction in corrections:
            lines += [f'- {correction["at"]}: {correction["candidate_id"]} — {correction["reason"]}',
                '  Before: ' + correction['before']['description'], '  After: ' + correction['after']['description'],
                '  Corrected deadline: ' + (correction['after'].get('due_at') or 'Not specified')]
    if kind in {'all', 'detailed'}:
        lines += ['## At a glance — AI draft', data.get('executive_summary') or data.get('summary', ''),
            '', '## Detailed summary — AI draft', data.get('detailed_summary') or 'Not available for this older extraction.', '']
    if kind in {'all', 'notes'}:
        notes = notes_view(meeting)
        lines += [f'## Meeting notes ({notes["author"]}, version {notes["version"]})', notes['markdown'], '']
    if kind in {'all', 'minutes'}:
        lines += [minutes_markdown(meeting), '']
    lines += ['## Evidence', 'Quotes are recorded speech; draft interpretations remain unverified.']
    for section in data.get('discussion_sections', []):
        lines += ['### ' + section['title']]
        for ref in section['evidence']:
            lines += [evidence_markdown([ref]), '> ' + ref['quote']]
    for field in CANDIDATE_FIELDS:
        for item in data.get(field, []):
            lines += [evidence_markdown(item.get('evidence', [])), '> ' + item['evidence_text']]
    return '\n'.join(lines).replace('{meeting_id}', str(meeting.id)) + '\n'
