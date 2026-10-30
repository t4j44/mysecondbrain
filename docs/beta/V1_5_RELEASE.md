# Personal Context Foundation V1.5 release candidate

Date: September 28, 2026. This is the final pre-pilot feature expansion. Further large features wait for dogfood and tester evidence.

## Identity and release state

- Starting SHA: `9cf7ea0e4791bcc06dfa75d52e150aa63062d181`.
- Branch: `codex/personal-context-v1-5`.
- Verified application SHA: `f760f4583f8002dd8564fc0110f77506c2e88564`.
- [Security & Quality CI](https://github.com/t4j44/mysecondbrain/actions/runs/36394223243): PASS. [PostgreSQL upgrade and recovery CI](https://github.com/t4j44/mysecondbrain/actions/runs/36394223233): PASS, both on that exact SHA.
- The release-report commit following that SHA changes documentation only; `git rev-parse HEAD` identifies the final checkout revision. Deploy a revision with passing CI and compare both hosted service SHAs.
- No merge, hosted migration, production deployment or promotion performed.

| Required state | Result | Evidence needed |
| --- | --- | --- |
| CODE COMPLETE | YES, within the documented V1.5 cut line | Exact-revision quality CI, PostgreSQL upgrade/restore and local component checks pass. Hosted acceptance is a separate gate. |
| STAGING VERIFIED | NO | Both hosted service SHAs, two-account authenticated E2E and provider checks remain unverified. |
| DOGFOOD READY | NO | Hosted V1 then V1.5 acceptance must pass first. |
| PRIVATE BETA READY | NO | Staging acceptance and seven-day dogfood evidence required before 10–15 testers. |
| PRODUCTION VERIFIED | NO | No production promotion or verification performed. |

Safe to deploy into isolated staging: **YES**, after confirming the isolated target, reviewing its migration ledger and taking a backup. Safe to promote production: **NO**. Ready for 10 private testers: **NO**.

## Schema, backend and frontend changes

Exact migrations added:

1. `20260927000029_context_events.sql`: private source events and media metadata; occurred/recorded/updated timestamps, timezone, original source and provenance; temporal graph edges, current-edge uniqueness, composite owner references and RLS.
2. `20260927000030_outreach_receipts.sql`: separate `opened` and `sent` receipt actions.
3. `20260927000031_mcp_oauth.sql`: five durable OAuth vault/connection tables. Owners can read their grant metadata; clients, pending requests, code/token hashes are server-only.

The seven new tables extend the existing Supabase store. No new graph/vector service is introduced. New source events participate in the existing owner-scoped keyword and pgvector retrieval, index jobs and live-record revalidation. Restricted/deleted events are excluded. AI sessions preserve their recorded source and occurrence time; aliases/retries resolve to one finalization. Ambiguous identities fail closed instead of silently merging people.

Capture adds reviewed card/contact fields, event time/timezone and up to two private photos. Photos are resized/re-encoded without embedded metadata and originals are discarded. Home prioritizes the existing action queue; intent search explains saved evidence for relevant people. Person profiles show chronological moments, dates, private photos and source links. Source pages expose the original event and explicit erasure. Drafts remain editable; WhatsApp/email opens require a reviewed draft. A separate explicit, idempotent confirmation writes the self-reported outcome and updates relationship history. Opening an app is never counted as sending.

Basic temporal Ask covers bounded explicit date windows and exact saved entities with cited source dates. Arbitrary temporal language, inferred unrecorded work, full skill dashboards and autonomous agents remain deferred. See [implementation map](V1_5_PERSONAL_CONTEXT_SPEC.md).

## MCP and privacy

The official SDK serves Streamable HTTP at `/mcp` inside FastAPI. OAuth adds discovery, dynamic client registration, PKCE S256, exact callback/resource binding, explicit browser consent, granular permissions, short-lived access, refresh rotation/reuse detection and revocation checked per request. Token/code values are hashed at rest. Legacy scoped keys remain supported. Public information moved to `/mcp/info`. Client ID Metadata Documents are not implemented; actual ChatGPT/Claude/Gemini client compatibility remains unverified. [Setup and limits](../mcp/client_setup.md).

Canonical data stays in Supabase. Gemini configuration remains `gemini-2.5-flash`, `gemini-embedding-001`, `AI_DATA_MODE=free_redacted`. Stable placeholders, redaction and beta sensitivity warnings remain active. Device OCR is English and requires user review; minimization is heuristic, not guaranteed anonymization. An external AI granted MCP access receives the approved records under that client's own terms, separate from internal Gemini redaction.

Event erasure clears its original content, removes active derived retrieval and queues private blob erasure. A content-free replay tombstone prevents recreation by retry. Existing referenced people/projects remain. Derived domain rows follow existing soft deletion and remain in the database until account erasure; they are excluded from active retrieval/export. Expired draft photos are cleaned by the worker. Account exports include active event text/media metadata and exclude OAuth vault material and binary bytes. Storage completion is asynchronous; backups are a separate retention boundary. [Data inventory](../privacy/data_inventory.md).

## Measurement

Fourteen private event counters cover capture, card/moment, intent, evidence opens, draft/open/confirmed outcome and MCP connection/session/revocation. Event metadata contains counts/types/record IDs, not raw queries, names or message bodies. Weekly activity and [operator SQL](RELATIONSHIP_METRICS.sql) distinguish opened links from self-reported outcomes. These are product observations, not traction, independently verified delivery, revenue or testimonial permission.

## Verification evidence

| Gate | Latest observed result |
| --- | --- |
| Backend full suite | 260 passed in CI on the verified application SHA; 25 warnings, no failed or skipped tests. |
| V1.5 backend focused suite | 28 passed across event/media/outreach, temporal/finalizer and OAuth tests. |
| Frontend unit suite | 22 passed across 8 files in exact-revision CI. |
| Ruff / mypy / Bandit | PASS; mypy checked 154 source files. |
| Frontend lint / TypeScript | PASS in exact-revision CI. |
| Production frontend build | PASS in exact-revision CI with build-only mock public configuration; no hosted connection proved. |
| Synthetic component browser QA | 12 checks passed: Home, Capture, Person Context and OAuth consent at 320, 390 and 1440 px; no page errors or horizontal overflow. Real components with mocked API/session, not hosted E2E. |
| PostgreSQL / seeded V1 upgrade / dump-restore | PASS on the verified application SHA: 43 + 43 + 43 passed, zero skips/failures. [CI run](https://github.com/t4j44/mysecondbrain/actions/runs/36394223233). Three separate executions of the same integration suite, not 129 distinct cases. |
| Browser suite collection | PASS: 26 desktop/mobile/public cases collected without credentials. This is configuration validation, not browser test execution. |
| Hosted two-account desktop/mobile E2E | NOT RUN. Automated V1.5 acceptance cases added; staging accounts/access unavailable. Missing/skipped evidence must fail the gate. |

Local UI evidence is in the ignored `.test-tmp/v15-ui` folder. It uses clearly labelled synthetic data and never sends a message. The user-interface fixture does not prove hosted auth, Gemini quality, Supabase Storage or physical-device behavior.

The CI database gate bootstrapped all 31 migrations, upgraded seeded V1 data through 29–31 and executed the integration suite again after real dump/restore. Old V1 PostgreSQL evidence was not reused to certify these changes. No skipped test is a passed release gate.

## Hosted exclusions, blockers and next action

Not tested against hosted services: actual Vercel/Render revisions/readiness; two-user authenticated Capture/RAG/outcome flow; hosted Supabase RLS/Storage erasure; live Gemini free-tier quota/quality; external AI OAuth clients; Google Drive/Calendar token refresh/retries; public portfolio publication/revocation regression; hosted restore; physical phones. No real users, testimonials or usage claims have been invented.

Staging access and two synthetic accounts were promised but have not been verified. The available GitHub connector cannot inspect environment variables/secrets, so this report does not claim those hosted settings are absent. The highest-priority next step is **deploy the tested revision to isolated staging and execute [the runbook acceptance](RUNBOOK.md#v15-staging-acceptance)**. Then complete seven days of dogfood before inviting 10–15 testers. A paid Gemini decision is not a gate.

## Repository housekeeping

Only the regenerable `graphify-out/cache/` is ignored and removed from the Git index. No required graph/source output is deleted. Existing tracked graph configuration/manifest sidecars remain tracked; generated graph JSON, HTML, report and dated backups remain available locally without adding unrelated historical output to this release. The AST graph refresh completed; SQL extraction is unavailable because the local SQL parser is not installed. SQL correctness is covered by the PostgreSQL CI gate instead. No LLM graph refresh or paid call was used.
