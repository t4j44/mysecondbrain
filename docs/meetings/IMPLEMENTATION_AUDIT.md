# Meeting Intelligence V1 implementation audit

Audited 2026-10-08 before implementation; final verification is in HANDOFF.md.

## Working base and repository boundary

Live `git ls-remote --heads origin` confirmed `codex/v1-5-prompt-intelligence` at
`8862f701c8a2ef12aff58bdf7613da8eb40e87ec`. It remained the correct V1.5 + Prompt
Intelligence base. Created `feature/meeting-intelligence-v1` from that exact commit.
Main was not used or merged. Initial tracked tree was clean; existing unrelated
untracked artifacts were preserved.

The base commit's GitHub combined status reported Vercel success. The workflow API
returned no matching workflow runs; this was not evidence that current feature CI
had run. Neither the feature nor its migration was pushed or deployed.

## Relevant reusable files

| Area | Existing implementation reused |
| --- | --- |
| Meeting + CRM | `apps/api/app/models/entities.py`, `models/meetings.py`, `repositories/meetings.py`, `services/network.py`, `schemas/meetings.py`, `api/v1/endpoints/network.py` |
| Auth + tenants | `dependencies/auth.py`, `dependencies/database.py`, `db/rls.py`; postgres application login with transaction-local authenticated role and owner claims |
| Audio storage | `integrations/storage_client.py`; flat owner prefix, private objects, short signed reads, existing storage-delete jobs |
| Durable processing | `jobs/runner.py`, `jobs/index_queue.py`, persisted `jobs` table and restart recovery |
| AI + retrieval | `ai/provider.py`, `ai/privacy.py`, `ai/indexing.py`, `ai/retrieval.py`; existing Gemini text/embedding provider and pgvector |
| Personal context | `services/context_events.py`, canonical ContextEvent + EntityEdge, existing timeline and relationship queries |
| User lifecycle | `services/account.py`; durable closure and portable export |
| Web | Meetings routes, `hooks/useMeetings.ts`, existing API client/auth, responsive containers and buttons |

## Verified inconsistencies

The list page had an audio placeholder; the detail page had transcript/summary
placeholders. The hook consumed `data/pagination` instead of the API's `items/total`
and the detail page expected a wrapped result. Generic meeting service writes used
the generic repository rather than the dedicated participant-junction implementation.
That left participant writes inconsistent. The Meeting response metadata alias also
collided with SQLAlchemy's class metadata. General document validation was not a
safe way to accept audio.

The implementation now uses the dedicated MeetingsRepository for CRUD/participants,
the direct Meeting response, and the actual list pagination contract. The generic
repository remains available for existing read consumers such as calendar sync.

## Migrations and implementation order

Read/inventoried all 32 existing SQL migration files through migration 31, including
the `21b` migration. Added only `20261008000032_meeting_intelligence.sql`: generic
usage counters, one-to-one processing metadata for existing Meetings, owner RLS,
and private meeting-audio bucket policies. No replacement CRM or transcript entity.

Implementation followed this order: repair existing contracts; add capture/quota/
private upload and job stages; implement Gemini final and metered Live relay; add
strict evidence-backed proposals and speaker mapping; transactionally confirm into
canonical CRM/context records; extend the existing index; replace meeting UI stubs
with recorder/upload/review; add tests, optional smoke scripts and handoff.

## Actual hosted inspection

Read-only check of `https://mysecondbrain-web.vercel.app` returned HTTP 200 and
`Server: Vercel`. The documented Render API endpoint's `/health/live` request timed
out after 20 seconds. No authenticated hosted acceptance, backend release SHA,
Gemini access, Supabase migration ledger or production storage state was verified.
Repository Docker/runtime config is evidence of intended architecture, not proof
of the currently running production container.

## Reference graph

Used graphify's existing code graph for the audit, then refreshed AST/code relations
with `graphify update .` without an AI call. The final refreshed graph had 6,001
nodes, 12,562 edges and 362 communities.
SQL extraction was unavailable because `tree_sitter_sql` was missing; migrations
were read directly. Existing graph/report snapshots were backed up by graphify.
