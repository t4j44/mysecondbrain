# SECOND BRAIN — RELATIONSHIP INTELLIGENCE V1

Release review: September 26, 2026 (Asia/Dhaka).

Branch: `codex/free-tier-beta`. Implementation candidate: `42955b89538ab48b6da01131c877e9f9ccbfb6f5`. This report is a release artifact; the final response records the final local/remote SHA after documentation is committed. No merge to main or production promotion was performed.

The relationship workflow is implemented. Hosted acceptance is still blocked. Local tests, a synthetic UI fixture and disposable PostgreSQL CI do not demonstrate a working deployed product, real Gemini quality, or tester traction.

## What changed

| Area | Delivered change |
| --- | --- |
| Architecture | Shared relationship capabilities in the existing FastAPI service. Home, profiles, Ask and MCP use the same owner-scoped records and evidence. Existing Next.js, Supabase, Gemini, pgvector and background indexing remain in place. |
| UI | Consistent Home / Capture / People / Work / Ask navigation on desktop and mobile. Home uses saved contacts, promises, meetings, projects and interactions. Work links to projects, ventures, tasks, commitments, meetings and documents. |
| Capture | Review person identity, organization, meeting date/location, topics, existing project/venture and commitment direction. Confirmation saves connected records and queues indexing. Saved records are immediately linked in the UI. AI failure preserves manual review. |
| People | Source-linked brief, relationship timeline, topics, commitments by direction, tasks, affiliations and explicit work/person connections. Active/Warm/Cooling/Dormant labels explain dated contact recency and do not claim personal closeness. |
| Backend | Follow-up draft, scheduling, dismissal and completion. Completion requires a written outcome and explicit approval; it records an interaction and memory, completes the promise and its linked task, and supports safe retry. Drafting never sends a message. |
| Database | Migrations 27–28 add relationship action receipts and public professional claims. Owner policies, account-closure restrictions, composite owner/person foreign keys, export and deletion coverage. Fixed PostgreSQL project enum and UUID-array compatibility. |
| Agents | Bounded capability functions handle capture, relationship context, source review and follow-up suggestions. No always-running autonomous agent or external-message sender was added. Reasons and source links accompany suggestions; the user approves actions. |
| RAG | Existing real pgvector and bounded document normalization remain. Relationship questions first use current structured records and graph links, then existing semantic/keyword retrieval. Stale/deleted interaction links cannot support recommendations. No evidence means no invented contact recommendation. |
| MCP | Extended the existing server with `list_followups`, `find_people_who_can_help` and reviewed `log_interaction`; enriched person context while retaining existing history behavior. Existing read/write scopes and confirmation gates apply. |
| Enrichment | Optional public HTTPS page reader with bounded text, public-address checks, pinned DNS resolution, TLS verification and robots checks. No redirects, private-network fetching, login/CAPTCHA bypass or private contact-list transmission. Source URL/type/time, exact quote, identity review and qualitative confidence are stored. |
| Enrichment conflicts | Proposals do not alter canonical identity. Users can verify a source while keeping their profile, explicitly approve an update, reject or remove it. Company changes retain prior affiliation history. Removing evidence invalidates its searchable copy and derived portfolio drafts. |
| Privacy/security | Existing Gemini Free Tier minimization/placeholders and beta notice remain. New records are owner-scoped. Deleting a person invalidates direct linked private memories, interactions, commitments/tasks, action receipts, claims, cached public pages, vectors and derived portfolios. |
| Analytics | Actual 5-person / 3-interaction / 1-project / 1-commitment / 1-evidence-backed-Ask activation checklist. Private weekly activity and approved-outcome counts. Operator aggregate SQL for weekly active users, actions per user, return activity and stated $5 willingness. No payment, revenue or testimonial claim is inferred. |
| Hidden legacy UX | Hardcoded Home cards and simulated completion removed. Life KPIs, ideas, content and other legacy tools moved out of primary navigation into Settings; existing data/routes preserved. |

## Verification

Both required CI gates passed on implementation candidate `42955b89538ab48b6da01131c877e9f9ccbfb6f5`:

