# Release evidence — 2026-10-20

**PRODUCTION READY: NO. Hosted staging acceptance is BLOCKED by owner direction.**
No production database, credentials or storage may be used for release testing.

## Identity and review

Starting branch `feature/relationship-loop`,
`a97e8f64b55c0441a9d46d3570ecd98ea0ca1052`; release branch
`codex/second-brain-release-hardening`. Meeting `49d9f34` and Prompt `8862f70` are
ancestors; this preserves the newer relationship/Google/email work. See
FINAL_FEATURE_AUDIT for the initial matrix, preserved files and base CI links.
Verified candidate identity and linked CI receipts are below. The completion report
also supplies the final branch HEAD and its exact Actions runs; historic/base
results alone do not pass a newer candidate. This release additionally ensures a
confirmed self-speaker appears in minutes, preserves separately spoken legacy
deadline evidence without reattribution, and corrects the runbook's test-user
creation order; the final commit's own checks must pass before acceptance.

Independent read-only review found incorrect cross-reference speaker attribution,
stale minutes after extraction, and legacy conditional/deadline compatibility gaps.
All received focused fixes/regressions. Final independent review additionally
reproduced blank normalized quotation/condition bypasses; schema and grounding
now reject those, with three regression cases. Scoped independent re-review passed.
Review is supplementary to execution,
not independent hosted certification. No further defect was confirmed in reviewed
locking, graph ownership, optional gates or async-cookie changes.

## Local execution receipts

Clean Python 3.12.14 environment installed from the hash-locked requirements;
pnpm 10.17.1, Next 15.5.27, React 18 (compatible declared peer), Vitest 4.1.11,
Vite 6.4.3. Retained google-genai 0.8 and MarkItDown 0.1.5 compatibility bounds.

| Check | Observed result | Limit |
|---|---|---|
| Meeting release regressions after final legacy deadline fix | 25 passed, 12 deprecation warnings, 10.80s | Mocked AI, SQLite owner checks; not RLS/provider proof |
| Complete local backend at 4d78cc2 | 459 passed, 0 failures/errors/skips, JUnit 311.986s | Before the final three blank-evidence regressions; final code CI receipt below |
| Complete frontend Vitest | 60 passed, 14 files, 39.69s | Component/unit, not hosted auth |
| Frontend lint/typecheck | PASS, no ESLint warnings/errors | Next lint deprecation is tooling notice |
| Production Next build | PASS, 41/41 static pages generated | Explicit mock public configuration; no hosted auth/data proof |
| Real Chromium component fixture | 3/3 widths: 320/390/1440 | Synthetic API/recorder/provider; all viewport scenarios printed PASS |
| Ruff | All checks passed | Static lint |
| Mypy | No issues, 171 source files | Existing untyped rate-limiter note |
| Bandit | 0 findings | Static scanner; no new suppressions |
| Python dependency audit | 0 known vulnerabilities | pip-audit 2.10.1, current locked environment |
| Browser production dependency audit | 0 all severities | `pnpm audit --prod`, not development tooling |
| All JS dependency audit | 1 HIGH, 0 critical/moderate/low | Unfixed build-only `braces`; see below |

Earlier full locked backend execution: **453 passed, 1 failed**, 26 warnings,
733.71s. Failure: isolated MarkItDown subprocess hit its unchanged 40-second limit
while concurrent builds/scans were active. Isolated document diagnostic then
**2 passed, 11 warnings, 9.23s**. No timeout/security limit was relaxed. This failed
full run is retained, not recast as passing. The serial full rerun passed 459/459
without relaxing a limit. A separate build invocation without required mock public
variables failed closed as designed; the correctly configured final build passed.
Final full-suite/CI receipts follow.
The explicit legacy deadline regression initially failed when a second participant
stated the due date; resolving that participant's own canonical reference repaired
it without relaxing primary promise/speaker matching. Both same-speaker and
different-speaker variants are now covered by the focused suite.
Previous 438-test baseline and 93-test intermediate focus runs are not final proof.
Hosted Playwright collection is configuration validation only, not execution.

### Remaining build supply-chain finding

Full audit still reports [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm),
`braces` 3.0.3 stack exhaustion from deeply nested untrusted glob patterns, HIGH,
no patched upstream release. Paths are ESLint/Tailwind development dependencies;
the production audit has zero affected runtime dependencies. App users do not
submit glob patterns to these tools. Keep build configs trusted, never run builds
on attacker-supplied patterns, and track an upstream fix. It is NOT suppressed or
declared resolved. Security acceptance must explicitly assess this residual build
risk before release; this evidence does not certify the entire application secure.
Other discovered test-runner/CSS/YAML/brace-expansion and runtime vulnerabilities
were repaired and retested; no unrelated framework rewrite was introduced.

## Data and output proof

No migration added or old SQL edited. Existing 35-file manifest includes migration
32 meeting, 33 Google multi-account, 34 email contacts and historical 21b. Notes/
history/review remain owner-scoped Meeting JSON; extraction/checkpoints remain
MeetingCapture JSON. API tests deny another owner and anonymous notes/review/export,
reject foreign entity links, exercise confirmed graph idempotency/deletion and MCP
bounded exact segments. PostgreSQL tests race real row locks for notes and confirm;
their executed CI counts belong below, not to local SQLite results.

