"""Gmail contact dates: when the user last wrote to, and last heard from, each saved person.

Only the From, To, Cc and Date headers (plus three bulk-mail markers) are requested. Subjects,
snippets and bodies are never fetched, stored or sent to a model, and nothing is read at all
unless a saved person has an email address to match.
"""
import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any

import httpx
from sqlalchemy import select

from app.core.errors import IntegrationError
from app.integrations.google_client import GoogleIntegrationService
from app.models.entities import EmailContact, JobRecord, Person

API = 'https://gmail.googleapis.com/gmail/v1/users/me'
HEADERS = ('From', 'To', 'Cc', 'Date', 'List-Unsubscribe', 'Precedence', 'Auto-Submitted')
FIELDS = 'id,internalDate,labelIds,payload/headers'
# Mail Google files as promotions, social, updates or forums, plus junk and drafts, is not a conversation.
SKIP_LABELS = {'SPAM', 'TRASH', 'DRAFT', 'CATEGORY_PROMOTIONS', 'CATEGORY_SOCIAL', 'CATEGORY_UPDATES', 'CATEGORY_FORUMS'}
BULK_PRECEDENCE = {'bulk', 'list', 'junk'}
FIRST_SYNC_DAYS = 90
MAX_MESSAGES = 400
PAGE_SIZE = 25  # a page is read at once, so this bounds the extra reads once known mail is reached
FETCH_AT_ONCE = 8
MAX_RECIPIENTS = 8  # a message to more people than this is a broadcast, not a conversation
_GMAIL_HOSTS = {'gmail.com', 'googlemail.com'}
_ADDRESS = re.compile(r'^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$')


@dataclass(frozen=True)
class MailContact:
    email: str
    at: datetime
    direction: str  # 'sent' | 'received'


def normalize_email(value: str | None) -> str | None:
    """Lower-case address; Gmail ignores dots and +tags in the local part, so we do too."""
    address = (value or '').strip().lower()
    if not _ADDRESS.match(address):
        return None
    local, host = address.rsplit('@', 1)
    if host in _GMAIL_HOSTS:
        local, host = local.split('+', 1)[0].replace('.', ''), 'gmail.com'
    return f'{local}@{host}' if local else None


def _addresses(*values: str) -> list[str]:
    found = (normalize_email(address) for _, address in getaddresses(list(values)))
    return list(dict.fromkeys(item for item in found if item))


def _moment(message: dict[str, Any], headers: dict[str, str]) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(message['internalDate']) / 1000, tz=timezone.utc)
    except (KeyError, TypeError, ValueError):
        pass
    try:
        parsed = parsedate_to_datetime(headers.get('date', ''))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def parse_message(message: dict[str, Any], me: str) -> list[MailContact]:
    """Who the user wrote to, or who wrote to them, in one message. Empty for bulk or automated mail."""
    headers = {str(item.get('name', '')).lower(): str(item.get('value', ''))
               for item in (message.get('payload') or {}).get('headers', [])}
    if SKIP_LABELS & set(message.get('labelIds') or []):
        return []
    if 'list-unsubscribe' in headers or headers.get('precedence', '').strip().lower() in BULK_PRECEDENCE:
        return []
    if headers.get('auto-submitted', 'no').strip().lower() not in ('', 'no'):
        return []
    at = _moment(message, headers)
    senders = _addresses(headers.get('from', ''))
    if at is None or not senders:
        return []
    sender = senders[0]
    if sender == me:
        recipients = [item for item in _addresses(headers.get('to', ''), headers.get('cc', '')) if item != me]
        if not recipients or len(recipients) > MAX_RECIPIENTS:
            return []
        return [MailContact(item, at, 'sent') for item in recipients]
    return [MailContact(sender, at, 'received')]


