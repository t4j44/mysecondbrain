# V2 implementation truth — 2026-10-27

Status: **IN PROGRESS / PILOT NO-GO**. Code, local tests, CI, hosted tests and owner sign-off are separate gates.

## Source and scope

- Repository: `t4j44/mysecondbrain` (public), live refs fetched this session.
- Starting checkout: `codex/mobile-first-performance`, `e4557128250b57aa5c659b1bfaefee4647687e69`. Its tracked files and untracked recovery artifacts are preserved.
- V2 base: `codex/pilot-release-candidate-20261023`, `50890449cef9a68a73808383d12d257d0e1cb5aa`. The mobile checkout is an ancestor. `main` is `5402a5e65fcb97295c19f090fdca1310b4497392`, not the latest product baseline.
- Isolated workstream: `codex/v2-integrity-20261027`. No reset, force push, external PR merge, production promotion, hosted migration, payment or customer-data processing.
- All 20 sections of the supplied combined Production Astra Kit and nine companion files were read. Current expanded contracts take precedence over historical navigation. Documents are implementation specifications, not evidence of deployed features or authorization for production actions.

## Confirmed blocking CI cause

[Security & Quality run 40139964710](https://github.com/t4j44/mysecondbrain/actions/runs/40139964710), job `121009434894`, failed at the locked audit: `pypdf 6.21.1`, CVE-2026-115572 / CVE-2026-115585 / CVE-2026-115580, fixed in `6.21.2`.

The package minimum and both generated lockfiles now select 6.21.2. No advisory ignored, scanner disabled or assertion relaxed. [Upstream changelog](https://pypdf.readthedocs.io/en/stable/meta/CHANGELOG.html) confirms the patched release. `requirements.txt` also had a stale Pillow 12 cap; it now agrees with the already-existing pyproject/lock Pillow 13 range. The isolated hash-locked pip-audit returned **No known vulnerabilities found** on this dependency set. This is not a blanket security certification.

## Hosted observation, not V2 acceptance

The first repaired run, [40485062887](https://github.com/t4j44/mysecondbrain/actions/runs/40485062887), passed Python audit, backend tests, types and all 82 frontend tests, then exposed a second audit blocker: Zod 3.25.76, [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5). Zod is now pinned to 4.6.6 with compatible form resolvers 6.0.1. Login input/output types preserve the remember-me default; five real resolver regression tests cover field errors, password confirmation and profile bounds. The production pnpm audit and focused six-test form/login run passed locally. No advisory is suppressed.

The initial UI snapshot `3e0875206656087547da401732121f2c454b4aad` passed 308 local browser cases with 16 explicit viewport-specific skips, three meeting scenarios and a production build. Those local results do not include the later dependency or navigation changes. Its PostgreSQL CI passed in runs 40485063076 and 40485160130. The new dependency commit needs fresh CI.

| Surface | Observed | Boundary |
|---|---|---|
| Render API staging | `srv-dbbjrp4s728c738mhsj0`, live deploy `dep-dbd5nsafngtc73fnc71g`, commit `ac7d4bf3b2aa899a0d5dbd458c9445f03ca98dbb`, auto deploy OFF | Older build; V2 not deployed |
| Supabase staging | `rpkjmdrralzxhdsgceal`, ACTIVE_HEALTHY, ledger contains 37 entries through migration 36 (includes historical 21b) | Ledger names map to repo migrations; this is not two-account or storage acceptance |
| Vercel staging | `second-brain-web-staging`, `prj_r27R5j3Oss8GpNlHLZO58h0MA2uJ` | Owner approved team access; subsequent deployment inspection still returned 403. PR15 staging status says Canceled by Ignored Build Step, not a successful staging deployment. |
| Production | Not modified or tested with customer records | No promotion authorization |

Supabase security advisor returned six informational deny-by-default tables, one warning for `account_active` SECURITY DEFINER execution, and disabled leaked-password protection. The former needs the migration-36 self-owner guard checked against live DDL; never remove required policies or grant access merely to clear an advisor. Password protection remains an operator configuration decision. No hosted security finding is claimed remediated here.

## Next gates

Local backend regression: **477 passed, 0 skipped**, Python 3.11.16, synthetic test configuration, JUnit `.test-tmp/v2/backend.xml`. Ruff passed; mypy passed for 171 source files; Bandit exited 0 (existing annotation warnings). CI uses Python 3.12 and remains a separate gate. Supplied specification files were subsequently located under `Downloads/2nd brain/`; they are not copied into the public repository.

Integrity PR15 is green at `4f8c5a7f4259b8ab464c8b3702c28978c6f6d77e` (Security 40486715614, Postgres 40486721682). Navigation PR16 is green at `ea6a7794219de746b693a94d66471e22bc65a777` (Security 40494495931, Postgres 40525464787). The earlier pending-CI observations above are historical. See RELEASE_MANIFEST for exact receipts and the complete 91-case acceptance ledger.

Progressive meeting details and evidence navigation are implemented on the next review branch. Continue canonical action correctness, default-off Telegram, briefs and research. See FEATURE_MATRIX and PILOT_GATES. Later features cannot inherit an earlier build's PASS.
