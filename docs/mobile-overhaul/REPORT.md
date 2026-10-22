# Mobile UX and performance acceptance — 22 October 2026

This report separates implemented code, synthetic/local measurements, migrated PostgreSQL CI, hosted acceptance, and physical-device testing. A passing fixture is not proof of a working hosted account or AI provider.

## Scope and release boundary

- Repository: `t4j44/mysecondbrain`; baseline: `1c4d537` on `codex/second-brain-release-hardening`.
- Implementation branch: `codex/mobile-first-performance`. Production and the release branch were not merged or promoted. No hosted schema migration, billing change, new service, shared personal-data cache, or provider replacement was introduced.
- The user requested execution of the supplied mobile-overhaul document and a parallel performance audit. Instructions in the document were treated as task requirements within that request, not as independent permission to weaken security or publish private records.
- GRAVITAS decision: deep implementation across shared layout, API, and private-data boundaries. Existing architecture and canonical APIs were retained. No subagents were delegated. Existing unrelated untracked workspace files were preserved.

## Findings and changes

| Finding | Evidence | Change |
| --- | --- | --- |
| Home could fail while reading an empty account | Staging Render logs repeatedly returned 409 on `/api/v1/relationships/home`. The read writes audit events without `resource_type`; staging requires that column to be NOT NULL with no default. The generic handler mislabeled integrity failures as duplicate conflicts. | Explicit audit targets for Home/activation/suggestion events; model default matches the existing schema. NOT NULL/check violations return a safe 500 with request ID and logged SQLSTATE, without SQL/parameters. No migration needed. |
| Dashboard did repeated work for each project/contact | Release implementation calls ownership/person queries in project and participant loops. Registered ORM mappings also eagerly loaded unused participant/capture records. | Per-project window limits; batched people, participant and evidence lookup; explicit owner/deleted-source checks; scalar activation counts in one query; suppress unused eager loads. |
| Assistant was narrowed by nested page containers | Baseline screenshots show horizontal overflow and a narrow composer at phone widths. | One full-width conversation surface, one heading, compact disclosure, wrapped sources, message scrolling and manual-scroll preservation, visible Send/Stop, autosizing 16px composer, visual-viewport handling, safe-area navigation spacing. |
| Retry/double-send/late-cancel states were unreliable | Added tests exposed duplicate retry questions; same-render double submission and late stream responses are exercised directly. | Synchronous request lock, generation guard, abort handling, safe errors, final UTF-8/SSE flush, retry replaces the failed answer while retaining one question. |
| Small-screen headers/forms were crowded | Screenshot inspection caught hidden Save controls and 200% text clipping in WebKit. | Measured navigation height provides real bottom spacing; enlarged text can scroll the document; focus-managed dialogs/drawers; native relationship select on phones; shared labels, 44px controls, 16px inputs and wrapping. |
| Six saved-tool pages showed fake implementation buttons | Organizations, notes, ideas, achievements, metrics and content displayed “Agent X” toast stubs; notes falsely claimed every record had vector indexing. | Actual existing list APIs with pagination, honest errors and empty states; source links where supported; optional details elsewhere. Existing note form corrected from incompatible `content/category` to canonical `body/type`, with a real saved-source destination. |
| Login loaded unused code before interaction | Bundle manifest and source inspection found an unused global React Query provider and the auth SDK in the initial login graph. | Remove unused provider from root; defer Supabase browser SDK until password/OAuth submission; remove unused Inter font and eager monospace preload. Keep safe redirects and auth methods. Remove unsubstantiated “zero leaks/online predictive” claims. |

## Measured performance

Full-route JavaScript means the unique union of page and ancestor-layout chunks, gzipped per file. It includes layout code; counting just page chunks understates the load.

