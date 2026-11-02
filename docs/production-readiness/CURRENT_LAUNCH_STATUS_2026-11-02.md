# Second Brain — current launch acceptance (2026-11-02)

**Status: NO-GO for public/paid production.** This document supersedes historical August 2026 “READY FOR PRODUCTION” statements. Treat code, CI, staging, and public production as different evidence tiers. [Live release tracker #32](https://github.com/t4j44/mysecondbrain/issues/32) remains authoritative.

## What is verifiably ready

- Staging Supabase project `rpkjmdrralzxhdsgceal`: migrations 37–40 applied; 7/7 V2 tables and their RLS policies present; 3 Auth users and 1 commitment retained (read-only check 2026-11-02).
- Render staging V2 backend deployment `7a986638850e5ff5e22742ec4be4d2be5e0f3273` live; [hosted SHA/DB readiness passed](https://github.com/t4j44/mysecondbrain/actions/runs/41312587053).
- CI PostgreSQL 16/17 + Security & Quality passed on `b73ed724cc3a4756d9edca13c7ee44aa6e3077cc`. After merging PR #37, the [live anonymous RLS gate passed](https://github.com/t4j44/mysecondbrain/actions/runs/41409181900). This is **anonymous** read-denial evidence only, not two-account signed-in isolation.
- Vercel frontend has READY **preview** builds. Preview is not production promotion or authenticated user acceptance.

## Exact blocking acceptance tasks

| Gate | Evidence needed before marking PASS | Current truth |
|---|---|---|
| Hosted Supabase database/Storage/Auth backup and restore | Actual encrypted staging `pg_dump` including Auth + public data; independent PostgreSQL 17 restore with verified record counts and permission checks; private Storage object backup/restore if any, separate from DB dump; recovery owner and retention | Not verified. Supabase Free plan doesn't provide automated hosted backup and the connected SQL tool cannot run `pg_dump`/restore. CI disposable restore is insufficient. |
| Two separate authenticated test users | Create two synthetic staging-only accounts via supported Supabase Auth administration/signup; place `E2E_EMAIL`, `E2E_PASSWORD`, `E2E_EMAIL_B`, `E2E_PASSWORD_B` in GitHub **beta-staging environment secrets**, never in code/docs/chat; run [closed-beta E2E](https://github.com/t4j44/mysecondbrain/actions/workflows/beta-e2e.yml), retain evidence of A unable to read/update/delete B's records and private objects; test logout/reload | Not run. [Preflight](https://github.com/t4j44/mysecondbrain/actions/runs/41313962272) listed four missing secrets. GitHub app does not expose secrets administration and Supabase app does not expose Auth admin create-user. |
| Privacy/terms | Owner-reviewed public privacy notice and terms, accurately identifying controller/contact, processors, international transfers, retention and backup limits, actual export/erase behavior, AI provider data handling, lawful basis, user consent and incident contacts; accessible before signup | **Not signed off.** [Internal inventory](../privacy/data_inventory.md) explicitly says exports omit attachment bytes and AI redaction can miss details; user-facing legal review required. Do not claim encryption/erasure/retention not demonstrated. |
| Payments (if charging) | Merchant/provider approved, customer pricing/terms shown, test-mode checkout and webhook signature, duplicate/replay protection, entitlement delivery, failed/refunded/cancelled handling, tax/invoice and support; no live charge until owner accepts | **Not established.** No payment-provider receipt or live billing acceptance supplied. Free pilot may explicitly defer payments, but must not be advertised as paid production. |
| Reliability/operations | Alerts for staging/prod health, failed jobs and 5xx; restore drill; cost/quotas for AI, storage, OCR, email; incident owner; support channel; measured browser/mobile performance; real Gemini, MCP, meeting and erasure tests; acceptable failure rates; domain and production env verified | Incomplete; CI/mocks and unauthenticated smoke tests do not cover hosted user journeys. |
| Security warnings | Investigate `account_active(owner uuid)` SECURITY DEFINER behavior in context of RLS; leaked-password protection disabled on Free plan, which Supabase documents as a Pro+ feature; choose supported mitigation and account plan | Not cleared. Do not blindly revoke `account_active` because policies rely on it. |
| Production web promotion | Explicit launch decision after above gates PASS, verified production Supabase separation, immutable release SHA, rollback target, operational owner, 5→10→25→100 gradual onboarding | Not done: Vercel project latest deploy is preview (target null), not live production promotion. |

## Service access boundary

Connected GitHub can edit repo and trigger some existing workflow reruns but **cannot write environment secrets**. Connected Supabase can apply migrations and read SQL but **cannot export a full database, restore it or create supported Auth users**. The Vercel connector can promote, but no promotion should occur while backup and hosted Auth acceptance are missing. Switch the task to an authorized browser/computer-use workflow or run the existing scripts on a machine with secure local staging database credentials. Never paste secrets or copies of user data into ChatGPT.

**Launch decision:** Free, small invite-only pilot can be reconsidered only after recovery and two-account isolation pass, with sensitive data and unsupported integrations forbidden. Paid/public production requires the fuller gates above. Do not mark user acceptance or payment evidence PASS from documentation alone.