- [Security & Quality CI](https://github.com/t4j44/mysecondbrain/actions/runs/36174688297): backend suite, Ruff, Bandit, Mypy, frontend lint/typecheck/tests and production build.
- [PostgreSQL tenant and schema gate](https://github.com/t4j44/mysecondbrain/actions/runs/36174688270): migrations 27–28, real PostgreSQL/pgvector, RLS isolation, new Home/profile/source queries, outcome save/retry, portable export and account-closure restrictions; isolated dump/restore with the integration suite rerun.

Local evidence:

- Final CI backend suite: 232 passed. Local full run passed 229 before the added regression cases; final focused coverage and CI include those additions.
- Focused final regression run: 31 passed (schema adapters, Capture, relationship actions, source review).
- Frontend: 18 tests passed; lint and TypeScript passed; production build passed. A test-only typing issue was corrected before the UI commit.
- Ruff and Bandit passed. Local Mypy checked 146 source files. Fresh CI dependency/type failures were corrected in dependency declarations and database adapters.
- Final candidate PostgreSQL run: 34 passed; 34 passed again after real dump/restore. The expanded workflow exposed and verified the fix for the UUID-array persistence bug.
- Actual Home, Capture, profile, follow-up and Work components were inspected in a local synthetic UI fixture at 320, 390 and 1440 pixels without horizontal page overflow. Capture confirmation, editable draft and explicit outcome confirmation were exercised. This does not prove authentication, hosted persistence, physical-device behavior or live provider delivery.
- Staging browser E2E now includes Capture → person timeline → draft → confirmed outcome → reload persistence, followed by retrieval and portfolio revoke. It has not run against a configured staging environment.

## Product status matrix

These statuses describe verified implementation scope. Hosted end-to-end acceptance remains blocked across the product.

| Area | Status | Evidence boundary |
| --- | --- | --- |
| Home | PASS | Real owner-scoped data, component QA and real PostgreSQL queries. |
| Capture | PASS | Reviewed persistence, identity selection, topics, links and retry tests; local UI confirmation. |
| People | PASS | History, source brief, affiliations and actions; real PostgreSQL profile queries pass. |
| Work | PASS | Hub, promises, source-to-person links and explicit project links tested locally. |
| Ask | PASS | Person history/promises, follow-ups and evidence-linked network queries tested; broader questions retain RAG. |
| Relationship graph | PASS | Owner-validated explicit links; deleted-origin and cross-owner negative tests. |
| Opportunity reasoning | PARTIAL | Explainable due/cooling follow-ups and recorded offers; no multi-hop introduction guarantees or validated recommendation quality. |
| Follow-ups | PASS | Approval tests and real PostgreSQL outcome persistence and safe retry pass. |
| Enrichment | PARTIAL | Safe adapter and source-review/conflict/deletion tests; no real identity-accuracy benchmark or supported-site certification. |
| RAG | PARTIAL | Real pgvector CI coverage; live Gemini embedding/synthesis quality and free-tier capacity unmeasured. |
| MCP | PARTIAL | Existing server and transport tests; external ChatGPT/Claude/Gemini connector acceptance remains unverified. |
| Privacy | PARTIAL | Application isolation and database policies tested; hosted Auth/Storage isolation and end-to-end erasure still need acceptance. Redaction is heuristic. |
| Mobile | PARTIAL | Responsive synthetic component QA and action unit tests; authenticated mobile E2E and physical-device testing unrun. |
| Analytics | PASS | Actual-record activation, private counts and willingness form tested; no observed tester retention or testimonials yet. |

## Hosted readiness

Fresh probes at 18:29 UTC September 25 (September 26 Dhaka):

| Endpoint | Result |
| --- | --- |
| Existing web `/login` | HTTP 200 in 1.7 seconds; does not establish deployed revision or signed-in functionality. |
| Existing API `/health/live` | Timed out at 35.1 seconds. |
| Existing API `/health/ready` | Timed out at 35.1 seconds. |

Local process environment and available local configuration do not contain two E2E accounts, a staging test URL, or Render/Vercel/Supabase deployment credentials. This does not claim those settings are absent in hosted dashboards or GitHub secrets.

- READY FOR HOSTED STAGING: **NO**, working staging access/configuration is missing. The implementation passes the code/CI gate for an isolated staging deployment.
- READY FOR TAJ DOGFOODING: **NO**, hosted capture-to-outcome acceptance unrun.
- READY FOR 10 PRIVATE TESTERS: **NO**, hosted acceptance and real-provider checks unrun.

Exact remaining blockers:

1. Existing backend health times out; a healthy isolated staging API with the tested SHA and migrations 27–28 is not verified.
2. Two synthetic staging accounts and staging URLs are unavailable here. Therefore signed-in Capture/Person/Ask/document/MCP/logout-login persistence, cross-user Storage and authenticated desktop/mobile E2E cannot be completed from this session.
3. Live Gemini Free Tier quality/quota, external MCP-client access/revocation, and hosted privacy/deletion/recovery acceptance remain unverified. Drive and Calendar retain their existing implementation but live Google OAuth/sync is unverified and optional for the relationship beta.

## Next action

Restore access to a healthy isolated Render/Supabase/Vercel staging deployment and configure the `beta-staging` GitHub environment described in [RUNBOOK.md](RUNBOOK.md). Deploy only the tested revision there, then run the authenticated closed-beta E2E gate with two synthetic users. Keep passwords and provider keys in environment secrets, not chat. No paid Gemini decision is needed.

## Deliberate beta limits

This is a bounded V1: up to 500 contacts considered for follow-ups, latest 100 profile interactions/commitments/tasks, 150 profile edges, six projects/meetings and twelve recent interactions on Home. Explicit source review is limited to ten public page reads per hour. Identity confirmation is manual; public evidence may be stale. Existing free-tier redaction, provider quotas, English OCR and browser voice limits remain as documented in the runbook.

No real users, useful-outcome rate, willingness to pay, revenue or testimonials were manufactured. Successful actions currently mean user-approved follow-ups with recorded outcomes, not independently verified business results.
