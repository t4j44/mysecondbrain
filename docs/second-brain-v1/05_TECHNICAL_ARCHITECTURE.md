# Technical Architecture — Existing Stack First
## Principle
Build a **cohesive modular monolith**, not five disconnected SaaS products. Reuse and validate current services before adding any new microservices, queues, databases or agent framework.

## 1. Current stack (repository-backed unless otherwise noted)
- **Frontend:** Next.js / React in `apps/web`, deployed preview on Vercel; state, UI modules and routes under `apps/web/app` and `apps/web/components`.
- **Backend:** FastAPI / SQLAlchemy asynchronous Postgres in `apps/api`, hosted on Render staging.
- **Auth/data:** Supabase Auth, Postgres 17, RLS, pgvector and private Supabase Storage; migrations in `supabase/migrations`.
- **AI:** existing Gemini integration, retrieval/search, meeting intelligence, chunking/indexing/AI services. Model and privacy mode must be verified per environment.
- **MCP:** existing server/tools and revocable access paths; source of identity and permission checks must be audited.
- **CI:** GitHub Actions; existing PostgreSQL schema and security tests. Draft PR #45 for hosted E2E, draft PR #46 for staging encrypted recovery (snapshot 2026-11-12).
- **Operations:** Render Free-like service and Vercel current plan; exact billing/terms verify. Google Drive for *encrypted offsite pilot backup*, not database hosting.

## 2. Logical architecture
```
Browser/PWA (Next.js) ── HTTPS/JWT ──> FastAPI business API
        │                                  │
        │                                  ├─ Auth + permission middleware
        │                                  ├─ People / Context / Commitments
        │                                  ├─ Meetings / Recording / Transcript
        │                                  ├─ Booking / Calendar / Notifications
        │                                  ├─ Ask / retrieval / citations
        │                                  └─ MCP / integration boundary
        │                                           │
        └── (signed audio upload) ──> Supabase Auth/Postgres + private Storage
                                            │
                            Encrypted staging backup → owner-private Google Drive
```
All derived outputs point to canonical source IDs. Ownership/tenant boundary is enforced in DB policies, not inferred from UI route, client-submitted user ID or AI content. Render/Vercel are deploy platforms, not sources of truth for user data.

## 3. Reuse targets in existing code
- `apps/api/app/services/meeting_audio.py`: accepts audio formats, private upload and bounded read, inspect 50MB max.
- `apps/api/app/api/v1/endpoints/meeting_intelligence.py`: auth + meeting recording retrieval. Signed URL is short-lived in current code (300s) or direct bytes for other storage modes.
- `apps/web/components/meetings/capture-panel.tsx`: consent, record/upload, local retry buffer, processing progress.
- `apps/web/app/(dashboard)/meetings/[meetingId]/page.tsx`: source navigation, correction, private recording player; audio download UI was absent in inspected main.
- `apps/api/app/services/meeting_preparation.py`, `meeting_corrections.py`, `meeting_intelligence.py`, `meeting_outputs.py`: verify existing contracts before replacements.
- `apps/api/app/services/relationships.py`, `person_context.py`, `commitment_actions.py`, `notification_outbox.py` for person and follow-up pipeline.
- `apps/api/app/db/rls.py` and `apps/api/app/dependencies/database.py` for canonical tenant-aware DB sessions; never bypass.
- `scripts/backup/*` and `scripts/restore/*` with review of PR #46; real hosted recovery **still unverified** in last evidence.

## 4. Canonical context graph (design contract)
Entities: `Account`, `Person`, `Organization`, `Relationship`, `Interaction/ContextEvent`, `Meeting`, `Recording`, `TranscriptSegment`, `Source`, `EvidenceRef`, `Claim`, `Memory`, `Commitment`, `Project`, `Booking`, `BookingType`, `AvailabilityRule`, `CalendarConnection`, `IntegrationGrant`, `ReviewReceipt`, `AuditEvent`.

