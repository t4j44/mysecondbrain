# SECOND BRAIN — VERIFIED RELEASE STATUS

Evidence checked September 19, 2026. **The code and disposable PostgreSQL gates pass. Hosted daily use and the 10–15-user pilot remain blocked by staging access and unverified hosted behavior.** Gemini Free Tier remains selected; no paid AI decision is required.

## Revision and CI

- Branch: `codex/free-tier-beta`; no merge to main or manual production promotion.
- Verified implementation local/remote SHA: `6f48bd506be48855fcf3562353cf457a77229df1`.
- Separate pnpm-only commit: `9c2244931ff9dd617ae835dd06eb94fa9fb9a2fc` (`fix(ci): pin pnpm 10 for GitHub Actions`).
- Vector-query commit: `6f48bd506be48855fcf3562353cf457a77229df1` (`fix(rag): qualify pgvector distance operator schema`).
- Security CI: **PASS**, [run 35457303815](https://github.com/t4j44/mysecondbrain/actions/runs/35457303815).
- PostgreSQL CI: **PASS**, [run 35457303790](https://github.com/t4j44/mysecondbrain/actions/runs/35457303790).
- This report is a later documentation-only commit. Its SHA is discoverable with `git log -1 --format=%H -- docs/beta/VERIFIED_RELEASE_SEP19.md`; the application evidence above identifies the exact tested implementation.
- Latest repository migration: `20260917000026_account_closure_and_storage.sql`. The entire chain applied in disposable CI PostgreSQL; the latest hosted migration is **UNVERIFIED**.
- Staging SHA: **UNVERIFIED**. Render SHA: **UNVERIFIED**.
- Vercel: GitHub reported a successful automatic deployment for implementation SHA `6f48bd506be48855fcf3562353cf457a77229df1`, [deployment record](https://vercel.com/thenadish-4808s-projects/mysecondbrain-web/2TWyqpa5EHcWpgjEPgTxAZFGrSjr). Its environment/domain and the production domain's SHA were not verified because the dashboard requires sign-in. This is not a same-SHA production certification.

## Failures, fixes and verification

| Failure | Root cause | Fix | Verification |
|---|---|---|---|
| pnpm setup aborted with `onlyBuiltDependencies?.sort is not a function` | `.npmrc` supplied a comma-separated string where pnpm expected a list; workflows also selected pnpm 11 | Pin root `packageManager` and both frontend workflows to 10.17.1; move the two allowed build dependencies to the workspace YAML list; retain the tesseract.js exclusion using the pnpm 10 setting | Node 22, frozen install, unchanged lockfile, lint, typecheck, 14 tests and build pass locally and in GitHub |
| Real PostgreSQL semantic search failed | The query used bare `<=>`, while canonical migrations install pgvector in `extensions`; the connection search path omitted it | Use `OPERATOR(extensions.<=>)` without changing schema or tenant filters | Regression runs with both `public` and `public, extensions`; verifies actual score, owner filtering, stale-index exclusion and deleted-record exclusion |
| First local backend rerun had five fixture errors | Windows denied pytest access to its shared temporary directory | Rerun with a unique temporary directory inside the workspace | Fresh result: 214 passed, zero failures/errors/skips |
| First local frontend build failed fetching fonts | Restricted build process could not reach existing Google Fonts dependencies | Rerun with network access; no font or app change | Production build passed |
| Hosted backend did not respond | Root cause remains unknown without Render service logs/configuration | No speculative production change | `/health` and `/health/live` each timed out after 45.4 seconds; web `/login` returned 200 in 1.8 seconds |

The GitHub billing lock is resolved: real job steps ran. Earlier reports describing that lock or unexecuted PostgreSQL tests are historical. [pnpm 10 documents the list settings](https://pnpm.io/10.x/settings); [PostgreSQL documents schema-qualified operators](https://www.postgresql.org/docs/16/ddl-schemas.html).

## Verification matrix

PASS in a test column means the stated checks passed, not exhaustive certification. PARTIAL explicitly limits the evidence. BLOCKED means required credentials/access are unavailable. No hosted workflow is inferred from local tests.

| Area | Implemented | Local | Real Postgres | Staging | Production | Verdict |
|---|---|---|---|---|---|---|
| Database | YES | PASS contract checks | PASS migrations/contract | BLOCKED | NOT TESTED | PARTIAL |
| Auth | YES | PASS token/closure tests | PARTIAL claims/role shim | BLOCKED | NOT TESTED | PARTIAL |
| RLS | YES | PASS identity helpers | PASS ownership/pooling policies | BLOCKED | NOT TESTED | PARTIAL |
| Storage | YES | PASS mocked provider/local disk | NOT TESTED provider | BLOCKED | NOT TESTED | PARTIAL |
| Relationships | YES | PASS service tests | PASS constraints/backfills/isolation | BLOCKED | NOT TESTED | PARTIAL |
| Capture | YES | PASS reviewed capture tests | PARTIAL related persistence | BLOCKED | NOT TESTED | PARTIAL |
| MarkItDown | YES | PASS synthetic formats/guards | N/A | BLOCKED | NOT TESTED | PARTIAL |
| Documents | YES | PASS extraction/chunk/fallback tests | PARTIAL schema/vector tables | BLOCKED | NOT TESTED | PARTIAL |
| Embeddings | YES | PASS mocked provider boundary | PASS explicit test vectors | BLOCKED live Gemini | NOT TESTED | PARTIAL |
| RAG | YES | PASS bounded-context/fallback tests | PASS ranking and visibility regression | BLOCKED live Gemini | NOT TESTED | PARTIAL |
| Ask | YES | PASS structured routing/source tests | PARTIAL retrieval dependency | BLOCKED | NOT TESTED | PARTIAL |
| MCP | YES | PASS auth/tools/local transport | PASS finalize/idempotency | BLOCKED external client | NOT TESTED | PARTIAL |
| Privacy | YES | PASS minimization/restoration tests | PARTIAL tenant/closure policies | BLOCKED | NOT TESTED | PARTIAL |
| Deletion | YES | PASS failure/retry/token denial tests | PASS canonical erasure/closure restrictions | BLOCKED provider erasure | NOT TESTED | PARTIAL |
| Export | YES | PASS owner scope/credential stripping | PASS real-schema archive | BLOCKED | NOT TESTED | PARTIAL |
| Portfolio | YES | PASS approved snapshot/revocation | PARTIAL schema | BLOCKED | NOT TESTED | PARTIAL |
| Mobile | YES | NOT TESTED authenticated device flow | N/A | BLOCKED | NOT TESTED | PARTIAL |
| Backup | YES | PASS recovery guards | PASS real dump/restore and restored suite | BLOCKED hosted recovery | NOT TESTED | PARTIAL |
| CI | YES | PASS frontend/backend checks | PASS real DB and restore jobs | BLOCKED authenticated E2E | N/A | PARTIAL |
| Observability | YES | PASS health contract tests | PARTIAL schema readiness | BLOCKED | FAIL backend health probe | PARTIAL |
| Drive | YES, optional export | PASS mocked provider tests | N/A | NOT TESTED | NOT TESTED | PARTIAL |
| Calendar | YES, optional task sync | PASS mocked provider tests | N/A | NOT TESTED | NOT TESTED | PARTIAL |

## Test totals and actual PostgreSQL results

- Local: **214 backend tests passed**, zero failures/errors/skips; **14 frontend tests passed**; lint, typecheck and production build passed under Node **22.23.2** and pnpm **10.17.1**. The lockfile was not regenerated.
- Security CI on the implementation SHA: **214 backend tests passed** (47.59 seconds), **14 frontend tests passed**; Ruff, Bandit, mypy across **140 files**, frontend lint/typecheck/build passed. Bandit found zero issues; this is static scanning, not a penetration test.
- PostgreSQL CI: **33 collected/executed, 33 passed, 0 failed, 0 skipped**, 3.57 seconds. The additional case tests the second search-path configuration; the previous 32-test run had 31 passed and one genuine query failure.
- Restored PostgreSQL: **33 executed, 33 passed, 0 failed, 0 skipped**, 3.45 seconds. Evidence validators explicitly reported no skips or failures for both suites.
- The 33 restored tests repeat the same integration cases; they are not 33 additional distinct tests. Total distinct automated cases across backend unit, frontend unit and PostgreSQL integration: **261**.
- PostgreSQL JUnit artifacts: `postgres-test-evidence`, artifact ID `10588508997`, containing `postgres-results.xml` and `restore-results.xml`. No private production data was used.

The real database checks cover schema tables/columns/foreign keys, vector dimensions, relationship constraints/backfills, cross-owner read/update/delete/insert denial, identity removal on commit and pooled connections, token-vault restrictions, per-owner idempotent MCP finalization, export and account erasure. The database uses Supabase-compatible auth role/function shims, not the hosted Supabase Auth service.

## Hosted and subsystem evidence boundaries

- **RLS:** database ownership and transaction identity checks pass. RLS means database rules restricting each user to their own records. Real Supabase JWT, anonymous HTTP and Storage policies still need staging execution.
- **Storage:** actual Supabase A/B/anonymous upload/read/update/delete and signed-link behavior have not run. Local provider mocks cannot establish them.
- **Auth:** live sign-in, refresh, logout, expired token rejection and old hosted JWT denial after closure remain untested.
- **MarkItDown:** 14 normalization tests pass, including supported synthetic text/Office/PDF conversions, unsafe archive rejection, chunk metadata and bounded excerpts. Earlier local three-run median conversions were DOCX 2.15 s, PPTX 2.25 s and PDF 3.94 s; those measurements were inspected, not rerun in this checkpoint. They do not measure live model quality or hosted throughput.
- **RAG:** real vector storage/search now passes with explicit synthetic vectors. Gemini is mocked in that integration test. Real Gemini embeddings, semantic recall, grounded answer quality, measured tokens and 10–15-user free-tier capacity remain unverified.
- **MCP external client:** local authenticated transport and database finalization pass; no actual ChatGPT/Claude/Gemini client connection, retrieval or revocation was verified.
- **Account deletion:** canonical database export/erasure and account-active restrictions pass on PostgreSQL. The erasure test explicitly mocks Supabase Storage and Auth deletion. Actual provider erasure and old hosted JWT/MCP denial remain blocked.
- **Backup/restore:** the real PostgreSQL drill dumps the migrated database, restores into a uniquely named empty database, verifies exact synthetic record contents and owner/foreign visibility, then runs all 33 integration tests on the restore. It preserves grants. This does not back up or restore Storage object bytes or certify hosted Supabase Auth recovery.
- **Mobile:** no actual Android Chrome device was available for authenticated capture/photo/upload/keyboard checks. Existing responsive UI or browser emulation is not physical-device proof.
- **Deployment SHAs:** implementation local/remote match is verified. GitHub reports a Vercel deployment for that SHA; production Vercel SHA, Render SHA and staging SHA remain unverified. No merge or manual production promotion was performed.

## Known limitations

Free-tier redaction reduces exposure but is not guaranteed anonymization; avoid highly sensitive/confidential input. Provider mode can later change through configuration; changing embedding model or data mode requires reindexing. Original attachment bytes are excluded from JSON/CSV/Markdown export and PostgreSQL dumps. Scanned PDFs need OCR; document and context size limits remain. Drive export and one-way Calendar task sync are optional and lack live OAuth verification. Portfolio revocation cannot retract recipients' copies. No real-user retention, usefulness or testimonials are claimed.

## Owner actions and exact blocker

Render, Supabase and Vercel each showed sign-in pages in the available in-app browser. The discovered Chrome connection could not be opened. There is no callable hosting/Supabase management connector and no local staging DSN, Gemini key, server Supabase credentials or test-user credentials. This does not prove the hosted services lack configuration; their configuration could not be inspected.

**Next owner action:** sign in to the three provider dashboards in the Codex in-app browser and identify the isolated staging project/web/API URLs. Do not paste secrets into chat. If no staging project exists, state that before any migration or synthetic erasure test. Required private configuration belongs in provider dashboards or ignored environment files, as listed in [RUNBOOK.md](RUNBOOK.md).

Once access exists, the remaining release gates are real Supabase Auth/Storage isolation, Gemini retrieval and core authenticated E2E, provider account erasure/recovery, external MCP, actual Android Chrome, and a healthy deployment with matching tested SHAs. Additional local reruns cannot replace those checks. Optional Drive/Calendar do not block the core pilot if disabled.

READY FOR TAJ DAILY USE:
NO
- Hosted backend health is failing to respond; staged identity, Storage, core workflows and deployed SHA are unverified.

READY FOR 10–15 USER PILOT:
NO
- Daily-use blockers plus live Gemini/free-quota behavior, external MCP, hosted erasure/recovery and actual Android Chrome remain unverified.

NEXT ACTION:
- Restore signed-in access to the isolated staging providers so the hosted verification gates can run.
