> Latest checkpoint: [September 19 release gate](RELEASE_GATE_SEP19.md). This September 18 report is retained as historical evidence.

# SECOND BRAIN — FINAL PRODUCTION READINESS

Evidence checkpoint: September 18, 2026. **Release decision: NOT YET VERIFIED for personal production use or a 10–15-user private-data pilot.** This is a readiness checkpoint, not a completion certificate. The free Gemini decision remains accepted; paid Gemini is not a release requirement.

## What changed

- Verified Supabase token audience/issuer/expiry claims in commit `6150efa`.
- Backend privacy and document implementation: `f1ed659`.
- Privacy settings and document UI: `06d0bc4`.
- Operations/report follow-up: resolve with `git log -1 --format=%H -- docs/beta/PRODUCTION_READINESS.md`.
- Branch: `codex/free-tier-beta`; no merge to main or production promotion in this checkpoint. Previous beta commits were pushed. Final push evidence is appended after remote verification.

Account closure now blocks ordinary access, revokes publications and MCP credentials, queues private Storage deletion, removes owner records and then deletes the Supabase Auth identity. A durable receipt supports retries and blocks old tokens. The worker must be running; failed cleanup is not reported as completed. Local tests mock Storage/Auth responses; actual hosted erasure remains a mandatory gate.

Privacy settings expose a portable ZIP containing canonical JSON, per-table CSV and Markdown. Credentials are excluded; CSV formula cells are escaped while JSON retains originals. Original attachment bytes are not bundled. Copies already exported to Google and provider backups require their own retention/deletion handling.

MarkItDown 0.1.5 with only PDF/DOCX/PPTX/XLSX extras normalizes those formats and text/Markdown/CSV/JSON/HTML. Conversion uses a separate byte-only child process, secret-stripped environment, socket/process audit restrictions, ZIP/input/output limits and a 40-second timeout. Unix has memory/CPU ceilings; Windows does not have equivalent OS memory isolation. This is defensive isolation, not a hardened parser sandbox. No cloud OCR, plugin discovery, raw attachment model upload or LLM conversion is enabled. Image-only PDFs report OCR_REQUIRED. Rich formatting and source page numbers are not promised.

Conversion identity, chunking version and embedding model are independent. Unchanged normalized text can be reused, and unchanged stored chunks can be reused when changing embedding models. Ordinary answers use bounded relevant sections with configurable top-K and total context. Keyword fallback now selects matching later sections instead of always showing the opening paragraph. Three MCP document tools expose search, metadata and bounded canonical sections even when embedding is unavailable.

Contact deletion invalidates directly linked memories/interactions/tasks/commitments, vectors, graph edges and source-backed portfolio drafts. Company/role corrections update current affiliation for app and MCP updates. Exhaustive indirect-reference review and hosted graph accuracy remain unverified.

## Evidence matrix

| Area | State | Evidence / remaining gate |
|---|---|---|
| Local backend | PASS | 198 tests passed in readiness-verified.xml, plus one added MCP bounded/owner-isolation regression passed separately. No unit tests skipped. |
| Code quality | PASS | Ruff; mypy across 140 files; Bandit zero reported issues. Fixed-worker subprocess import has a documented narrow suppression. |
| Frontend | PASS locally | 14 unit tests, production build, three signed-out Chromium checks. Build used nonfunctional public placeholders, not real Supabase credentials. |
| Database schema | Static PASS only | 37 ORM tables against 67 parsed migration tables; zero missing columns/tables/type mismatches. Does not validate live constraints, grants or migration execution. |
| PostgreSQL/RLS | BLOCKED | 31 integration tests collected, not executed. No isolated DSN or local PostgreSQL runtime available. New closure-policy test included. |
| Supabase Storage | UNVERIFIED | Migration 26 installs private bucket and owner/anonymous restrictions. scripts/verify_storage_isolation.py ready for real A/B/anonymous HTTP proof; not run. |
| Auth/account deletion | PARTIAL | Local audience/issuer and closure regressions pass; live sign-in, refresh, old-token denial, Storage cleanup and Auth deletion require staging. |
| Capture/relationships | PARTIAL | Existing reviewed capture and relationship code retained; direct deletion/correction regressions pass. Real tester corpus accuracy unmeasured. |
| RAG/documents | PARTIAL | Actual local conversions and bounds tested. Real Gemini vectors/ranking, representative document latency/token benchmark and free-tier capacity not measured. 100 chunks per indexed record remains a beta limit. |
| MCP | PARTIAL | Local transport tests plus bounded canonical sections and owner denial. External ChatGPT/Claude/Gemini connection not verified. |
| Drive/Calendar | OPTIONAL / UNVERIFIED LIVE | Existing explicit sync and mocked tests retained; real OAuth consent/refresh and provider receipts needed. Does not block core beta if clearly disabled. |
| Portfolio | PARTIAL | Existing approved snapshot/revocation tests plus invalidation logic. Hosted link verification pending. |
| Mobile | UNVERIFIED authenticated | Responsive implementation retained; real phone sign-in, capture/photo, keyboard, attachment upload and installation checks pending. |
| Backup/restore | PARTIAL | Checked custom-format dump replaces unsafe shell pipeline; restore requires empty isolated target. No real dump/restore or Storage recovery drill performed. |
| CI | BLOCKED externally | GitHub run 35241544929 annotation: job was not started because account is locked due to a billing issue. No job steps ran. This is not a Gemini budget decision. |
| Hosting | UNVERIFIED current release | Earlier public homepage GET returned 200; API liveness/readiness requests timed out. Neither establishes deployed SHA or authenticated health. |
| Analytics/value | NOT VALIDATED | Existing first-party beta counters/feedback retained. No actual users, retention, time-saved evidence or testimonials claimed. |