Principles:
- One stable owner/tenant scope on every private entity, including embeddings, temporary drafts, search vectors, job status and caches.
- A **Source** is immutable original record metadata with provenance, time, modality, owner, retention status and optional immutable content digest.
- An **EvidenceRef** points to exact source (file page, message ID or transcript segment+start/end timestamps) and survives UI changes.
- **Claim** has `draft/needs_review/confirmed/rejected/superseded`; generated claims are not canonical memories by default.
- **Commitment** has actor/assignee/due/status/source; editing creates audit/event, updates indexes and future recall consistently.
- Person linking uses explicit user confirmation or strongly validated identity rules; ambiguous/duplicate matches stay unresolved.
- Deletion propagates into storage objects, embeddings, caches, linked derived objects and external grants subject to lawful retention.

Proposed migration fields/tables only if absent in current schema. Avoid duplicating existing `people`, `commitments`, `context_events` and meeting data. Require migration proof on isolated Postgres 17 and RLS tests.

## 5. Scheduling implementation design
- `BookingType`: host, public URL random identifier, default duration, buffer, lead time, published flag, rate limits.
- `AvailabilityRule` / `AvailabilityException`: local IANA timezone, recurring hours, breaks, holidays; convert slots to UTC and test DST overlaps/skips.
- `Booking`: host, guest contact (minimized), UTC start/end, guest timezone, status, provider event ID (nullable), idempotency key, cancellation credentials digest, sync status.
- Reservation transaction must serialize competing slots (exclusion constraint or locking) + check conflicting busy calendar events. Do not rely on browser-side calculations alone.
- Integrations: provider-scoped OAuth token server-side encrypted at rest, no tokens in JS or analytics; queue safe retries and reconcile partial failures. Manual ICS fallback when provider fails/unavailable.
- Public routes expose only minimal host display data and open slots. No private People, meeting extracts or documents.

## 6. AI and retrieval design
- Use present ingestion/indexing and hybrid retrieval if valid. Partition search by owner before ranking, never filter only after retrieval.
- Answer schema should carry `claim`, `source_ids[]`, `evidence_refs[]`, `uncertainty` and `suggested_next_actions[]`; do not invent refs to satisfy UI.
- Verify commitment/decision type with deterministic rules and structured validation. Review before write. Maintain extraction version and traceability without logging plaintext sensitive content.
- Include correction propagation to derived summaries and embeddings. Evaluate retrieval with synthetic manually scored questions for per-person cross-meeting recall and contradictory facts.
- Limit concurrency/tokens/audio, report per-user marginal costs, fail closed when free quotas or provider privacy restrictions are violated.
- For external AI providers, check data handling terms first; avoid sending personal or confidential data through free models allowed to improve provider products.

## 7. Reliability and background tasks
- Process ingestion and transcription idempotently; durable job state with explicit retry budget, poison messages, recovery path. Never run long audio processing inside a normal frontend request.
- Durable state labels: `created`, `uploading`, `uploaded`, `processing`, `ready_for_review`, `confirmed`, `failed/retryable`, `expired`, `deleted`.
- Instrument job failure, queue age, success ratio, latency and AI cost **without recording content**.
- Render Free sleeping/cold starts should show polite "Waking up" or retry guidance, not silent loss. Avoid unauthorized warmup workarounds or reliance on free always-on service guarantees.
- Provider webhooks validated with signed signatures/allowlists where applicable; idempotency and replay protection.

## 8. Secure interfaces / testing
- API identity comes only from verified session token; database RLS plus service authorization. Owner scope on cached, object and public booking endpoints.
- MCP tools return least-permission data, require explicit write approvals where appropriate, have revocable scoped tokens, audit and rate limits.
- Public booking tokens and recording URLs are short-lived/scoped; never serially enumerable.
- Every schema change must include migration, rollback/forward-recovery strategy, role/policy tests, backup evidence and deployment compatibility checks.

## 9. Technology tradeoffs and cost
- Prefer `Next.js + existing component library + FastAPI + Supabase` over microservices, separate vector DB, Elastic, event buses, Kubernetes or proprietary "agent orchestration" layers for the first 5–10 users.
- Booking/meeting bots, live transcription, multi-provider calendar sync and auto follow-up can become **high-complexity/high-per-user-cost**. Keep those off until evaluated.
- An explicit `$0 incremental` budget does not guarantee free AI processing, compliant commercial hosting or reliable compute. Flag all potential charges and obtain owner approval.
