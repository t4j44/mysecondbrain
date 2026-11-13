# Unified Meetings, Scheduling, People and AI Memory — Functional Specification
## Positioning
Fireflies provides meeting capture/intelligence and Timetics provides booking/availability workflows. Second Brain's unified outcome is **before → during → after → next interaction**, connected to **people, commitments and sources**, with user approval.

## 1. Five canonical journeys
### Journey A — Prepare
`Meetings > Upcoming > Open` shows title, attendees, purpose, last conversation, open commitments, relevant files, evidence links and one suggested agenda. A missing participant match is marked "Unlinked person" and never auto-associated merely by similar name. No invented meeting history.

### Journey B — Capture
Record with explicit recording permission + AI-provider notice; or upload WAV/MP3/M4A/WebM/OGG etc under current size/time quotas. Clearly show processing state, fallback, device buffering and privacy mode. Browser recovery drafts are **not** a guaranteed cloud backup. Unavailable live transcription cannot cause silent audio loss. Do not claim system audio capture where browser permissions don't support it.

### Journey C — Understand
Output: two-sentence gist; user-visible transcript with timestamps and speaker labels; proposed decisions, commitments, follow-ups, questions, dates, people/projects; every item links to the source segment and can be corrected. Display **suggested**, **confirmed**, **rejected** states. For controversial claims or uncertain transcription, flag human review; no made-up evidence.

### Journey D — Remember
After confirmation, write one canonical action/relationship event with provenance and version. Person detail timeline reflects confirmed interaction, meeting links, relationship changes and outstanding promises. Deduplicate actions and handle correction of inaccurate extraction. Distinguish `mentioned` from `promised`, `idea` from `decision`, and `potential follow-up` from `confirmed commitment`.

### Journey E — Schedule next
From Person or Meeting open `Schedule`. Owner picks booking type + availability. Guest chooses a timezone-aware slot, confirms, receives a calendar invitation only after sender consent and provider validation; owner sees confirmation and optional link to an existing person. Reschedule/cancel flows remain scoped to that booking. Do not expose private contact/notes to guests.

## 2. Meeting module acceptance contracts
### M1 — Original audio download (release-critical)
Existing code references: `apps/api/app/api/v1/endpoints/meeting_intelligence.py` contains `GET /{identity}/recording`; `apps/api/app/services/meeting_audio.py` handles storage; `apps/web/app/(dashboard)/meetings/[meetingId]/page.tsx` has private playback but no prominent dedicated download action in audited main.
- Add `Download original audio` alongside Play. Preserve original file bytes, MIME, and safe extension; avoid forced MP3 transcoding.
- Authenticate each request; verify `owner`, not only URL possession. Use current source handler/short-lived signed URL (currently ~300s) or safe streaming proxy. **Never expose indefinite public links.**
- Correct disposition/filename, mobile/browser CORS compatibility, bounded memory and no untrusted path or filename injection.
- Ensure recording retention/deleted/expired logic runs **before** signing/serving. Do not lengthen the present ~7-day recording retention without owner-controlled policy and cost review.
- A/B tests: A own 200; B or unauthenticated 401/403/404 as appropriate; expired/deleted no download; chunk hash preserved; original MIME; repeated requests; iOS Safari and Android Chrome.
- Optional front-end one-tap `Download transcript (.md/.txt)` and AI-summary export, separate from original audio.

### M2 — Transcript and evidence
- Each segment carries `meeting_id`, `segment_id`, `start_seconds`, `end_seconds`, `speaker_local_id`, `text`, quality/source metadata; correctable label and text with edit audit.
- Evidence reference must cite a **real** segment with valid timestamp. Clicking scrolls to transcript and seeks playback where recording retained.
- AI summary sentence with unsupported evidence must be flagged/abstained; no dynamic fake reference IDs.
- Speaker diarization is probabilistic. Ask user to name speakers, and avoid merging identities across meetings automatically.

### M3 — Human approval of persistent memory
- Review suggestions list: `Confirm`, `Edit & confirm`, `Reject`; full source context immediately visible.
- Persist only confirmed decisions/commitments/relationship updates as canonical records. Keep audit trail of source, actor, timestamp and extraction version. Corrections invalidate/refresh derived search indexes.
- A user may manually add content without AI, but its provenance remains explicit.

### M4 — Cross-meeting Ask and pre-meeting brief
- Retrieve across authorized meetings + confirmed person/commitment entities; use hybrid search already present if appropriate.
- Return `answer`, cited source spans, confidence or completeness indicator, and direct next actions requiring explicit user approval.
- Queries: "What did I promise Sarah in the last 90 days?", "What's changed?", "Show latest unresolved task", "Prepare for next call".
- If sources conflict, surface conflict; if missing, abstain. Ranking benchmark against hand-labeled synthetic questions before release.

### M5 — Three reusable AI templates (pilot)
1. **Founder meeting:** key decisions, owner/next step, milestone, investor/contact context, open risks.
2. **Client call:** goals, confirmed requirements, open questions, promised deliverables, next meeting.
3. **User interview:** problem, workaround, exact user-observed behavior, verbatim consented quotes, follow-up requests; separate interview claims from product facts.
Templates adjust *presentation and schema*, not owner permissions or AI provider privacy rules.

