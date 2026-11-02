# Second Brain — 5–10-user free invite-only beta acceptance

**Status:** NOT YET OPEN. Operate only in staging until each P0 gate is supported by exact-run receipts. Launch decision belongs to [issue #32](https://github.com/t4j44/mysecondbrain/issues/32).

## P0 release stops — do not invite anyone until all PASS

1. **Credential rotation:** Supabase staging database connection was observed in a tool output on 2026-11-02. Treat as exposed. Rotate the database credential through an authorized dashboard session; securely update Render and every worker/backup consumer without printing values; confirm Render `/health/ready` = 200 and authenticated access restored. Do not rotate during a running database dump or tests.
2. **Real hosted recovery:** Before inviting any real user, create a restorable and encrypted dump of actual hosted staging Postgres (including `auth` and `public`), verify it on a separate isolated PostgreSQL 17 instance, and document restored owner counts, schema and RLS. Supabase Storage **object bytes** require separate proof; database dumps contain Storage metadata, not blobs. Free plan does not provide hosted managed backups. If host DNS fails from runner, fix IPv6/session-pooler connectivity; never bypass TLS verification or leak credentials into CI artifacts.
3. **Authenticated E2E:** Run [Closed beta staging E2E](https://github.com/t4j44/mysecondbrain/actions/workflows/beta-e2e.yml) on the exact approved candidate using dedicated synthetic users A/B. Both must sign in, exercise capture→retrieve→act, prove A cannot GET/PATCH/DELETE B's objects and vice versa, and pass browser/mobile relevant journeys. Zero critical failures; record failed/skipped cases explicitly. Mocked CI or anonymous-only checks are insufficient.
4. **Actual invite-only Auth enforcement:** User-facing `/signup` is closed by default in this frontend when `ALLOW_PUBLIC_SIGNUP` is unset. This is **not a security boundary**. Before launch, use Supabase Auth's authorized dashboard/admin controls to disable *new public signups* for email/OAuth and verify an unauthenticated signup attempt cannot create a new account. Existing invited accounts must still sign in. Manually create invited accounts via the supported Supabase Auth admin flow.
5. **Privacy and safe scope:** Approve legal controller name, support/privacy email, processor list, international transfers, retention/backups, user rights, terms and applicable law. Replace the review warnings in `/privacy` and `/terms` with approved notices before outside users enroll. Keep sensitive/confidential data prohibited. Test export and deletion without promising immediate backup erasure. Independently inspect private Storage objects. Add approval evidence to issue #32.
6. **Cost/security/ops:** Verify error alerts, backups, restore runbook, budget and AI rate/size limits, incident owner, security advisor exceptions and owner-controlled response. Confirm no billing/checkouts/live payments, no outbound Telegram/Google or public portfolio publishing unless separately accepted. Require deployment SHA manifest and rollback plan.

## Rollout after P0 PASS

- **Day 0:** invite 2 trusted testers first, manually provision Auth users, send approved privacy/terms and test-data restrictions. Verify sign in, save, search, editing, export, deletion in an isolated fixture.
- **Next:** invite remaining 3–8 testers only after first two report no cross-user exposure or data-loss incidents. Limit total to 5–10 users; do not open self-signup or allow referral creation.
- **Daily first week:** confirm backend readiness, Auth/storage 4xx/5xx, provider failure rates, unresolved incidents, support response and compute/AI usage. Keep a dated release log; rollback or stop onboarding on SEV-1 or unrecoverable data errors.
- **Go/no-go metrics (small-sample pilot assumptions, not measured promises):** zero cross-user leaks; zero data-loss incidents; all critical authenticated journeys pass; at least 70% of recorded pilot answers rated useful, wrong answer reports below 10%, with source checks; repeated usage observed, not fabricated.
- **Expansion:** 25 then 100 users only after new acceptance and actual per-user cost estimates. Paid billing is a separate release and remains OFF.

## Explicit non-claims

A frontend flag, CI test, documented backup script, storage metadata query, or preview deployment **does not** certify actual Auth signup restriction, hosted recovery, legal sign-off, or production readiness. Never publish secrets in this file or its PR.