class GmailSync:
    def __init__(self, db, user_id):
        self.db, self.user_id = db, str(user_id)
        self.google = GoogleIntegrationService(db, user_id)

    async def _saved_people(self) -> dict[str, str]:
        rows = (await self.db.execute(select(Person.id, Person.email).where(
            Person.user_id == self.user_id, Person.deleted_at.is_(None), Person.archived_at.is_(None),
            Person.email.is_not(None)))).all()
        found: dict[str, str] = {}
        for identity, address in rows:
            key = normalize_email(address)
            if key:
                found.setdefault(key, str(identity))
        return found

    async def _cursor_row(self, integration_id: str):
        kind = f'gmail_sync_cursor:{integration_id}'
        return kind, (await self.db.execute(select(JobRecord).where(
            JobRecord.user_id == self.user_id, JobRecord.job_type == kind).with_for_update())).scalars().first()

    async def _get(self, client, url, headers, params):
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 401:
            raise IntegrationError('Google authorization expired or was revoked. Reconnect Gmail.', code='GOOGLE_RECONNECT', status_code=409)
        if response.status_code == 403:
            raise IntegrationError('Gmail access was not granted, or the Gmail API is not enabled for this app.', code='GMAIL_ACCESS_DENIED', status_code=409)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        integration = await self.google.select_integration('gmail', payload.get('integration_id'))
        me = normalize_email(integration.account_identifier)
        if me is None:
            raise IntegrationError('Reconnect Gmail so Second Brain knows which account it is.', code='GOOGLE_ACCOUNT_UNKNOWN', status_code=409)
        people = await self._saved_people()
        if not people:
            return {'messages_checked': 0, 'people_with_email': 0, 'people_updated': 0, 'complete': True}
        token = await self.google.access_token('gmail', integration.id)
        kind, cursor = await self._cursor_row(str(integration.id))
        since_ms = int((cursor.result_payload or {}).get('internal_date_ms', 0)) if cursor else 0
        since_ms = since_ms or int((datetime.now(timezone.utc) - timedelta(days=FIRST_SYNC_DAYS)).timestamp() * 1000)
        seen: dict[str, dict[str, datetime]] = {}
        newest_ms, checked, reached_known, page_token = 0, 0, False, None
        auth = {'Authorization': 'Bearer ' + token}
        gate = asyncio.Semaphore(FETCH_AT_ONCE)
        params_for = [('format', 'metadata'), ('fields', FIELDS), *[('metadataHeaders', name) for name in HEADERS]]

        async with httpx.AsyncClient(timeout=30) as client:
            async def fetch(message_id: str):
                async with gate:
                    return await self._get(client, f'{API}/messages/{message_id}', auth, params_for)

            while checked < MAX_MESSAGES and not reached_known:
                query: dict[str, Any] = {'maxResults': PAGE_SIZE, 'includeSpamTrash': 'false'}
                if page_token:
                    query['pageToken'] = page_token
                listing = await self._get(client, f'{API}/messages', auth, query) or {}
                ids = [item['id'] for item in listing.get('messages', [])][:MAX_MESSAGES - checked]
                if not ids:
                    break
                for message in await asyncio.gather(*(fetch(identity) for identity in ids)):
                    checked += 1
                    if message is None:
                        continue
                    internal = int(message.get('internalDate') or 0)
                    if internal and internal <= since_ms:
                        reached_known = True  # the list is newest first; everything after this is already covered
                        break
                    newest_ms = max(newest_ms, internal)
                    for contact in parse_message(message, me):
                        person_id = people.get(contact.email)
                        if person_id:
                            slot = seen.setdefault(person_id, {})
                            slot[contact.direction] = max(slot.get(contact.direction, contact.at), contact.at)
                page_token = listing.get('nextPageToken')
                if not page_token:
                    reached_known = True  # the mailbox ends here, so nothing older is waiting
        await self._store(integration.id, seen)
        complete = reached_known
        if complete and newest_ms:
            if cursor is None:
                cursor = JobRecord(user_id=self.user_id, job_type=kind, status='completed', result_payload={})
                self.db.add(cursor)
            cursor.result_payload = {'internal_date_ms': newest_ms}
        await self.db.flush()
        return {'messages_checked': checked, 'people_with_email': len(people), 'people_updated': len(seen), 'complete': complete}

    async def _store(self, integration_id, seen: dict[str, dict[str, datetime]]) -> None:
        """Keep the latest date per direction. Re-reading the same mail changes nothing."""
        if not seen:
            return
        rows = (await self.db.execute(select(EmailContact).where(
            EmailContact.user_id == self.user_id, EmailContact.integration_id == integration_id,
            EmailContact.person_id.in_(list(seen))))).scalars().all()
        existing = {str(row.person_id): row for row in rows}
        for person_id, found in seen.items():
            row = existing.get(person_id)
            if row is None:
                row = EmailContact(user_id=self.user_id, integration_id=integration_id, person_id=person_id)
                self.db.add(row)
            for column, direction in (('last_sent_at', 'sent'), ('last_received_at', 'received')):
                if direction in found:
                    current = getattr(row, column)
                    current = current.replace(tzinfo=timezone.utc) if current is not None and current.tzinfo is None else current
                    setattr(row, column, max(found[direction], current) if current else found[direction])