## 3. Timetics-style scheduling module
### Pilot-safe slice (prioritize once meeting flow passes)
**B1 Booking types**: user defines title, duration, buffers, minimum notice, daily max, meeting location type (phone/online/in-person), visibility, public slug, expiry/revocation. Keep 1:1 first.
**B2 Availability**: weekly business hours in IANA timezone; exceptions, vacations, minimum lead time; DST transitions; avoid creating slots that overlap confirmed events. Store time in UTC plus original zone.
**B3 Guest page**: no login required for guest; optional identity/contact fields with consent, CAPTCHA/honeypot/rate limits, only show available times and minimal public profile; no account private info in HTML, API or errors.
**B4 Atomic booking**: server transaction prevents race/double-booking; unique conflict logic and idempotency key; provider calendar acceptance only after successful local booking. On provider failure show manual fallback and track sync status.
**B5 Confirmation**: human-readable date/time in host and guest timezone, cancellation/reschedule via signed scoped token with TTL, optional ICS invite if no live calendar connection.
**B6 Reminders**: in-app/manual by default; if email is configured, verified consent and unsubscribe/notification preferences, retries/idempotency and bounded costs.
**B7 Calendar OAuth**: connect a single provider first, request minimum scopes, use refresh token encryption, scopes/expiry checks, disconnect/revoke, sync conflict observability, never write/delete external events without user authorization.

### Advanced / flag-disabled until accepted
- Round-robin/team scheduling and shared hosts; multi-calendar conflict resolution; appointments as paid services and payment integration; embeddable/white-label page builder; AI scheduling by natural language; autonomous agent modifications; auto-joining Zoom/Meet/Teams bots; live assist/voice agents, video recording; bulk marketing reminders.
- Each requires its own security/privacy/legal/cost gate. **Do not advertise or expose a button just because a database table exists.**

## 4. Fireflies-inspired capabilities and explicit tradeoffs
| Pattern | User outcome | Build strategy | Risk / release stance |
|---|---|---|---|
| Auto transcription + speaker diarization | Search conversation | Reuse existing audio & meeting pipeline; verify accuracy | P0 existing/validate |
| Timestamped search | Find exact quote | Reuse segment indexing, test source navigation | P0 |
| Ask across conversations | Recall promises | Merge meeting/person/commitment retrieval with audit evidence | P0 |
| Meeting summaries, action items | Save time | Template + approval workflow | P0 |
| AI Skills | Structured repeatable output | 3 templates, no third-party skill marketplace | P0 small set, P1 registry |
| CRM sync | Relationship context | Internal People updates on approval first | P0 internal; P2 external CRM |
| Recording/download/export | User-owned data | Original format + expiring auth | P0 |
| Autojoin bot | Capture video calls | Study platform terms, bot identity, announcement/consent | P2 off |
| Live assistance | Timely suggestions | Browser display only with explicit opt-in; resource budget | P2 off |
| Business/sales analytics | Trend insight | Pilot minimal private usage only | P2 |
| Enterprise teams | Sharing/workspaces | No unnecessary multitenancy expansion in pilot | P2 |

## 5. Data ownership and privacy
- Meeting, recording, transcript, extracted insight, booking, calendar token and relationship event are all scoped to authenticated owner/workspace. Multi-tenant boundary must be enforced by DB RLS **and** API authorization.
- Recording permissions and remote AI data-processing consent are separate; users can delete raw audio independently where storage supports it. When expired, preserve transcript only under declared retention policy.
- A public booking URL reveals available slots only; cannot enumerate People, stored meetings or staff/private emails. Guest data minimal, retention and right to delete respected.
- External calendar/provider failures must not create duplicate bookings or silently lose confirmed appointments.

## 6. Developer-friendly API/data contracts (shape, not mandate)
```
POST /meeting-captures                    create/capture draft
POST /meeting-captures/{id}/authorize    signed upload policy
POST /meeting-captures/{id}/finalize     idempotent start processing
GET  /meetings/{id}/recording            authorized time-limited media
GET  /meetings/{id}/recording/download   proposed safe download variant if needed
GET  /meetings/{id}/evidence/{segment}  transcript segment source
POST /meetings/{id}/review              human-confirm selected suggestions
GET  /people/{id}/brief                 evidence-linked relationship brief
POST /booking-types                     authenticated host config
GET  /public/book/{slug}/slots          privacy-restricted guest availability
POST /public/book/{slug}/reserve        atomic reservation, rate-limited
POST /public/bookings/{token}/cancel    signed scoped guest action
```
The agent must inspect existing router conventions before creating endpoints. Do not add duplicates or bypass the canonical auth dependency.

## 7. User test script
Ask 3 unfamiliar users to (a) upload a fictional call, (b) download its recording, (c) verify and confirm one extracted promise, (d) find Sarah and view why the promise is linked, (e) prepare for another meeting and (f) schedule a new meeting in another timezone. Observe completion, wrong actions, unsupported citations, consent understanding and time to task. Failed steps become usability defects before more AI features.
