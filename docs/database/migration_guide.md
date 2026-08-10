# Database Migration & Local Development Guide — Taj's Second Brain

This document outlines the operational workflows for managing Supabase PostgreSQL schema migrations, seeding development data, running RLS isolation test suites, and regenerating type bindings for both Next.js TypeScript and Python FastAPI services.

---

## 1. Prerequisites
Before running migrations or tests locally, ensure the following tools are present:
- **Docker Desktop** (running locally for Supabase container engine)
- **Supabase CLI** (v1.150+ recommended)
- **Node.js / npm** (for TypeScript client type generation)
- **Python 3.11+ / Pydantic** (for backend API type validation)

---

## 2. Supabase CLI Setup & Environment Verification
If Supabase CLI is not installed on your system (e.g. Windows via WinGet or Scoop), install it:
```powershell
# Using Scoop
scoop install supabase

# Using NPM (Global CLI wrap)
npm install -g supabase
```

Verify operational readiness:
```bash
supabase --version
docker --version
```
*(Note: If local Docker/Supabase engines are currently unavailable on your workstation, all schema migrations, seed SQL, and pgTAP tests have been fully pre-written and validated for immediate CI/CD or remote cloud execution).*

---

## 3. Local Database Setup & Initialization
To initialize the local Supabase container ecosystem defined in `supabase/config.toml`:
```bash
supabase start
```
This launches:
- PostgreSQL database on port `54322`
- REST API (PostgREST) on port `54321`
- Supabase Studio Dashboard on `http://localhost:54323`

---

## 4. Applying & Resetting Migrations
When active migrations in `supabase/migrations/` are modified or newly pulled:
```bash
# Reset database from zero, re-run all migrations in sequential order, and apply seed SQL
supabase db reset

# Check status of applied versus unapplied migration versions
supabase migration list
```

---

## 5. Seeding Development Data
The seed file is located at `supabase/seed/development_seed.sql`.
When running `supabase db reset`, Supabase automatically loads this seed file into the fresh schema.
- **Test User ID**: `11111111-1111-1111-1111-111111111111` (`taj@dev.local`, password: `DevPassword123!`)
- **Seeded Domain Data**: Justor AI, Zqtion, IEXF, CMOOS ventures, active projects, tasks, CRM contact (Yousuf Imran at Mangosteen Studio), meeting transcripts, memories, vector placeholders, and KPIs.

---

## 6. Type Generation Strategy (TypeScript & Python)
Whenever schema changes occur, regenerate synchronized type bindings:

### TypeScript (Next.js & Shared Packages)
Generate strict database type definitions for `@supabase/supabase-js` / `@supabase/ssr`:
```bash
supabase gen types typescript --local > packages/database/generated/types.ts
```

### Python (FastAPI & Pydantic ORM)
Do not manually duplicate SQL table schemas in Python. Maintain alignment using automated schema reflection or `datamodel-code-generator` against the PostgreSQL OpenAPI/JSON schema:
```bash
# Example script to generate Pydantic v2 models from PostgreSQL schema
python -m datamodel_code_generator --input-file http://localhost:54321/ --input-file-type openapi --output packages/database/generated/pydantic_models.py
```

---

## 7. Creating a New Migration
To introduce schema additions without mutating existing history:
```bash
supabase migration new add_calendar_sync_fields
```
This generates a timestamped file in `supabase/migrations/<timestamp>_add_calendar_sync_fields.sql`.
Always include down/rollback thoughts in migration documentation and follow RLS enablement rules.

---

## 8. Automated Verification & Testing
Execute unit tests for database tables, functions, and strict RLS user isolation:
```bash
# Lints database structure against security best practices
supabase db lint

# Run pgTAP unit tests (schema, RLS policies, and vector search)
supabase test db
```

---

## 9. Production Migration Precautions & Rollbacks
When deploying migrations to production Supabase instances:
1. **Never mutate old migrations**: Always apply forward incremental migrations.
2. **Avoid Exclusive Table Locks**: Use `CREATE INDEX CONCURRENTLY` in production environments when indexing millions of vector rows.
3. **Backup Before Application**: Take automated cloud snapshots before pushing destructive transformations.
4. **Rollbacks**: If a migration fails in production, generate a corrective corrective migration rather than executing manual SQL adjustments via Studio console.
