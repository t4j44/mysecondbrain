# Release gate — September 19, 2026

**READY FOR TAJ DAILY USE = NO, pending hosted verification.**

**READY FOR 10–15 USER PILOT = NO, pending hosted verification.**

The $0 Gemini free tier remains the selected beta provider. No paid Gemini decision is needed. Google Drive/Calendar remain optional; the core privacy and relationship workflow owns the launch gate.

## Fixed and verified locally

Implementation revision: `df283ebd2f5384275a7e2be130212c8f6d4978bb`, pushed to `codex/free-tier-beta`. This report and the benchmark are a later follow-up commit, discoverable with `git log -1 --format=%H -- docs/beta/RELEASE_GATE_SEP19.md`.

| Defect / risk | Root cause | Fix and evidence |
|---|---|---|
| Reuploaded file could be deleted | Identical bytes and filename reused a path still referenced by a queued deletion | Unique object IDs, plus a per-owner/checksum PostgreSQL upload lock. Regression executes old deletion and confirms the new copy remains readable; canonical duplicate upload still returns the existing record. Lock behavior itself still needs PostgreSQL execution. |
| Clean PostgreSQL bootstrap would fail | Migration 26 grants to service_role, but the local auth shim created only anon/authenticated | Added the missing NOLOGIN role. Bootstrap now sorts migration timestamps, rejects a populated public schema, requires explicit isolated-target opt-in for remote hosts, and never echoes connection strings. Guard tests pass; actual migration execution BLOCKED. |
| Restored database could lose app access | Backup/restore used --no-acl and omitted grants | Preserve grants; clear inherited PG connection overrides; preserve DSN SSL settings; retain checked partial-file handling. Ten recovery/verifier tests pass, but mocked command tests are not restore evidence. |
| Storage cleanup could stall all jobs | A provider repeatedly listing supposedly deleted files caused an endless loop | Repeated object names fail cleanup with a retryable error. Test confirms bounded failure. |
| Staging could silently use local disk | Only production rejected missing Supabase Storage configuration | Both staging and production now fail closed; tests cover both. |
| Isolation script could report false proof | A 500/503 or redirect was treated as denied access | Require explicit denial statuses, add foreign/anonymous update/delete attempts and verify original bytes remain. Outage/rate-limit/redirect regression tests pass. Real Storage HTTP run BLOCKED. |
| Deployed revision could not be identified | Health exposed only a generic app version | /health exposes a validated 40-character RELEASE_SHA, automatically accepting RENDER_GIT_COMMIT. Misconfigured arbitrary values are not exposed. Readiness DB probes now have a five-second timeout. |

The PostgreSQL CI job now performs a real dump to a custom archive, creates a uniquely named temporary database on its disposable local server, restores, checks synthetic record content and owner/foreign visibility, then runs the integration suite against the restored database. It removes only its generated database and fixtures. It preserves roles/grants and pins PostgreSQL client/server major version 16 on Ubuntu 24.04. **This drill is implemented, not executed.** It does not verify Supabase-managed Auth recovery or Storage object backup.

## Evidence levels

| Subsystem | Implemented | Local tested | Real PostgreSQL tested | Staging verified | Deployed revision verified | Production workflow verified |
|---|---|---|---|---|---|---|
| Auth / closure / export | YES | PASS | BLOCKED | BLOCKED | UNVERIFIED | UNVERIFIED |
| Storage and delete/reupload | YES | PASS with mocked provider and local files | BLOCKED | BLOCKED | UNVERIFIED | UNVERIFIED |
| Core capture / relationships | YES, prior implementation retained | PASS | BLOCKED | BLOCKED | UNVERIFIED | UNVERIFIED |
| Document conversion / bounded excerpts | YES | PASS, synthetic formats | BLOCKED for stored vectors | BLOCKED | UNVERIFIED | UNVERIFIED |
| Semantic RAG / external MCP | YES | Local/mocked boundary only | BLOCKED | BLOCKED | UNVERIFIED | UNVERIFIED |
| Recovery | YES, new CI drill | Guards PASS | BLOCKED | BLOCKED | N/A | UNVERIFIED |
| Mobile core flow | YES | Prior signed-out browser evidence only | N/A | BLOCKED | UNVERIFIED | UNVERIFIED |

