# Second Brain V1 status — September 17, 2026

**Closed-beta readiness: PARTIAL. Implementation is ready for connected staging verification; this is not a verified production release.** The $0 Gemini decision is implemented and no additional budget decision is required. Supplied credentials, account configuration, real PostgreSQL execution and external-client checks remain the release gates.

| Area | Status | Evidence and exact remaining gate |
|---|---|---|
| Production | PARTIAL | No push/deploy in this run; Render/Vercel deployed commits and hosted health unverified. |
| Database | PARTIAL | Canonical migration/schema contract updated; no staging DSN available to execute PostgreSQL migration tests. |
| Auth | PARTIAL | Local protected routes/API tests pass; actual Supabase sign-in/refresh requires public configuration and test users. |
| RLS | PARTIAL | Owner-isolation application tests pass; real PostgreSQL role/policy and Storage cross-tenant checks not run. SQLite is not RLS proof. |
| Relationship intelligence | PARTIAL | Existing graph integrated with reviewed capture, contact history, commitments and evidence-backed suggestions; connected end-to-end accuracy unverified. |
| Capture | PARTIAL | Proposal/review/atomic confirm, duplicate replay, owner checks, existing-person chooser, voice and in-browser photo OCR implemented. Live extraction and physical-phone flow unverified. |
| RAG | PARTIAL | Real 768-dimension embedding requests, durable indexing, pgvector query and canonical keyword fallback implemented; live Gemini and PostgreSQL ranking tests require credentials. No fake vectors. |
| MCP | PARTIAL | Official HTTP initialization/list/call/auth/scope/owner/revoke smoke test passes locally. Compatible real external-client connection and native hosted OAuth connectors unverified. |
| Assistant | PARTIAL | Correct answer endpoint, clickable private citations, explicit no-AI fallback, structured overdue-task queries and linked contact evidence. Live synthesis quality not measured. |
| Documents | PARTIAL | Private upload/extraction/index/retry and preserved local text on AI failure implemented. Hosted private bucket and scanned-document quality unverified. |
| Google Drive | PARTIAL | PKCE OAuth/encrypted token handling and retry-safe one-file Markdown archive implemented; mocked HTTP tests pass. Real OAuth consent/refresh/account export remains. |
| Google Calendar | PARTIAL | Explicit task scheduling/rescheduling/cancel with stable retry IDs; mocked HTTP tests pass. Real account verification remains; remote-event import is not implemented. |
| Portfolio | PARTIAL | Private evidence drafts/save and exact reviewed public snapshots/revoke tested. Hosted publication and live model claim quality unverified. |
| Mobile/PWA | PARTIAL | Touch-sized beta pages, compact navigation and existing manifest. Authenticated mobile E2E and physical-device/browser install checks remain. No offline private-data cache. |
| CI | PARTIAL | Real PostgreSQL and staging E2E workflows added; local checks below pass. Workflows have not run on GitHub for these commits. |

## Tests and security verification

- Backend unit/application tests: **176 passed**, 13 warnings; SQLite fixtures, no skipped tests in this unit suite.
- Additional focused structured-query tests after narrowing intent matching: **2 passed**.
- Frontend unit tests: **14 passed** (6 files).
- Official MCP Streamable HTTP smoke: included in backend suite; initialization, listing, search, cross-owner exclusion, write-scope denial and credential revocation.
- Python Ruff: pass. Mypy: pass across 133 source files. Bandit: exit 0; one documented false-positive exclusion for a PostgreSQL `token_hash` column type, no unresolved findings.
- Next.js production build: pass, including lint/types/static generation; explicitly nonfunctional build-only Supabase configuration. This does not prove connected authentication.
- Playwright signed-out browser tests: **3 passed** (protected-route redirect, invalid-email rejection, login controls). No authenticated test was counted as passed.
- New beta desktop/mobile E2E: authored; execution blocked on staging configuration and two users. PostgreSQL/pgvector/RLS: authored gate, not executed locally.
- Privacy tests exercise outbound generation/embedding payload minimization, stable owner-specific placeholders, restore only sent aliases, secret-content denial, raw attachment denial and configuration-only provider mode changes. Logs avoid raw provider errors/content and public bearer-link paths.
- Graphify local AST update succeeded; SQL graph coverage warns that its optional SQL parser is absent. Graph cache churn is excluded from product commits.

Evidence logs are local/ignored under `.test-tmp/`: `beta-complete-local.log`, `backend-complete.xml`, `structured-final.log`, `mypy-final2.log`, `ruff-complete.log`, `bandit-complete.log`, `web-unit-beta.log`, `web-build-final.log`, `browser-beta2.log`.

## Changes and migration

Backend: `apps/api/app/ai`, reviewed Capture service/routes, source inspection, publication/feedback models/routes, Google client, durable jobs, storage protection, scoped MCP tools, safe logging and repository indexing. Tests live in `apps/api/tests`.
Frontend: Capture, Documents, Ask, Sources, Portfolio and public links; Google integration/callback, private exports, MCP credentials, feedback/activity settings; mobile navigation, beta notice, browser tests. Existing user bearer-token work in `useChat.ts` is preserved.
CI/config: `.github/workflows/security_ci.yml`, `postgres.yml`, `beta-e2e.yml`, `scripts/check_test_evidence.py`, package scripts/lock/workspace and backend example configuration.
Migration created: `supabase/migrations/20260916000024_beta_publications_and_feedback.sql` (not applied to a live database).

Commit identifiers and exact file list are recorded in `COMMITS.md` after local commit creation. Base checkout: `522810cc7ecb2959eb450069aabb5653d7397286`. Deployment SHA: **not verified; no new deployment**. Pre-existing recovery artifacts, render.yaml, .agents and graph cache changes are left outside these commits.

## Manual actions and limitations

Follow [RUNBOOK.md](RUNBOOK.md) for exact setting names, callback path, migration procedure, GitHub staging environment and tester script. First supply staging Supabase configuration and the two synthetic users; this unlocks the database/authenticated browser gates. Add the Gemini Free Tier key for real AI checks, and Google OAuth settings for Drive/Calendar. Enter secrets only into gitignored local files or provider dashboards.

Remaining limitations include heuristic redaction, unmeasured shared free quota, native hosted-client OAuth compatibility, English photo OCR, no bidirectional Drive/Calendar import, partial-field Markdown archives and no physical-device certification. Activity counters and private feedback are implemented; real usage, retention, willingness to pay and approved testimonials remain to be collected. Do not describe this work as launch-ready until the connected staging gates pass.
