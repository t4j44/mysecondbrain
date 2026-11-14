# Execution Backlog, PR Boundaries and Durable Agent Handoff
## 0. Rule
One accountable coding-agent session coordinates execution, but **small PRs with tests** are the units of progress. This file is the durable truth when the chat context runs long. Never change or claim a gate without actual evidence.

## 1. Ordered PR map (do not blindly merge existing PRs)
| Batch | Scope | Dependencies | Evidence / exit criteria |
|---|---|---|---|
| PR-A | Current code/live state and signed-in UI reconciliation | None | Exact branch SHAs/URLs, existing feature matrix, route screenshots |
| PR-B | Safeguard existing credentials, review recovery PR #46, real Drive backup+isolated restore | Auth/staging access | Remote read-back hash, restore comparison, managed-service gap report |
| PR-C | Protected browser E2E and tenant isolation, review PR #45 | Staging + synthetic accounts | GitHub run ID, real A/B denied cross-access, no skipped critical tests |
| PR-D | Shared IA/navigation/design-system tokens, Home/People/Capture shell | Baseline UI | Before/after **authenticated** screenshots, mobile + a11y |
| PR-E | Meeting page: download, transcript corrections, verified extraction review, People/Work links | Existing meeting APIs; privacy | Owner recording download, negative auth, citations and approval tests |
| PR-F | Cross-meeting Ask + pre-meeting brief + three skills templates | Source-index integrity | 20–30 synthetic gold queries, abstention and correct person history |
| PR-G | Timezone-safe booking MVP and ICS fallback under Meetings | Calendar decisions, privacy | Conflict/DST/idempotency/guest link tests; no public PII leak |
| PR-H | Optional calendar OAuth integration and bounded reminders | Scoped provider permissions | Consent/revoke, provider failure + retry; gate feature on acceptance |
| PR-I | Privacy/account UX, AI caps, alerts, plan/host eligibility | Security/recovery | Deletion/export and spending/reliability proof |
| PR-J | Pilot instrumentation, invite flow and final E2E+release audit | All core | Issue #32 evidence-backed separate GO decisions |

Do not force separate PRs if the repository convention combines small related changes, but avoid one giant PR containing backend, UX, auth, migrations and billing changes simultaneously.

## 2. Existing PR handling
- **#45** Draft: E2E preview target fix; review for stale URLs, Vercel preview protection secret injection and reproducible `workflow_dispatch` run. Merge only after checks and existing owner approvals.
- **#46** Draft: encrypted recovery; synthetic tests passed, real staging recovery not proven. Review complete diff, secrets handling, Restore safety and validated Drive read-back. Do not equate a form save with completion.
- **#39, #42, #44** and other drafts: inspect for overlap/conflicts before rebasing; #44 included docs-only synthetic UI recovery evidence, not necessarily implementation. Do not overwrite live uncommitted changes or assume all old PRs should merge.

## 3. Per-task work template
```
ID: M-01
Status: NOT_STARTED | IN_PROGRESS | BLOCKED | VERIFIED_HOSTED | FLAG_DISABLED
Problem/user outcome:
Code baseline + paths:
Implementation delta:
RLS/privacy impact:
AI/provider cost:
Tests (unit/integration/E2E/device):
Failure cases:
PR/commit SHA:
Staging URL + deployed SHA:
Evidence:
Owner approval needed (ONE action only):
Rollback strategy:
```

## 4. Actual blockers (at last checked snapshot, 2026-11-12)
- Real encrypted staging backup, offsite Drive read-back and independently restored data: **unverified**.
- Authenticated A/B privacy and full hosted E2E: **unverified**.
- Old separate-project exposed database password still flagged for rotation before external beta; operational impact check required.
- Signed-in preview UI confusion and obsolete staging alias require exact deployment check.
- Hosting eligibility for commercial external pilot, AI free-tier privacy, user support/retention: **unverified**.

## 5. Founder approval rules
Allowed without repeated approval: read-only repo analysis, unit/integration tests with synthetic data, small reviewed branch/PR changes, protected staging inspection, synthetic staging E2E if safe and scoped.
Ask explicit approval for: entering/retrieving private credentials, changing production/legacy infrastructure, deleting data/old files, creating paid cloud resources, enabling public routes, outgoing customer messages, recording real participants, calendar writes, merging risky schema/auth changes or publishing a real user pilot.
Do not describe an agent as having access to all user accounts unless the specific connection permission is proven.

## 6. Durable session checkpoint
### Active implementation checkpoint — 2026-11-13

- Isolated candidate: `E:/second brain/.worktrees/v1-pilot`, now `codex/v1-meeting-workflows-20261113`, based on #51 `c3bcb2d`. Original checkout preserved.
- Draft PR chain: #48 shell/search, #49 original audio, #50 protected E2E, #51 synthetic callback chronology; separate #47 recovery guards over #46. None merged or deployed. Templates are the next slice.
- Evidence: 129 earlier frontend tests; final affected search/recording 25 PASS, final recording component 8 PASS, 35 synthetic browser checks; 110 affected API tests and final 15 recording tests. Protected harness 17 PASS; 28 hosted cases discovered, not executed. TypeScript/lint PASS. Final template/correction API 18 PASS, template component 14 PASS after review fixes.
- #51 PostgreSQL 16/17 CI PASS, including disposable restore, upgrade and API container checks: run `43445904521`. This does not replace actual staging backup/recovery. Local frontend production build remains blocked by cross-drive dependency junctions; preserve-symlink retry also failed on dependency resolution.
- Recovery follow-up is isolated on `codex/v1-recovery-guards-20261113` over #46. Five confirmed issues addressed, 20 synthetic recovery tests passed including real Windows ACL and cancellation checks. Actual backup/Drive/restore still unverified.
- Protected preview still needs observed application sign-in; user sign-in handoff remains pending. No secrets read, hosted mutations or public deployments.
- Next: finish template PR/evidence, then manual scheduling and protected A/B acceptance. Follow `WORK_LOG.md` for exact commands, current results and remaining gates.

At end of each work batch update `docs/second-brain-v1/WORK_LOG.md` (create during execution) with:
- current HEAD/branch and dirty working-tree state;
- PRs created/reviewed/merged;
- exact test commands, pass/fail/skipped and run URLs;
- actual staging deployment URLs/SHAs and any CORS/auth outcomes;
- checklist G0..G4 evidence & unresolved risk;
- next single independent action;
- owner authorization needed, if any (no credentials).

## 7. Release evidence declaration
```
**Date/commit:**
**Build:**
**Unit/integration:**
**Hosted E2E:**
**A/B isolation:**
**Recovery:**
**Signed-in UX:**
**Provider data terms:**
**Budget/protection:**
**Critical findings:**
**Dogfood decision:** GO | NO-GO
**5–10 real beta decision:** GO | NO-GO
**Reason/links:**
```
Even after launch, do not label V1 *fully production ready* for public paid use until G4 specifically passes.
