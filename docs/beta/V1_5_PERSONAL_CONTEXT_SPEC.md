# Personal Context Foundation V1.5

Audit baseline: `9cf7ea0e4791bcc06dfa75d52e150aa63062d181`, September 27, 2026.
Implementation branch: `codex/personal-context-v1-5`. Highest existing migration: 28.
This map was written before application edits. Baseline V1 CI evidence is in
RELATIONSHIP_INTELLIGENCE_V1_RELEASE.md; those passes do not validate V1.5.

## Requirement map

| Brief sections | Classification | Existing implementation / compatible change |
| --- | --- | --- |
| 0–2 mission, architecture, audit | EXISTS / EXTEND | Next.js, FastAPI, Supabase PostgreSQL, pgvector and existing MCP server retained. Dedicated branch; no production mutation. |
| 3–5 temporal events and provenance | NEW | `context_events`: owner, happened/recorded/updated times, timezone, source, bounded original input, reviewed summary, references, privacy and replay key. Link derived records through existing graph. |
| 6 temporal graph | EXTEND | `entity_edges` currently has hard `uq_entity_edge`; replace with uniqueness for current facts, retain historical windows and event provenance. |
| 7 AI sessions | EXTEND | Existing finalizer transaction, extraction, scopes and retry semantics; add one authoritative event and derived-record links. |
| 8 remote MCP OAuth | NEW / EXTEND | Installed official SDK has authorization server/provider interfaces. Add durable hashed code/token grants, Supabase login/explicit consent, PKCE, resource binding, refresh rotation, revocation and Settings UI; preserve legacy credentials. Research current registration requirements before selecting client registration. |
| 9–11 card/photo/moments | EXTEND / NEW | Existing in-browser Tesseract OCR and reviewed Capture. Add compressed/EXIF-free private media, owner metadata, optional card plus moment, chronological profile events. Manual text works after OCR failure. |
| 12 intent people search | EXTEND | `relevant_contacts` already searches saved sources and graph. Add events, rank evidence, expose relationship recency/context/action and limits. No inferred willingness. |
| 13 Action Queue | EXTEND | Existing Home follow-ups; compact 3–5 highest priority items with evidence and explicit controls. |
| 14 outreach | EXTEND | Existing editable draft and approved outcome receipt. Add validated WhatsApp/mailto links, separate opened receipt and explicitly confirmed sent event; retries cannot double-record contact. |
| 15 pilot metrics | EXTEND | Existing private AuditLog/counts; add event names with IDs/counts/types only, no body/query/contact data. Outcomes remain self-reported. |
| 16 Context RAG | EXTEND | Existing source registry, fingerprints, owner revalidation, index jobs and real pgvector. Add approved/indexable events; invalidate derived context on erasure. |
| 17 time-aware Ask | EXTEND / DEFER | Implement bounded explicit/basic date windows with timezone and source dates. Defer sophisticated natural-language temporal interpretation first. |
| 18 enrichment | EXISTS | Keep bounded public-source fetch/review and provenance; no new scraping or external contact disclosure. |
| 19–21 privacy, model tier, security | EXTEND / EXISTS | Add event/media/OAuth erasure/export and owner checks/RLS; retain Gemini Free Tier configuration and beta notice. No new AI provider. |
| 22 APIs | EXTEND | Reuse capture, relationship, knowledge and MCP services; add only event/media and OAuth endpoints needed by UI/clients. |
| 23 mobile/navigation | EXTEND | Keep Home/Capture/People/Work/Ask; add touch-friendly photo review, action controls, profile moments and OAuth Settings. |
| 24–25 acceptance flows | EXTEND | Synthetic capture → person → evidence → reviewed outreach → explicit outcome → reload; MCP authorize → session → retry → retrieve → revoke. |
| 26–27 tests/gates | EXTEND | Backend, frontend, lint/types/build, PostgreSQL migration/RLS/vector and restore; desktop/mobile two-user browser coverage. Report local/CI/hosted separately. |
| 28 hosted order | EXISTS | Hosted V1 → V1.5 isolated staging → 7-day dogfood → 10–15 testers. Access was promised, not confirmed available. No hosted claims from code tests. |
| 29 release docs | NEW / EXTEND | This spec, V1_5_RELEASE, runbook, MCP auth/client setup, privacy/migration/E2E handoff. |
| 30 graph cache | EXTEND | `graphify-out/cache` contains tracked regenerable parser/semantic caches, including pre-existing missing files. Ignore/remove cache from index only; retain graph/report source outputs. |
| 31 cut line | EXISTS | Implement P0 first, then AI sessions/RAG/OAuth; advanced temporal language last. |
| 32 trust | EXISTS / EXTEND | AI proposes → review → explicit approval; no automatic sends/identity merges/outcome fabrication. |
| 33–35 completion/report | EXTEND | Demonstrate both acceptance chains and cross-owner denial. Distinct code/staging/dogfood/beta/production states with exact evidence. |

## Data and privacy contract

Canonical private records remain in Supabase. An event preserves the reviewed original
source separately from derived summaries; timestamps distinguish when it happened from
when it was saved. Owner-scoped event links connect interactions, memories, commitments,
tasks and MCP decisions without duplicating the existing graph or vector store.
New migrations follow 28 and are applied only to disposable test databases or authorized
isolated staging. Every new owner table requires RLS and an account-active guard.

Photos are re-encoded, compressed and stored in the existing private owner-prefixed
bucket. No original image or embedded location metadata is retained. Reads require
authorization or short-lived signed access. Account erasure must remove orphaned owner
objects as well as registered media; event/person erasure must remove derived searchable
context. Portable exports include metadata and text; any missing binary bytes are stated.

Outreach follows review → explicitly open external app → separately confirm sent/outcome.
Opening a link never proves delivery. Telemetry records private counts and record IDs,
never message bodies, raw prompts or contact details. OAuth code/token values are hashed
at rest and excluded from exports; revocation is checked on each request.

## Acceptance and non-goals

Required: reviewed card plus moment survives reload; occurred-at/source remain visible;
evidence supports the recommended person; WhatsApp/email text is reviewed; only explicit
confirmation updates contact history; an OAuth client can finalize/retrieve exactly one
session and loses access after revocation; user B cannot access user A records/media.

Gemini remains `gemini-2.5-flash`, embeddings `gemini-embedding-001`,
`AI_DATA_MODE=free_redacted`. Redaction is heuristic, not guaranteed anonymity.
Avoid highly sensitive or confidential beta input.

No automatic sending, social scraping, paid AI requirement, new database/provider,
large autonomous agent, skills dashboard, journey/year review, Daily Brain, public context
API, production promotion or unrelated redesign. Further major features wait for dogfood
and real tester evidence.

## Implemented protocol and temporal boundaries

OAuth uses the official MCP Python SDK handlers with a durable PostgreSQL provider,
PKCE S256, hashed code/access/refresh values, exact redirects and resource binding,
explicit owner consent, granular scopes and rotating refresh tokens. Dynamic client
registration is supported; Client ID Metadata Documents are not. Actual external-client
compatibility remains a hosted acceptance gate. Legacy scoped keys remain supported.

Time-aware Ask handles explicit supported questions about saved work, AI sessions,
events and commitments with yesterday, last calendar week/month, last 30 days, or an
explicit inclusive date range of at most 366 days. It uses a validated IANA timezone,
exact unambiguous saved entity names, at most 50 source rows and visible dates. It does
not infer unrecorded activity or support arbitrary temporal natural language. More
complex temporal interpretation is deferred under the P2 cut line.
