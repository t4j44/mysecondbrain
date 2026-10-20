# Isolated staging operator runbook

**Production readiness: NO. Do not deploy this candidate to production.** The owner
has no verified staging Supabase project and forbids using production credentials,
database or storage for tests. The next human step is creating a separate project
and providing ONLY its URL/ref. Put secrets directly into provider secret stores.
No paid plan, hosted migration, deployment, production change or merge is performed
by these instructions automatically.

## 1. Supabase — next owner action

1. Open Supabase dashboard → organization → **New project**. Name it
   `second-brain-staging`; choose a region near the intended Render service. Confirm
   any cost before creation. Use a new database password saved in your password
   manager, never production's password.
2. Project → **Settings / General**: copy the project ref. **Connect / API**: copy
   project URL `https://<staging-ref>.supabase.co`. Compare with the production ref;
   they must differ. Supply only this staging URL/ref in chat. Provisioning and
   connection acceptance remain BLOCKED until that identity is provided.
3. **Settings / API keys**: enter the publishable key into staging Vercel and GitHub
   environment secret `BETA_SUPABASE_PUBLISHABLE_KEY`. Enter the server secret into
   staging Render only (`SUPABASE_SECRET_KEY`); never the browser or chat.
4. **Connect**: store a staging-only database URI in Render `DATABASE_URL`, using
   `postgresql+asyncpg://` and percent-encoded password. Choose a reachable direct
   IPv6 connection or the dashboard-provided session pooler; asyncpg requires a
   compatible connection mode. Do not assume transaction-pooler/prepared-statement
   support. Verify TLS/target privately and do not paste the URI into evidence.
5. **Authentication / URL configuration**: set the staging web URL as Site URL;
   allow only its `/callback` and `/reset-password` redirect routes. Create two
   ordinary synthetic email/password users A/B under **Authentication / Users**.
   Confirm their emails for the test. Neither is an administrator/service account.
6. **Storage / Buckets**: after migrations, verify `meeting-audio` and the existing
   document/context buckets are private, with owner-prefix policies and active
   account checks. Migration 32 sets audio size/MIME constraints. Check with user
   JWTs and direct object requests; a service key bypassing RLS proves nothing.

## 2. Migration and database preparation — after identity approval

There are **35** canonical SQL files, ordered by filename, including historical
`20260828000021b_mcp_work_session_finalization_objects.sql`. Latest:

- `20261008000032_meeting_intelligence.sql`
- `20261013000033_google_multi_account.sql`
- `20261013000034_email_contacts.sql`

This release adds **zero** migrations. Notes/history/review use existing JSON;
structured output/checkpoints use existing capture intelligence JSON. Do not edit
old files, invent migration 33, reset main, or replay bootstrap over existing data.

Before applying anything, record target hostname/ref, backup status, existing
public table list and migration history. Match `app/db/schema_contract.MIGRATION_FILES`
against every filename. The historical `21b` name is not a numeric Supabase CLI
timestamp: **do not blindly run `supabase db push` over this ledger**. Existing
repository bootstrap executes the exact ordered file manifest and validates schema.
It requires an empty public schema and explicit `BOOTSTRAP_ALLOW_ISOLATED=1` for
remote targets. Review its auth shim/grants against Supabase first; it must not
replace native auth helpers. Only use it after the separate target is approved and
proved empty, with `POSTGRES_TEST_DATABASE_URL` loaded privately for that operation:

```powershell
$env:BOOTSTRAP_ALLOW_ISOLATED='1'
python scripts/db/bootstrap_migrations.py
```

For a nonempty staging target, stop: reconcile its actual ledger and apply only
reviewed missing files individually through the approved migration operator. Keep
file SHA256 receipts. Never use destructive test reset/restore scripts on hosted
Supabase. Fresh/upgrade/backup-restore CI uses a disposable local pgvector container;
hosted Auth/Storage and encrypted backup/object recovery still need separate proof.

## 3. Render — separate staging API and durable worker

Dashboard → **New / Web Service** → connect `t4j44/mysecondbrain` → choose the exact
verified `codex/second-brain-release-hardening` revision. Name
`second-brain-api-staging`; runtime **Docker**, root directory `apps/api`, Dockerfile
`Dockerfile`; health check `/health/ready`. Disable automatic deploys while reviewing
the release. Do not repoint the existing production service.

The API's existing supervised durable worker runs when `JOB_WORKER_ENABLED=true`.
One always-running API instance is the initial staging topology; it avoids inventing
another worker entrypoint. Render Free sleep cannot guarantee unattended jobs.
If only free infrastructure is approved, document manual wake-up and mark unattended
processing BLOCKED. An always-running paid instance needs explicit budget approval.
An API and any separate approved worker must use the same SHA, database and settings;
verify each worker's restart/reclaim before claiming reliable background processing.