- **214 backend tests passed, zero skipped**, `.test-tmp/sep19-complete.xml` (96.77 seconds).
- Recovery script tests rerun after final exception handling edits: **10 passed**, `.test-tmp/sep19-recovery-final.log`.
- Ruff and mypy (140 application files) passed; Bandit reported zero issues. These are static checks, not penetration testing.
- **32 PostgreSQL tests collected; none executed**. One added test exercises real-schema export/erasure with external Storage/Auth calls explicitly mocked.
- Frontend files were unchanged in this pass. September 18's 14 frontend tests, build and three signed-out browser checks remain historical evidence; they were not rerun or represented as authenticated testing.
- Graphify AST update completed; its optional SQL parser remains absent.

## Synthetic document measurements

Three conversions per format on the local Windows host. Each generated document contains 300 fictional work notes and a final follow-up sentence. The benchmark checks that sentence survives normalization, splits the document, explicitly selects the matching section, and passes it through the application's context budget function. **It does not run vector ranking, Gemini, live user queries or a quality evaluation.**

| Format | Normalized characters | Conversion median | Chunks | Selected context characters | Reduction versus full normalized text |
|---|---:|---:|---:|---:|---:|
| DOCX | 31,454 | 2.15 s | 18 | 1,223 | 96.1% |
| PPTX | 32,777 | 2.25 s | 32 | 93 | 99.7% |
| PDF | 31,468 | 3.94 s | 18 | 1,223 | 96.1% |

Evidence was preserved in all three synthetic fixtures. DOCX's escaped Markdown underscore is normalized only for the benchmark comparison. Reported token estimates use characters/4 and are not measured provider tokens. Free-tier throughput, real PDF layouts, phone performance, model latency and semantic recall remain UNVERIFIED.

Reproduce: `apps/api/.venv/Scripts/python.exe scripts/benchmark_document_pipeline.py`. Local raw measurements: `.test-tmp/sep19-document-benchmark.json`. These results do not certify the hosted service's speed.

## External blockers and owner actions

1. **GitHub account lock:** after the implementation push, PostgreSQL check `105878646347` again reported, "The job was not started because your account is locked due to a billing issue." The user has said they will resolve it. Security check `105878646615` also failed before running. Clear the lock and rerun the latest branch workflows. No paid Gemini purchase is requested.
2. **Staging access/configuration:** no staging PostgreSQL DSN, Supabase service settings, Gemini key, or two test identities are available locally. Configure them in the provider dashboards or gitignored environment files using RUNBOOK.md; do not paste secrets in chat. No Supabase/Render/Vercel management connector is available in this session.
3. **Hosted backend:** public login scripts confirmed `https://taj-secondbrain-api.onrender.com/api/v1` as the web app's API. A fresh /health/live request timed out after 50.2 seconds. Inspect that Render service's deploy/startup logs and configuration; this is not proof of its exact failure cause. No production change was attempted.

After CI unlock: execute actual migrations, all 32 PostgreSQL tests and the restore drill; then verify Supabase A/B/anonymous Storage, real sign-in/refresh/logout, capture→relationship→retrieval→task, old-token denial after closure, external MCP and a real phone. Promote only the same tested revision, then repeat production identity and workflow checks. Original attachment export, indirect contact-reference review, provider backup retention and actual Storage recovery remain explicit limitations from PRODUCTION_READINESS.md.

Reference for permission-preserving database recovery: [PostgreSQL pg_dump documentation](https://www.postgresql.org/docs/current/app-pgdump.html) and [pg_restore documentation](https://www.postgresql.org/docs/current/app-pgrestore.html). PostgreSQL dumps do not include cluster roles or external Storage object bytes; provision roles and test Storage recovery separately.