| Measurement | Baseline | After | Meaning |
| --- | ---: | ---: | --- |
| Home + activation SQL statements | 80 | 17 | 78.75% fewer on the same fictional 6-project/6-meeting graph with production participant mappings registered. |
| Warm median service time | 200.081ms | 57.585ms | Three warm SQLite harness samples after one compilation sample; 71.2% lower. Not network or hosted PostgreSQL latency. |
| Warm median SQL execution time | 107.266ms | 23.671ms | Same harness; 77.9% lower. |
| Response payload | 7,765 bytes | 7,765 bytes | Exact serialized response equality asserted across both versions and all runs. |
| Message render calls while typing | median 3,540 | 0 | Actual message render functions, 60 fictional history messages, 29 typed characters, three development Profiler runs. Not field INP. |
| Login initial JavaScript, gzip | 232,443 bytes | 160,089 bytes | 31.1% lower after deferring the auth SDK. |
| Assistant initial JavaScript, gzip | 232,201 bytes | 246,569 bytes | 6.2% larger: focus-managed menus/dialogs and reliability controls add code. This is a measured cost, not a claimed bundle improvement. |
| Home initial JavaScript, gzip | 231,525 bytes | 246,231 bytes | 6.4% larger for the shared accessible shell and recovery UI. |
| People initial JavaScript, gzip | 235,208 bytes | 248,153 bytes | 5.5% larger. |
| Capture initial JavaScript, gzip | 232,692 bytes | 248,210 bytes | 6.7% larger. OCR remains dynamically imported only after a photo action. |
| Work initial JavaScript, gzip | 224,591 bytes | 244,630 bytes | 8.9% larger; now loads actual work summaries rather than only static destination cards. |

Lighthouse baseline: production Next.js `/login`, mock public configuration, mobile 390×844, Lighthouse 13.5.0 default mobile throttling, three fresh runs. Median performance **81**, LCP **3,581.5ms**, TBT **388ms**, CLS **0.0090**, accessibility **98**; transfer **353,745 bytes**. Final after-change numbers and raw evidence are recorded in `EVIDENCE.json`. Authenticated Web Vitals and field INP remain separate gates. The first optimization attempt did not materially improve LCP; its reports are retained in `initial-after/` rather than hidden.

### API, database, payload, caching and dependency audit

- Live staging schema/index inspection and `EXPLAIN (ANALYZE, BUFFERS)` were read-only. The owner-filtered live-people page used `idx_people_live` (planning 7.422ms, execution 1.241ms, zero rows for a synthetic nonexistent owner). This proves index selection for that query, not representative populated-account/RLS latency.
- Existing owner/live/name, interaction date/person, meeting start, edge source/target, and commitment-status indexes were inspected. The advisor reported 99 unindexed-FK informational entries. No blanket index creation was justified by a populated slow-query plan. A privileged empty plan does not establish end-user performance.
- Sanitized `pg_stat_statements` observations included 5 one-call entries with mean times 79.266/62.802/29.863/11.059/10.012ms. SQL text and parameters were not copied into reports.
- Connection snapshot: 7 idle, 0 other active, maximum 60. Existing persistent API pool is bounded at 5 plus 5 overflow, with pre-ping and 1,800-second recycle. No Redis, queue replacement, database replacement or extra pooler was added.
- First observed public API requests initially timed out or failed transport; readiness later returned 200 with 7,468ms then 197/122/108ms observations. A first observation is **not a proven cold start**. Warm/cold authenticated route distributions require test credentials and a verified backend commit; no p95 or cold-start guarantee is fabricated from these few samples.
- Existing server-side People pagination/search was preserved; 30-record pages and a debounced full-dataset query are tested. Capture no longer fetches 100 contacts before a user opens review. Home/Work previews have explicit limits. Large source/document text and the bounded per-source loops in the full person profile remain candidates for representative populated-account profiling; no claim of eliminating every N+1 path is made.
- Critical views use text/SVG UI rather than photographic hero payloads. Photo OCR is a dynamic `tesseract.js` import after explicit interaction; no image is added to first paint. Client image size and hosted OCR/upload performance still need an actual disposable upload test.
- Private API fetches explicitly use `no-store`; existing API middleware emits `Cache-Control: private, no-store`. No shared HTTP/Next.js cache was introduced for contacts, chat, or source records. A capture text draft uses the current user's session-storage key and is cleared after confirmed save/sign-out; it is not a shared server cache.
- No production dependency or lockfile change was required. Audit-only Lighthouse/axe packages are pinned in the ignored local tooling directory. React Query's unused provider is no longer in the root render graph; its package and provider file are retained to avoid an unrelated lockfile rewrite. CI audits production JS and hashed Python dependencies.

## Verification and honest boundaries

Raw runs, traces and reports live under `.test-tmp/mobile-overhaul/`; fixtures contain fictional people and text. Selected reviewable screenshots and compact JSON evidence are copied into this directory. CI artifacts are linked in `EVIDENCE.json` when available.