Synthetic five-output example and exact fixture expectations:
[RELEASE_FIXTURES](../meetings/RELEASE_FIXTURES.md). UI covers separate outputs,
evidence jumps, transcript search, speaker confirmation and note reload persistence.
Generated local screenshots: `.test-tmp/meeting-ui/detail-390.png` (synthetic).
Graph extends canonical typed temporal EntityEdges, with owner checks on both ends;
no inferred co-attendance friendship. User notes never authorize canonical writes.

## Hosted and operational acceptance

| Required evidence | Status / reason |
|---|---|
| Dedicated Supabase project; actual migration ledger | BLOCKED: owner has not created/verified staging |
| Staging API/web/worker exact-SHA alignment | BLOCKED: no staging deployment performed |
| Real two-user RLS, Auth, signed upload/read, direct private Storage denial | BLOCKED; CI pgvector is a different boundary |
| Real Gemini final/live transcription, bilingual accuracy, long audio | BLOCKED; no staging provider call performed |
| Real external ChatGPT/Claude MCP OAuth/read/finalize/revoke | BLOCKED; simulated transport is insufficient |
| Authenticated hosted non-meeting and meeting E2E | BLOCKED; workflow prepared, not dispatched without staging |
| Physical Android/iOS HTTPS/microphone/reconnect/slow data | BLOCKED; browser fixture does not count |
| Worker restart/provider checkpoint billing, hosted deletion erasure | BLOCKED; local mock retry cannot establish live billing/erasure |
| Hosted encrypted backup, separate-target restore incl. Auth/Storage | BLOCKED; disposable SQL restore alone insufficient |
| Google Drive/Calendar and portfolio | DISABLED in hosted release pending acceptance; revocation retained |
| Always-running Render and confidential audio plan | BLOCKED: owner budget/privacy decisions; no billing changes |
| Actual p95 latency/cost/error rate/beta return | UNMEASURED; collect baseline after staging |

No PR to stale main until clean tests and staging, per master spec. No merge,
production deploy, production migration or production change performed. Operator
screen-by-screen steps, configuration names and release sequence are in
[RELEASE_RUNBOOK](RELEASE_RUNBOOK.md).

## Candidate CI receipts

Both workflows completed successfully at reviewed code revision
`45cfaefdc8295e5beae3a199a679f74b7e808e0a`:

- [Security & Quality 39386805213](https://github.com/t4j44/mysecondbrain/actions/runs/39386805213),
  job `118508482854`: **462 backend tests passed**, 24 deprecation warnings,
  114.93s; Ruff, Bandit (no issues), mypy (171 files), locked Python audit and
  production browser audit passed. **60 frontend tests / 14 files** passed;
  lint/typecheck/build passed, **41/41** static pages generated. **3/3** real
  Chromium synthetic-adapter widths passed. Hosted test discovery: **28 tests / 7
  files**, NOT executed staging acceptance.
- [PostgreSQL 39386805259](https://github.com/t4j44/mysecondbrain/actions/runs/39386805259),
  job `118508483128`: **64 fresh tests** passed (8.68s), **64 seeded-upgrade tests**
  passed (8.35s), **64 restored-database tests** passed (8.42s); each had 19
  deprecation warnings and no skipped tests. Bootstrap/schema contract, retained
  temporal history, actual pg_dump/separate-target restore, exact restored fixture
  and owner/foreign-role RLS checks passed. Actual Docker build/run passed;
  **FFmpeg/FFprobe 7.1.5**, liveness/readiness/exact SHA and owner-scoped durable
  worker completion printed PASS. Artifact `postgres-test-evidence` contains the
  fresh/upgrade/restore JUnit reports. This is disposable pgvector PostgreSQL,
  not hosted Supabase Auth/Storage or physical object recovery.

The first candidate `4d78cc2` also passed both workflows (39386164747 / 39386164756),
but is superseded. The final evidence/minutes commit is checked again on push;
use [the release branch's Actions checks](https://github.com/t4j44/mysecondbrain/actions?query=branch%3Acodex%2Fsecond-brain-release-hardening)
and compare each run's full `head_sha` with `git rev-parse HEAD`. The completion
report links those exact final runs. Do not substitute an earlier green SHA.

| Gate | Status |
|---|---|
| CODE COMPLETE | PARTIAL: implementation and review repairs complete; HIGH build dependency risk remains open |
| CI VERIFIED | PASS at 45cfaef above; final evidence/minutes commit requires its own green checks |
| STAGING VERIFIED | BLOCKED: separate project required |
| 7-DAY DOGFOOD COMPLETE | BLOCKED: staging and owner authorization first |
| PRIVATE BETA ACCEPTED | BLOCKED: dogfood and 10–15 consented users first |
| PRODUCTION DEPLOYED & VERIFIED | BLOCKED: preceding gates and explicit owner authorization |
