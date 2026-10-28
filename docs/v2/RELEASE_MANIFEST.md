# V2 release evidence manifest

As of 2026-10-28: **IN PROGRESS; pilot NO-GO**. This is a stack of draft review branches, not a promoted release.

| Slice | Exact revision | Review | Automated receipts |
|---|---|---|---|
| Integrity / dependency repair | `4f8c5a7f4259b8ab464c8b3702c28978c6f6d77e` | [PR15](https://github.com/t4j44/mysecondbrain/pull/15) | [Security](https://github.com/t4j44/mysecondbrain/actions/runs/40486715614), [Postgres](https://github.com/t4j44/mysecondbrain/actions/runs/40486721682) |
| Navigation / universal capture | `ea6a7794219de746b693a94d66471e22bc65a777` | [PR16](https://github.com/t4j44/mysecondbrain/pull/16), based on PR15 | [Security](https://github.com/t4j44/mysecondbrain/actions/runs/40494495931), [Postgres](https://github.com/t4j44/mysecondbrain/actions/runs/40525464787) |
| Progressive meeting review | `537190bf3f877aeea6e358cd38dfa5e21c46e29b` | [PR17](https://github.com/t4j44/mysecondbrain/pull/17), based on PR16 | [Security](https://github.com/t4j44/mysecondbrain/actions/runs/40528180263), [Postgres](https://github.com/t4j44/mysecondbrain/actions/runs/40528239620) |
| Review snapshot / conflicting retry protection | `7db230674bad55548df1f97208bd4c568174d8c3` | [PR18](https://github.com/t4j44/mysecondbrain/pull/18), based on PR17 | [Security](https://github.com/t4j44/mysecondbrain/actions/runs/40530199944), [Postgres](https://github.com/t4j44/mysecondbrain/actions/runs/40530256484) |
| Telegram linking / consent / revocation | `b10fff469b8b1d85a6f2e89bf5baf4779132a88c` | [PR19](https://github.com/t4j44/mysecondbrain/pull/19), based on PR18 | [Security](https://github.com/t4j44/mysecondbrain/actions/runs/40661846095), [Postgres](https://github.com/t4j44/mysecondbrain/actions/runs/40661854859) |

Phase-1 security job 122156389391: 477 backend tests, 88 frontend tests, 350 browser passes, 46 intentional viewport skips, three Chromium meeting scenarios; lint, Python/TypeScript types, audits and build passed. PostgreSQL job 122263716204: 67 cases each against fresh, upgraded and restored PostgreSQL; seeded legacy history preserved; isolated dump/restore and runtime container schema/FFmpeg checks passed. This restore does not prove hosted Supabase Auth or private Storage recovery.

PR18 security job 122280595491: 483 backend tests, 92 frontend tests, 350 browser passes / 46 intentional skips; audits, lint, types and build passed. PostgreSQL job 122280786140: 68 cases each on fresh, upgraded and restored databases, including identical/competing confirmation races; isolated restore and runtime checks passed.

PR19 security job 122726537220: 497 backend tests, 97 frontend tests, 368 browser passes / 46 intentional skips, and three meeting scenarios; audits, lint, types and build passed. PostgreSQL job 122726567976: 71 cases each on fresh, upgraded and restored databases; legacy history, isolated restore and runtime checks passed. This proves the linking foundation in isolated CI, not live Telegram delivery.

The [91-case matrix](test-results/ea6a7794219de746b693a94d66471e22bc65a777/matrix.csv) is scoped to the navigation revision. Only G10 is PASS; narrower synthetic tests are supporting evidence, not full acceptance of a hosted or human scenario. Optional features stay unavailable while their cases are unverified. New code needs new exact-revision evidence before replacing this baseline.

Hosted API staging last observed on `ac7d4bf3b2aa899a0d5dbd458c9445f03ca98dbb`; no matching V2 API/worker/web release has been verified. Vercel team access was approved by the owner; connector inspection still returned 403. No production promotion, hosted migration, paid activation or sensitive-data processing was performed.

For promotion: rerun CI on the assembled candidate, align approved staging web/API/worker SHAs, run the outstanding real-provider, two-account, Storage, MCP, backup and physical-device cases, record actual usability/cost results, then obtain explicit owner GO. Never infer a provider PASS from a mocked fixture.