Set staging secrets in **Environment**, using `.env.example` names only:

| Setting | Staging value/requirement |
|---|---|
| `APP_ENV`, `ENVIRONMENT` | `staging` |
| `DATABASE_URL` | Staging asyncpg URI; no production key |
| `DATABASE_SCHEMA_VERIFY` | `true` |
| `SUPABASE_URL`, `SUPABASE_SECRET_KEY` | Dedicated staging project only |
| `JWT_SECRET`, `TOKEN_ENCRYPTION_KEY` | Two independent fresh random values, 32+ characters |
| `SUPABASE_JWKS_URL` | Derives from staging URL; set only if necessary |
| `FRONTEND_URL` | Exact staging HTTPS web origin |
| `CORS_ORIGINS`, `CORS_ALLOWED_ORIGINS` | JSON array of exact staging web origins, no wildcard |
| `MCP_ISSUER_URL` | Staging API HTTPS origin |
| `MCP_RESOURCE_SERVER_URL` | Same origin plus `/mcp` |
| `MCP_ALLOWED_HOSTS` | JSON array containing only staging API host (and approved custom staging host) |
| `JOB_WORKER_ENABLED` | `true` on the supervised runtime |
| `RELEASE_SHA` | Exact 40-character candidate SHA; Render's `RENDER_GIT_COMMIT` is fallback |
| `GEMINI_API_KEY` | Separate approved staging project credential |
| `AI_DATA_MODE` | `free_redacted` for non-personal synthetic audio only |
| `GEMINI_MODEL` | `gemini-2.5-flash`, verify project access before acceptance |
| `GEMINI_TRANSCRIBE_MODEL` | `gemini-3.5-transcribe`, verify actual project access |
| `GEMINI_LIVE_TRANSCRIBE_MODEL` | `gemini-3.5-transcribe-live`, verify actual streaming access |
| `GEMINI_EMBEDDING_MODEL`, `AI_EMBEDDING_DIMENSIONS` | `gemini-embedding-001`, `768` |
| `MEETING_EXTRACTION_MAX_BATCHES` | `80` default; monitor actual requests/tokens |
| `MEETING_AUDIO_*`, `MEETING_LIVE_SESSION_SECONDS` | Keep reviewed defaults: 18,000s/month, 7 days, 50MB, bucket `meeting-audio`, live 540s |
| `MEETING_PRIVATE_AUDIO_RELEASE_VERIFIED` | `false` pending privacy/plan/provider acceptance |
| `GOOGLE_INTEGRATIONS_RELEASE_VERIFIED` | `false` pending real OAuth/sync acceptance |
| `PORTFOLIO_PUBLISHING_RELEASE_VERIFIED` | `false` pending publication/revoke acceptance |

Never choose `paid_private` merely to bypass an audio warning: it does not activate a
private plan. Owner must verify provider project terms/billing and approve cost.
Unpaid audio is not redacted; the UI attestation permits non-sensitive synthetic
samples, not confidential meetings. Provider terms and model access must be checked
again at execution, not inferred from model names or mocked tests.

After authorized staging deploy, record `/health/live`, `/health/ready`, `/health`
and the exact release SHA; verify FFmpeg/FFprobe inside the deployed image. Investigate
timeouts via service event/build logs, startup schema, hostname, env and database
reachability. Do not label a timeout a cold start without evidence.

## 4. Vercel — separate staging project

Dashboard → **Add New / Project** → import same repo as a separate project named
`second-brain-web-staging` → framework Next.js → root `apps/web`, Node 22, install
`pnpm install --frozen-lockfile`, build `pnpm --filter @second-brain/web build`.
Verify monorepo workspace root detection and the shared-types package. Select the
verified release branch/revision; do not change the production project's branch.

The candidate's `apps/web/vercel.json` disables automatic Git deployments for this
branch so a push for CI cannot accidentally use the existing project's environment.
After the separate staging project is identified, deploy it explicitly from the
verified checkout using the staging project's identity; inspect `vercel deploy --help`
for the installed CLI and verify project linkage before running any deployment.
Do not remove the guard in the existing project to make a preview appear.

Set only browser-safe staging values in that project's environment:
`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`,
`NEXT_PUBLIC_API_BASE_URL=https://<staging-api>/api/v1`,
`NEXT_PUBLIC_SITE_URL=https://<staging-web>`, `NEXT_PUBLIC_APP_ENV=staging`.
Never set database/service/encryption secrets in Next public variables. Enter its
final origin into Supabase redirects and Render CORS. Inspect the deployment's Git
commit in Vercel and compare with API `/health` before acceptance.