Local evidence is in ignored `.test-tmp/`: readiness-verified.xml/log, mcp-section-proof.log, readiness-web-unit.log, readiness-web-build.log, readiness-browser.log, readiness-mypy-final.log, readiness-bandit-final.log, readiness-schema.json, readiness-pg-collection.log, readiness-graphify.log. Graphify AST refresh completed; its optional SQL parser is absent, so graph output is not SQL proof.

## Migrations and rollout order

1. Resolve GitHub account lock or execute the equivalent gates against an isolated PostgreSQL environment. Do not count a collected/skipped test as passing.
2. Apply canonical migrations through `20260917000026_account_closure_and_storage.sql` in staging. Migration 25 adds conversion metadata; 26 adds account closure and Storage restrictions. Neither was applied to production here.
3. Start both API and durable job worker with staging Supabase settings, free_redacted mode and a Gemini free key. Verify /health/live and /health/ready plus exact commit IDs.
4. Run PostgreSQL tests and the synthetic Storage isolation script. Then run the existing authenticated desktop/mobile E2E with two distinct staging users.
5. With synthetic data, verify capture → connect → retrieve → task, export, contact correction/deletion, account closure, revoked portfolio links and old MCP/JWT denial. Verify no foreign-user data changes.
6. Execute a real dump/isolated restore and separate Storage recovery drill. Benchmark representative PDF/DOCX/PPTX retrieval; record conversion time, context size, model tokens, latency and correctness without logging private text.
7. Verify an external MCP client and a real phone. Optional Google integrations remain disabled until their real-account checks pass.
8. Only after these gates pass, promote the same tested revision and repeat health, auth, isolation and core-flow smoke checks in production.

## Owner actions needed

- Resolve the GitHub account lock in GitHub account settings. No paid Gemini purchase is requested.
- Configure an isolated Supabase staging project and two synthetic users through provider dashboards or gitignored local environment files. Never paste keys/passwords into chat.
- Required configuration names: POSTGRES_TEST_DATABASE_URL, SUPABASE_URL, SUPABASE_SECRET_KEY (or the supported legacy server key), Supabase JWT/JWKS settings, TOKEN_ENCRYPTION_KEY, GEMINI_API_KEY, NEXT_PUBLIC_SUPABASE_URL and the public publishable/anon key, plus the documented E2E account variables in RUNBOOK.md.
- For Storage proof: STAGING_STORAGE_TEST=1, STAGING_SUPABASE_URL, STAGING_SUPABASE_PUBLIC_KEY, STAGING_USER_A_JWT and STAGING_USER_B_JWT. Only synthetic fixture bytes are uploaded and cleaned up. Signed links are bearer links; possession grants temporary access until expiry.
- Provide authorized staging deployment access through the provider connection/dashboard; no Render/Vercel token was available locally. Hosted configuration was not inspected, so missing local settings do not prove missing hosted settings.

The main remaining uncertainty is whether the complete system works safely with real hosted identities and data policies. Additional local passes cannot replace that evidence.

## Post-push verification

Implementation/operations revision `322b9073ad0591036fbd05e3262de0a024652b94` was pushed successfully; `git ls-remote` returned that exact branch SHA. PostgreSQL check 105550697474 and Security & Quality check 105550697471 failed before execution. The PostgreSQL annotation freshly confirmed: "The job was not started because your account is locked due to a billing issue." Vercel Preview Comments succeeded (not proof of app deployment); Supabase Preview was skipped. Fresh API liveness and readiness requests both timed out with a 25-second bound. No production readiness or deployed revision is inferred from these results.