- Final browser matrix: Chromium and WebKit, widths **320, 360, 375, 390, 412, 430, 768, 1024, 1440**, reduced motion, touch emulation on phones. A Pixel 5/iPhone preset is browser emulation, not a physical-device pass.
- Tests cover the five primary routes; no horizontal page overflow; control sizing; Home error/retry versus empty state; People pagination/full search/failed save; contact create/edit/refresh/archive confirmation; duplicate Send, source wrapping, offline retry; same-session Capture draft; drawer/search focus/Escape/return focus; 200% text reachability without navigation covering Send; delayed responses; six secondary saved-tool routes; note canonical payload/source refresh. Axe checks run at 390px in both engines.
- The first full local 252-case run had **241 passes, 5 failures, 6 intentional keyboard-simulation skips**. It found real enlarged-text/navigation issues alongside worker-load timeouts. Those failures are retained; they were not relabeled as passes. Later 54-case focused acceptance had **53 passes, 1 intentional secondary-width skip**, after fixes. Final all-width and CI counts are recorded in `EVIDENCE.json`.
- Local frontend component suite: **73 tests in 16 files passed**, before the final login-module test addition. Lint and production build passed; final exact counts/commit are recorded separately. A Windows fork-worker timeout run was invalid; the complete thread-worker rerun passed.
- The first full local backend run had **469 passes and 3 failures**. Two document-worker timeouts passed when rerun without competing workers. A query-budget failure exposed implicit ORM relationship loads; that code was fixed, not the budget raised. Focused relationship/error tests then passed **11/11**. Full current CI is required before declaring regression-free.
- Migrated PostgreSQL CI at `87c48d4` passed, including the new NOT NULL dashboard audit test, tenant/schema tests, upgrade/restore proof and Docker runtime. Later commits must be checked independently. SQLite tests alone do not prove RLS.
- A Vercel preview was created on the existing staging project with production promotion unset. Its default ignored-build step canceled the first attempt; a per-deployment `exit 1` override allowed a real READY build. Final source SHA/deployment ID/HTTP verification are recorded separately.
- Automatic approval review rejected generating a Vercel authentication-bypass link because it could expose the protected preview. No bypass was generated and protection was not disabled. Connected build metadata is available; protected browser acceptance requires authenticated access.
- Render's connector can inspect/log/trigger the configured branch, but does not expose a specific-commit deploy argument. The configured staging branch remains the release branch with auto-deploy off. A dashboard/authorized existing deployment path is required to deploy the feature SHA; simply triggering that service would deploy the wrong code. No production service is touched.
- Hosted two-account tests are blocked until staging-only credentials are available. The requested local `apps/web/e2e/.env.local` was absent at the latest check. No credentials or account data are invented. Physical iPhone/Android, real software keyboard, VoiceOver/TalkBack, provider delivery and the five-task human usability exercise are **pending**, not PASS.

## Release decision and follow-up

The implementation is reviewable on the feature branch. **Do not call the whole task verified or promote production while hosted authenticated acceptance and the final CI/device gates are unresolved.** A READY Vercel build does not establish that Home works against a newly deployed backend.

Human five-task exercise: capture a note; add/find a person; find a saved promise; ask and open a supporting source; find current work. Record completion without coaching, errors, time, and a short explanation of confusing terms. No completion-rate claim is made without participants.

Remaining performance follow-up should be driven by populated staging query plans, authenticated route timings and field INP. The dashboard bundle increase is a measured tradeoff; defer nonessential menu code only if production traces justify its complexity. Do not add shared private-data caching or speculative infrastructure to improve a synthetic score.

## Reproduce

```sh
# Repo root, installed workspace dependencies, Node 22+ and Python API venv.
node scripts/mobile-tools.mjs
pnpm --filter @second-brain/web exec playwright install chromium webkit
cd apps/web
node scripts/mobile-audit-run.mjs matrix
node scripts/mobile-audit-run.mjs before
node scripts/mobile-audit-run.mjs renders-before
node scripts/mobile-audit-run.mjs renders-after
cd ../..
node scripts/mobile-build.mjs before
node scripts/mobile-build.mjs after
node scripts/mobile-lighthouse.mjs before
node scripts/mobile-lighthouse.mjs after
# Run timing measurements without competing builds/browser suites.
cd apps/api
python scripts/mobile_checks.py benchmark
python scripts/mobile_checks.py tests/test_mobile_home.py tests/test_mobile_integrity_errors.py --no-cov
```

Hosted auth uses the existing E2E harness and staging-only local credentials. Never commit `.env.local`, browser auth state, test passwords, provider secrets or customer screenshots.