## 5. Acceptance execution

GitHub repo → **Settings / Environments / beta-staging**. Variables:
`BETA_WEB_URL`, `BETA_API_URL` (include `/api/v1`), `BETA_SUPABASE_URL`,
`BETA_SUPABASE_PROJECT_REF`, `PRODUCTION_SUPABASE_PROJECT_REF` (identity only).
Secrets: `BETA_SUPABASE_PUBLISHABLE_KEY`, `E2E_EMAIL`, `E2E_PASSWORD`,
`E2E_EMAIL_B`, `E2E_PASSWORD_B`. Credentials belong only to disposable users.
**Actions / Closed beta staging E2E / Run workflow** → exact release branch.
Missing/matching refs fail closed; do not point workflows at production. Reports
exclude auth-state files; keep any locally produced traces private and short lived.

For direct Storage isolation, privately populate these script environment names:
`RUN_MEETING_STAGING_SMOKE=1`, `MEETING_SMOKE_STAGING_CONFIRMED=1`,
`MEETING_STAGING_API_URL`, `MEETING_STAGING_SUPABASE_URL`,
`MEETING_STAGING_PUBLISHABLE_KEY`, `BETA_SUPABASE_PROJECT_REF`,
`PRODUCTION_SUPABASE_PROJECT_REF`, `MEETING_SMOKE_RELEASE_SHA`,
`MEETING_SMOKE_USER_A_TOKEN`, `MEETING_SMOKE_USER_B_TOKEN`.
Run `python apps/api/scripts/meeting_staging_storage_smoke.py`. This writes/deletes
one synthetic WAV, never finalizes or calls AI; verify physical cleanup completes.

For actual provider smoke, use a consented non-personal bilingual file:
`RUN_MEETING_PROVIDER_SMOKE=1`, `MEETING_SMOKE_AUDIO`, optional
`MEETING_SMOKE_MIME`, `MEETING_SMOKE_DATE`, approved `GEMINI_API_KEY`; run
`python apps/api/scripts/meeting_provider_smoke.py`. It calls the provider but writes
no application records; it does not prove streaming, database RLS or phone capture.
No call has been run for this candidate without these prerequisites.

Record each master-spec hosted journey with PASS/FAIL/BLOCKED, exact web/API/worker
SHA, synthetic user identity, route, counts and redacted evidence: sign-in; cards/
moments; explicit outreach sent/outcome; documents/MarkItDown/OCR; Ask; external
MCP OAuth/read/draft/context/finalize/revoke; 60–90 minute bilingual meeting with
secondary topic; two-user audio/graph/export denial; partial retry; worker restart;
deletion/index invalidation/object erasure; export/closure. Google and portfolio
remain visibly disabled unless live tests justify separately enabling their flags.

Physical HTTPS Android/iOS acceptance must cover permission denial, record/pause/
resume, reconnect/offline, refresh/recovery, background limitations, end/upload,
worker completion, five outputs, evidence seeks, selective confirmation and cited
retrieval. Browser fixtures alone never pass this gate. Measure source omissions,
speaker errors, conditional/deadline errors, processing latency/provider usage and
slow-data behaviour; do not invent achieved p95 or cost.

## 6. Operations, dogfood and release boundary

Monitor health/SHA, error/request IDs, pending/processing job age and retry counts,
failed extraction/indexing/erasure, quota consumption, retained audio and Storage
orphans. Logs/evidence must exclude tokens and raw meeting text. Alert thresholds
need actual staging baseline: measure completion/latency/usage first. Review failed
jobs with owner-scoped tools; never replay deleted sources or blanket reset jobs.
Document encrypted backup access/retention and restore into a different isolated
target, including Auth and private-object copies; CI SQL restore is only one part.

Proposed beta measurement plan (owner must approve targets): 7 consecutive days
personal dogfood, then 10–15 consented users; report denominators for every metric.
Track capture→processed success, useful summaries, unsupported claims per reviewed
claim, corrected CRM/task items, relevant document/meeting citations, MCP connect/
revoke success, explicit outreach completion and seven-day return. Collect all
failures, not just successful demos. No achieved values or release SLOs are claimed.

Only after clean CI, isolated staging/security/provider/phone/recovery acceptance:
open a reviewed release PR to stale main, inspect full ancestry/migration impact;
obtain owner authorization for dogfood deployment, beta and eventual production.
Before production: verified backup/restore, agreed runtime budget/privacy, compatible
worker and matched SHAs, then explicit owner cutover approval. Never merge/deploy
implicitly. Roll back application revisions via hosting revision controls after
owner approval; keep compatible processing/retention/deletion workers until queued
work is drained. Never delete data or reverse old migrations to simplify rollback.
