"""Bounded relationship routing. Deterministic facts first; RAG remains the fallback."""
import re

from sqlalchemy import func, or_

from app.models.entities import Person
from app.services.relationships import RelationshipService, source


def answer(lines, citations):
    return {'generated_text': '\n'.join(lines), 'provider_used': 'database', 'model_used': 'none',
        'source_citations': [row['id'] for row in citations], 'citations': [
            {'id': row['id'], 'entity_type': row['kind'], 'title': row['title'], 'uri': row['uri'],
             'snippet': row.get('snippet', row['title'])} for row in citations]}


async def relationship_answer(db, owner, prompt):
    service = RelationshipService(db, owner)
    normalized = prompt.strip().replace('’', "'")
    if re.fullmatch(r"(?i)(?:who (?:haven't|have not) i followed up with|who needs? (?:a )?follow[ -]?up|(?:show |list )?(?:my )?follow[ -]?ups)[.!?]?", normalized):
        suggestions = await service.followups()
        return answer([f"[{i}] {row['name']}: {row['why_now']}" for i, row in enumerate(suggestions, 1)] or ['No due or cooling relationships found in the current records.'], [row['evidence'] for row in suggestions])
    history = re.fullmatch(r'(?i)what (?:did|have) (?:i|we) (?:discuss(?:ed)?|talk(?:ed)? about) with (.+?)[.!?]?', normalized)
    promise = re.fullmatch(r'(?i)what (?:did|have) i promis(?:e|ed)(?: to)? (.+?)[.!?]?', normalized)
    their_promise = re.fullmatch(r'(?i)what did (.+?) promise(?: me)?[.!?]?', normalized)
    said = re.fullmatch(r'(?i)what did (.+?) (?:say|tell me) about (.+?)[.!?]?', normalized)
    match = history or promise or their_promise or said
    if match:
        name = match.group(1).strip().casefold()
        people = await service.rows(Person, or_(func.lower(Person.name) == name, func.lower(Person.name).startswith(name + ' ', autoescape=True)), limit=10)
        if len(people) != 1:
            return answer(['Choose the person you mean:' if people else 'No matching person is recorded. Save their context first.'] +
                [f'[{i}] {p.name}' + (f' — {p.company}' if p.company else '') for i, p in enumerate(people, 1)], [source(p, 'person') for p in people])
        profile = await service.profile(people[0].id)
        rows = profile['commitments'] if promise or their_promise else profile['timeline']
        if promise or their_promise:
            direction = 'owed_by_me' if promise else 'owed_to_me'
            rows = [row for row in rows if row['direction'] == direction]
        if said:
            topic = said.group(2).casefold()
            rows = [row for row in rows if topic in (row.get('summary') or row['title']).casefold()]
        rows = rows[:20]
        lines = [f"[{i}] {row.get('summary') or row['title']}" + (f" — {row['status']}" if 'status' in row else f" — {row['date']}") for i, row in enumerate(rows, 1)]
        return answer(lines or ['No supporting recorded ' + ('promises.' if promise or their_promise else 'conversation found.')], rows)
    patterns = [r'who (?:do i know|is) (?:in|connected to) (.+)',
        r'who (?:can|could|might|may) (?:help(?: me)?(?: with| on)?|introduce me to) (.+)',
        r"i(?:'m| am) trying to (.+)"]
    query = next((match.group(1) for pattern in patterns if (match := re.fullmatch(pattern + r'[.!?]?', normalized, re.I))), None)
    if query:
        from app.ai.structured import relevant_contacts
        query = re.sub(r'(?i)[.!?]\s*who.*$', '', query).strip(' .!?')
        query = re.sub(r'(?i)\b(?:raise funding|investors)\b', 'fundraising investors', query)
        contacts = await relevant_contacts(db, owner, query)
        citations, lines = [], []
        for person in contacts:
            citations.append({'id': person['person_id'], 'kind': 'person', 'title': person['name'], 'uri': f"/people/{person['person_id']}"})
            lines.append(f"[{len(citations)}] {person['name']} may be relevant. Confirm their interest and availability.")
            for evidence in person['evidence']:
                citations.append({**evidence, 'snippet': evidence['excerpt']})
                lines.append(f"[{len(citations)}] Recorded evidence: {evidence['excerpt'][:500]}")
        return answer(lines or ['No supporting relationship records found. No contact is recommended without evidence.'], citations)
    return None
