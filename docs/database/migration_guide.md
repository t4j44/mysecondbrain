# Database migration and recovery guide

The canonical schema is `supabase/migrations`; `app/db/schema_contract.py` lists the expected files and critical types/policies. Deployment must use migrations, never SQLAlchemy `create_all`. Keep `DATABASE_SCHEMA_VERIFY=true`.

## V1.5 changes

After the V1 ledger through migration 28:

1. `20260927000029_context_events.sql`: owner-scoped source events, original and recorded times, raw source, privacy classification, private media metadata, temporal graph history and composite owner foreign keys.
2. `20260927000030_outreach_receipts.sql`: separate opened/sent receipt actions; opening an external app does not record delivery.
3. `20260927000031_mcp_oauth.sql`: registered clients, pending requests, owner grants, hashed codes/tokens. Only grant metadata is readable by the authenticated owner; other vault tables are server-only.

These migrations are additive except replacing the graph's all-history uniqueness constraint with uniqueness for current edges. Existing edges keep their original created/recorded time. They do not migrate existing provider secrets or change AI billing mode.

## Existing isolated staging

Verify the target project, backup and applied migration ledger first. Apply only outstanding migrations in filename order with the project's normal migration process. Do not replay historical files, reset a populated database, or treat the empty-database bootstrap script as an incremental migration command. Validate schema on backend startup and compare `/health` release SHA with both deployment records. Apply database changes before deploying code that requires them.

No hosted migration or production change is authorized by the local test commands below. Stage and verify before dogfood or production promotion. Rolling the application back does not require immediately removing the additive tables; do not drop private records to roll back code. Restore from a verified backup only as a separately reviewed recovery operation.

## Disposable PostgreSQL evidence

Docker is optional on the developer workstation. GitHub's `PostgreSQL tenant and schema gate` creates PostgreSQL 16 with pgvector and runs the scripts below. A locally installed PostgreSQL/pgvector server can also be used. Set `POSTGRES_TEST_DATABASE_URL` in the environment to an empty disposable test database and install `apps/api/requirements.txt`.

```text
python scripts/db/bootstrap_migrations.py
pytest apps/api/tests/integration -q -o addopts= --junitxml=postgres-results.xml
python scripts/check_test_evidence.py postgres-results.xml
```

Bootstrap refuses a populated public schema and production-looking targets. Remote empty staging requires explicit `BOOTSTRAP_ALLOW_ISOLATED=1`; prefer CI for routine proofs.

The additional scripts require a loopback server, an explicitly named test database and their own opt-in environment flags:

```text
RUN_ISOLATED_UPGRADE_PROOF=1
python scripts/db/verify_v15_upgrade.py
RUN_ISOLATED_RESTORE_PROOF=1
python scripts/db/verify_backup_restore.py
```

Set flags using the shell's environment syntax (PowerShell: `$env:RUN_ISOLATED_UPGRADE_PROOF = '1'`). Each script creates and drops only its own uniquely generated disposable database. Upgrade starts from migrations 1–28 with seeded V1 records, applies 29–31 and verifies retained history before rerunning integration tests. Restore uses real `pg_dump`/`pg_restore` and reruns the same integration suite. Install matching PostgreSQL 16 client tools for recovery checks.

CI retains `postgres-results.xml`, `upgrade-results.xml`, and `restore-results.xml`. Empty, failed or skipped evidence is rejected. Read the [V1.5 release report](../beta/V1_5_RELEASE.md) for actual results; code existence is not proof that these passed.

## Boundaries

SQLite tests exercise application behavior but cannot certify PostgreSQL types, RLS, pgvector or migration compatibility. The container's minimal auth shim does not certify hosted Supabase Auth or Storage. Database dumps do not contain uploaded Storage bytes, external Google files/events or provider settings. Portable account JSON exports also exclude binary attachments and OAuth vault material.

Keep dumps private, encrypted and outside Git; the scripts do not encrypt them. Private photo erasure is queued, so the worker and retry monitoring must be active. See [beta runbook](../beta/RUNBOOK.md) for hosted two-account acceptance and [data inventory](../privacy/data_inventory.md) for deletion/export behavior.
