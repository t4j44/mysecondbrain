# Second Brain V2 — staging integration checkpoint (2026-10-29)

Status: **REVIEW ONLY / PILOT NO-GO**. This document records direct read-only inspections of connected staging services. It is not permission to modify production or process real customer data.

## Exact candidate
- Candidate input commit: `75d12fec1c34139bfbc1c71a86d10bbf460bfd36` (PR #23). It contains the stacked PR #15–#23 work.
- Integration branch: `codex/v2-staging-release-integration-20261029`, forked from that exact commit. Re-review all changes and re-run exact-SHA CI for every subsequent commit.
- The canonical pilot ancestor is `codex/pilot-release-candidate-20261023` at `50890449cef9a68a73808383d12d257d0e1cb5aa`.
- `main` at inspection remains `5402a5e65fcb97295c19f090fdca1310b4497392` and is **diverged**: one main commit not in the V2 candidate. Do not force-update or blindly merge `main`.

## Connected infrastructure — observed, not inferred

| Layer | Ground truth at inspection | Action |
| --- | --- | --- |
| GitHub | PRs #15–#23 are draft and success on latest commit `75d12fec`: Security & Quality run 40868329315 and Postgres run 40868387864 | Consolidate for review, preserve PRs, refresh exact-SHA CI |
| Render staging API | service `srv-dbbjrp4s728c738mhsj0`, branch `codex/second-brain-release-hardening`, auto-deploy OFF, **live commit `ac7d4bf3b2aa899a0d5dbd458c9445f03ca98dbb`**; https://second-brain-api-staging.onrender.com | Do not claim V2 is deployed; only change branch/deploy after staging release and rollback plan |
| Supabase **staging** | `rpkjmdrralzxhdsgceal`, ACTIVE_HEALTHY, migrations through **36**; schema inspected: no V2 assistant/outbox tables yet | Back up and validate before additive migrations **37, 38, 39, 40**; never apply to other project `qvmrnnyjfofytplbnwco` |
| Vercel web staging | `second-brain-web-staging`, project `prj_r27R5j3Oss8GpNlHLZO58h0MA2uJ`, team `team_grch3Jv8NVqO7rmOBM3lKXES`. Project details inaccessible with **403**; listing works | Team authorization approval required; verify branch, ignored build step, env and frontend SHA before deploy |
| Telegram | Implementation on candidate is **default OFF** and only mocked provider CI evidence exists | Test with an explicitly consented dedicated bot/recipient on isolated staging, then enable behind gates |
| Google and external MCP | Source exists, external hosted acceptance unverified | Execute actual OAuth/read/write/revoke tests with synthetic accounts |

## Security observations
- Supabase staging security advisor reports six `rls_enabled_no_policy` informational notices on deliberately server-only vault-like tables. **Do not add client-facing policies to clear these notices.**
- `public.account_active(owner uuid)` has a SECURITY DEFINER callable by `authenticated`: evaluate intent, actual function body, effective grants and self-owner check before changing privileges; advisor: https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable
- Supabase leaked password protection disabled: evaluate plan availability/Auth policy before changing settings. Docs: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
- Review migration 37–40 tables and policies in a disposable PostgreSQL clone; check all references and account deletion flows.

## Gate sequence
1. Review candidate vs pilot branch and divergent main commit. Check checksum/branch safety and build artifacts. No change to production branch.
2. Resolve Vercel access through the authorized team grant; inspect and repair the staging ignored-build condition only once exact branch/project/env are confirmed.
3. Capture a restorable **staging** snapshot; validate migration 37–40 in a separate disposable database first, compare table/privilege/ownership results, then apply to approved isolated staging with rollback evidence.
4. Deploy an exact V2 **staging** API/web/worker SHA in controlled order, ensuring compatibility; keep integrations and outbound delivery OFF.
5. Run real two-synthetic-user login/RLS/private Storage, capture/recovery, model/provider recording, review/correction, MCP, export/erase and offsite restore checks.
6. Run dedicated opted-in Telegram bot test, validate messages, callbacks, STOP, quiet hours, uncertain delivery and no duplicates. Disable after acceptance unless release approval obtained.
7. Complete post-confirmation source correction propagation, update V2 91-case acceptance matrix, collect usability/device tests and real provider cost observations.
8. Produce GO/NO-GO owner sign-off. Do not activate billing, broadcast, process sensitive user data, merge main or promote production without explicit approval.

## Evidence boundary
Passing 573 backend / 110 frontend / 422 browser tests and 84 database tests per database state is valuable CI evidence at `75d12fec`. It does **not** replace real staging or provider acceptance. The existing 91-case acceptance ledger still has **1 PASS, 54 NOT_RUN, 36 BLOCKED** at inspection.

## Operator links
- Render staging: https://dashboard.render.com/web/srv-dbbjrp4s728c738mhsj0
- Supabase staging: https://supabase.com/dashboard/project/rpkjmdrralzxhdsgceal
- GitHub V2 head: https://github.com/t4j44/mysecondbrain/tree/codex/v2-meeting-preparation-20261029
- CI: https://github.com/t4j44/mysecondbrain/actions/runs/40868329315
- PostgreSQL: https://github.com/t4j44/mysecondbrain/actions/runs/40868387864

## Direct connected-service actions — second pass, 2026-10-29

**Render STAGING ONLY:** set `TELEGRAM_LINKING_ENABLED=false`, `ASSISTANT_OUTBOX_ENABLED=false`, `TELEGRAM_DELIVERY_ENABLED=false`, and `GOOGLE_INTEGRATIONS_RELEASE_VERIFIED=false` via merge-only environment update (`replace=false`). Render automatically triggered staging deploy `dep-dbhk0r142hec73cltmbg` for branch commit `e69a7c094d69c57e3040f274e800af37a52448a9`. It reached **live** at 2026-10-29T12:49:59Z. Render startup logs show Uvicorn initialization and app startup complete, but a successful hosted `/health/ready` response was not independently observed. Render platform live status is not V2 acceptance. This is not V2: the approved V2 candidate remains `75d12fec`.

**Supabase STAGING ONLY:** executed the read-only query now committed as `scripts/staging/v2_schema_readonly_preflight.sql` on project `rpkjmdrralzxhdsgceal`. It returned 0/7 new V2 tables present, 7/7 missing, no `commitments.revision`, server connection predicate and account active function present, and both existing Auth accounts and existing commitment data flagged present. An earlier aggregated preflight counted **3 auth users, 1 commitment, 0 meetings**. These are aggregate counts only; no user records or secrets were extracted. **No migration was applied**, because a restorable staging backup (including Auth/Storage) and exact compatible V2 web/API/worker deployment remain unverified.

**Security advisor verification:** `public.account_active(owner uuid)` is SECURITY DEFINER and callable by `authenticated` but its inspected function body explicitly checks `owner = auth.uid()` and excludes closed accounts. Preserve this intended self-owner check; do not blindly change function privileges or add client access to server-only tables based solely on advisory names. Evaluate effective grants in full before any privilege changes.

**Vercel STAGING ONLY:** project discovery works, but detailed project/deployment listing returns HTTP 403 for team `team_grch3Jv8NVqO7rmOBM3lKXES`. Team authorization is a user-controlled step. No Vercel setting, build configuration, or deployment was changed.

**Test evidence:** The integrated review PR CI passed at `73a415a` prior to adding the read-only SQL script. New exact-SHA CI must be observed for subsequent commits. Do not count any of the connected-service reads above as a completed 91-case pilot release test.
