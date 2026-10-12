# Relationship loop: human drafts, Ask capsules, multi-account Google, email dates

Branch `feature/relationship-loop`, stacked on `feature/meeting-intelligence-v1`
(`49d9f34`, CI green: [Security & Quality](https://github.com/t4j44/mysecondbrain/actions/runs/38314396175),
[PostgreSQL gate](https://github.com/t4j44/mysecondbrain/actions/runs/38314396136)). Nothing here is deployed,
merged, or verified against hosted Supabase, a real Google account, or a real Gemini key.

## What exists now

| Piece | What it does | Where |
|---|---|---|
| Follow-up drafts | Writes a short message from the owner's saved facts (person, promise, last contacts, last email date) in the user's own style (their last three reviewed messages, this person's first). Output is cleaned of stock AI phrasing and rejected if it states any number, link, email or name not in the facts; one guided revision, then a plain template. Never sends. | `app/ai/message_draft.py`, `RelationshipService._compose` |
| Ask capsules | Each answer returns a short capsule (question gist, answer gist, up to three source titles). The device keeps the newest four and sends them with the next question so "what about him?" retrieves against the previous answer's records. Replayed as untrusted background, never as evidence. No server storage, no extra model call. The chat hook no longer uploads the full transcript. | `app/ai/capsule.py`, `hooks/useChat.ts` |
| Several Google accounts | One connection per user, capability and Google account (migration 33). Account email read from the verified ID token. Jobs are pinned to the chosen account; ambiguity returns 409 `GOOGLE_ACCOUNT_REQUIRED`. | `app/integrations/google_client.py`, settings page |
| Email dates | Optional Gmail connection (`gmail.metadata`). Records only when mail was last sent to and received from each saved person (migration 34). Feeds "last contact", quiet-contact detection, the person page and draft facts. | `app/integrations/gmail_metadata.py` |

## What email dates reads, exactly

- Requested per message: `format=metadata` with headers `From, To, Cc, Date, List-Unsubscribe, Precedence, Auto-Submitted`.
  No Subject, snippet or body is requested, stored, logged or sent to a model.
- Nothing is read at all unless a saved person has an email address.
- Ignored: spam, trash, drafts, Promotions/Social/Updates/Forums, anything with `List-Unsubscribe`, bulk precedence or
  auto-submitted headers, and mail sent to more than 8 people.
- Stored per person and account: `last_sent_at`, `last_received_at`. Idempotent (dates only move forward), so re-syncing
  never double counts.
- Disconnecting Gmail deletes the imported dates and sync cursor. Deleting a person deletes theirs.
- Capped at 400 messages per run (first run looks back 90 days). A run that hits the cap reports `complete: false`
  and does not advance its cursor.

## Google verification: read this before inviting anyone

- `gmail.metadata` is a **restricted** scope, the same tier as `gmail.readonly`
  ([Google's scope table](https://developers.google.com/workspace/gmail/api/auth/scopes)). Reading only headers is better
  for privacy but does not avoid verification.
- Apps that keep restricted-scope data on their own servers need Google verification and, for public use, an annual
  third-party security assessment ([restricted scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)).
  Personal-use and testing apps are exempt from that review.
- While the OAuth consent screen is in **Testing**, refresh tokens expire after 7 days and only listed test users can
  connect. Dogfood will need a reconnect each week until the app is published or the scope is verified.
- Gmail data is also covered by Google's API Services User Data Policy (Limited Use). Email dates stays within it by
  design: no model sees any of it. Do not extend this to message text without reading that policy and moving AI calls to
  `AI_DATA_MODE=paid_private`.

## Verification actually performed

Local, on this branch: ruff clean, mypy clean (168 files), backend tests for drafts, capsules, Google accounts and Gmail
(each with tests that fail against the previous behaviour, checked by reverting the unique rule), 54 frontend unit tests,
`tsc`, `next lint`. PostgreSQL integration tests for migrations 33 and 34 are written (`test_google_accounts_postgres.py`,
`test_email_contacts_postgres.py`) and **have not run locally** (no database); they run in the PostgreSQL CI gate.

Not verified: a real Google consent flow (ID-token parsing is tested against synthetic tokens), real Gmail responses,
real Gemini draft quality, hosted RLS, physical phone, and a production build on this branch.

## Not built, on purpose

- Reading message bodies or composing in Gmail. Gate: private AI path (`paid_private`) and a verification plan.
- Auto-sync. Email dates refresh when you press the button.
- Public-web research on people (Crawl4AI/Gruffet). The legitimate signal for job changes (LinkedIn) forbids scraping;
  revisit only with real demand and a consent model for the people being researched.
- Creating people from email. Only people already saved are matched.

## Staging acceptance for this branch

After the meeting branch is accepted in staging, apply migrations 33 and 34 to the **staging** project only, then:

1. Connect two test Google accounts for Calendar; confirm each shows its email and that scheduling asks which to use.
2. Connect Gmail with a test account, save a person with that test mailbox's correspondent address, press Refresh, and
   confirm the person page shows only dates. Check the Network tab: no Subject/snippet fields in any Gmail request.
3. Disconnect Gmail; confirm the dates disappear.
4. Ask a question, then a pronoun follow-up; inspect the request body: it carries `conversation` capsules, not the transcript.
5. Press Draft message with a real Gemini key and with the key removed; compare the AI draft with the plain fallback.
