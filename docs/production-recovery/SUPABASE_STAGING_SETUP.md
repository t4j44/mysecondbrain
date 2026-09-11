# Supabase Staging Setup (Manual Actions Only)

**Scope:** Human actions required to stand up a **non-production** Supabase staging project for this repository.  
**Do not:** use production, invent secrets into git, deploy, or change schema outside existing migrations.

Prep artifacts already in the repo:

| Artifact | Path |
|---|---|
| API env template | `apps/api/.env.example` → copy to `apps/api/.env` |
| Web env template | `apps/web/.env.local.example` → copy to `apps/web/.env.local` |
| E2E env template | `apps/web/e2e/.env.local.example` → copy to `apps/web/e2e/.env.local` |
| Staging smoke | `scripts/staging/supabase_staging_smoke.py` |
| Migrations | `supabase/migrations/` (canonical order in `apps/api/app/db/schema_contract.py`) |

---

## 1. Create a separate staging project

1. In the Supabase dashboard, create a **new** project whose name clearly identifies staging.
2. Do **not** reuse the production project, project ref, database password, Auth users, or Storage buckets.
3. Record privately (password manager only): project URL, project ref, database host, database password, publishable/anon key, and secret/service_role key.
4. Confirm Auth is enabled for the project.

## 2. Enable required extensions

In the staging project SQL editor (or via linked CLI), ensure these extensions are available (migration `20260811000001_enable_extensions.sql` also requests them):

- `vector` (pgvector)
- `pgcrypto`
- `uuid-ossp`
- `citext`
- `pg_trgm`

## 3. Apply repository migrations in order

Apply every file under `supabase/migrations/` in the order listed by `apps/api/app/db/schema_contract.py` (currently through `20260828000023_align_canonical_columns_with_application_contract.sql`).

Options:

- Supabase CLI linked to the **staging** project, or
- SQL editor: paste/run each migration file in order, or
- From a private shell only (after you attest the DSN is staging, never production):

```powershell
$env:POSTGRES_TEST_DATABASE_URL = "postgresql+asyncpg://postgres:<STAGING_DB_PASSWORD>@db.<STAGING_PROJECT_REF>.supabase.co:5432/postgres"
python scripts/db/bootstrap_migrations.py
```

Do not continue if bootstrap refuses the target, reports migration contract drift, or fails schema validation.

## 4. Create Storage bucket

In staging Storage, create a **private** bucket named exactly:

```text
brain-documents
```

Do not point staging at a production bucket.

## 5. Create two staging Auth users

In Authentication → Users for the **staging** project only:

| Role | Purpose |
|---|---|
| User A | Primary smoke / E2E operator (`E2E_EMAIL` / `E2E_PASSWORD`) |
| User B | Cross-tenant denial (`E2E_EMAIL_B` / `E2E_PASSWORD_B`) |

Confirm both users can sign in (email confirmed if the project requires confirmation).

## 6. Fill local ignored env files

Copy templates and replace placeholders privately:

```powershell
Copy-Item apps\api\.env.example apps\api\.env
Copy-Item apps\web\.env.local.example apps\web\.env.local
Copy-Item apps\web\e2e\.env.local.example apps\web\e2e\.env.local
```

Required concepts (names must match application code):

**API (`apps/api/.env`)**

- `DATABASE_URL`
- `POSTGRES_TEST_DATABASE_URL` (same staging DB for integration/bootstrap)
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `APP_ENV=staging`
- `ENVIRONMENT=staging`
- `DATABASE_SCHEMA_VERIFY=true`
- Distinct `JWT_SECRET` and `TOKEN_ENCRYPTION_KEY` (not production values)

**Web (`apps/web/.env.local`)**

- `NEXT_PUBLIC_API_BASE_URL` (include `/api/v1`)
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_APP_ENV=staging`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

**E2E (`apps/web/e2e/.env.local`)**

- `E2E_EMAIL` / `E2E_PASSWORD`
- `E2E_EMAIL_B` / `E2E_PASSWORD_B`
- `PLAYWRIGHT_TEST_BASE_URL`

Never commit those filled files. They are gitignored.

## 7. Safety attestation before any DB/API use

Before setting shell variables or starting the API:

1. Compare the connection-string host/project ref to the staging dashboard by eye.
2. Compare against your private production project ref — a matching ref is still production.
3. Confirm Auth users and the `brain-documents` bucket belong to staging.
4. Privately record: “I verified the target project ref is staging and is not production.”

Do not paste passwords or full DSNs into chat, git, or tickets.

## 8. Run the staging smoke (after API is up locally)

With the API pointed at staging Postgres/Auth (local process only — this doc does not deploy):

```powershell
python scripts/staging/supabase_staging_smoke.py
```

Expect `SUPABASE STAGING SMOKE = PASS`. Exit code `2` means env is incomplete (blocked, not invented). Non-zero other codes are failures.

Optional deeper DB checks (same staging DSN only):

```powershell
pytest apps/api/tests/integration/test_rls_cross_tenant.py -m postgres
```

## 9. What you do not do in this gate

- Do not deploy to Render/Vercel.
- Do not change production.
- Do not invent or commit secrets.
- Do not alter schema except by applying existing migrations.
- Do not weaken RLS policies.
