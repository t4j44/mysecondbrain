# Mobile UX and performance acceptance — 22–23 October 2026

This report separates implemented code, synthetic/local measurements, migrated PostgreSQL CI, hosted acceptance, and physical-device testing. A passing fixture is not proof of a working hosted account or AI provider.

## Scope and release boundary

- Repository: `t4j44/mysecondbrain`; baseline: `1c4d537` on `codex/second-brain-release-hardening`.
- Implementation branch: `codex/mobile-first-performance`. Production and the release branch were not merged or promoted. No hosted schema migration, billing change, new service, shared personal-data cache, or provider replacement was introduced.
- The user requested execution of the supplied mobile-overhaul document and a parallel performance audit. Instructions in the document were treated as task requirements within that request, not as independent permission to weaken security or publish private records.
- GRAVITAS decision: deep implementation across shared layout, API, and private-data boundaries. Existing architecture and canonical APIs were retained. No subagents were delegated. Existing unrelated untracked workspace files were preserved.

Final code: **`734ed7ac7aaa51059e161257fd4667994e0e1399`**. [Protected preview](https://second-brain-web-staging-git-co-699a83-thenadish-4808s-projects.vercel.app) is **READY** at that commit (`dpl_G8jp1Q3K9yMTrVz4JRHR9LccCUZY`). Use this stable protected branch address: the API allows only specifically reviewed origins, not arbitrary generated deployment URLs.

| Final gate | Actual result |
| --- | --- |
| [Security and quality CI](https://github.com/t4j44/mysecondbrain/actions/runs/39833678992) | **PASS**: 477 backend tests, 74 frontend tests, typecheck/lint/build, both dependency audits, 3 meeting viewports, and 308 mobile browser passes / 0 failures / 16 intentional skips. |
| [Migrated PostgreSQL CI](https://github.com/t4j44/mysecondbrain/actions/runs/39833688981) | **PASS**: 67 integration tests, seeded upgrade, isolated restore and actual API Docker runtime. |
| Real staging phone flows | **PASS**: 9/9 at 320px and 390px across Chromium/WebKit, plus 2/2 capture/retrieve/act/private-draft journey checks. |
| Protected preview browser/API integration | **PASS**: authenticated Chrome loaded real Home records; at 390×844 Ask retrieved the fictional test record with source links; the first citation opened the matching owner-scoped outcome. Scroll width was 390px. |
| Exact-origin security check | **PASS**: the two explicitly approved preview origins received 200 preflight with the exact matching origin; an untrusted origin received 400 and no allow-origin header. Existing origins preserved; no wildcard or protection bypass. |
| Physical devices, field performance and human acceptance | **NOT VERIFIED**. These remain separate from emulation and synthetic/automated acceptance. |

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

The final performance samples were recorded at `9ad17b1` with Next.js 15.5.28. The subsequent application change at `734ed7a` only anchors enlarged-text conversation navigation to the document; its complete regression matrix passed independently. Physical-device or field-performance results are not inferred from these lab samples.

| Measurement | Baseline | After | Meaning |
| --- | ---: | ---: | --- |
| Home + activation SQL statements | 80 | 17 | 78.75% fewer on the same fictional 6-project/6-meeting graph with production participant mappings registered. |
| Warm median service time | 200.081ms | 57.585ms | Three warm SQLite harness samples after one compilation sample; 71.2% lower. Not network or hosted PostgreSQL latency. |
| Warm median SQL execution time | 107.266ms | 23.671ms | Same harness; 77.9% lower. |
| Response payload | 7,765 bytes | 7,765 bytes | Exact serialized response equality asserted across both versions and all runs. |
| Message render calls while typing | median 3,540 | 0 | Actual message render functions, 60 fictional history messages, 29 typed characters, three development Profiler runs. Not field INP. |
| Login initial JavaScript, gzip | 232,443 bytes | 160,372 bytes | 31.0% lower after deferring the auth SDK. |
| Assistant initial JavaScript, gzip | 232,201 bytes | 246,750 bytes | 6.3% larger: focus-managed menus/dialogs and reliability controls add code. This is a measured cost, not a claimed bundle improvement. |
| Home initial JavaScript, gzip | 231,525 bytes | 246,366 bytes | 6.4% larger for the shared accessible shell and recovery UI. |
| People initial JavaScript, gzip | 235,208 bytes | 248,298 bytes | 5.6% larger. |
| Capture initial JavaScript, gzip | 232,692 bytes | 248,412 bytes | 6.8% larger. OCR remains dynamically imported only after a photo action. |
| Work initial JavaScript, gzip | 224,591 bytes | 244,763 bytes | 9.0% larger; now loads actual work summaries rather than only static destination cards. |

Lighthouse: production Next.js `/login`, mock public configuration, mobile 390×844, Lighthouse 13.5.0 default mobile throttling, three fresh runs per version. Baseline → final patched Next.js 15.5.28 median: performance **81 → 90**, LCP **3,581.5 → 3,251.001ms**, TBT **388 → 200ms**, CLS **0.0090 → 0.0095**, accessibility **98 → 100**; transfer **353,745 → 220,352 bytes** (37.7% lower). The mobile LCP target below 2.5 seconds is **not met**. Baseline scores were 79/81/84; final scores 68/92/90. An intermediate pre-security-patch run regressed to median 79/TBT 492ms and its reports are retained in `lighthouse-pre-next-patch/`. The substantial first-run variability prevents a universal speed guarantee or attribution of every gain to a particular edit. The largest after-change element was asynchronous Google-provider status text with mock provider configuration, which limits how well these lab numbers represent live sign-in. Authenticated Web Vitals and field INP remain separate gates. Raw summaries are in `evidence/lighthouse-before.json` and `evidence/lighthouse-after.json`.

### API, database, payload, caching and dependency audit

- Live staging schema/index inspection and `EXPLAIN (ANALYZE, BUFFERS)` were read-only. The owner-filtered live-people page used `idx_people_live` (planning 7.422ms, execution 1.241ms, zero rows for a synthetic nonexistent owner). This proves index selection for that query, not representative populated-account/RLS latency.
- Existing owner/live/name, interaction date/person, meeting start, edge source/target, and commitment-status indexes were inspected. The advisor reported 99 unindexed-FK informational entries. No blanket index creation was justified by a populated slow-query plan. A privileged empty plan does not establish end-user performance.
- Sanitized `pg_stat_statements` observations included 5 one-call entries with mean times 79.266/62.802/29.863/11.059/10.012ms. SQL text and parameters were not copied into reports.
- Connection snapshot: 7 idle, 0 other active, maximum 60. Existing persistent API pool is bounded at 5 plus 5 overflow, with pre-ping and 1,800-second recycle. No Redis, queue replacement, database replacement or extra pooler was added.
- First observed public API requests initially timed out or failed transport. After the verified staging deploy, all ten health/readiness requests returned 200: health first 535ms then 93/110/88/93ms; readiness first 247ms then 102/115/111/98ms. Real authenticated Home returned 200 five times: 1,053/209/213/201/195ms, 721 bytes each, all `private, no-store`. The subsequent warm-candidate median is 205ms. A first observation is **not a proven cold start**. These small empty-account samples do not justify a populated-account p95 or a causal hosted speedup claim.
- Existing server-side People pagination/search was preserved; 30-record pages and a debounced full-dataset query are tested. Capture no longer fetches 100 contacts before a user opens review. Home/Work previews have explicit limits. Large source/document text and the bounded per-source loops in the full person profile remain candidates for representative populated-account profiling; no claim of eliminating every N+1 path is made.
- Critical views use text/SVG UI rather than photographic hero payloads. Photo OCR is a dynamic `tesseract.js` import after explicit interaction; no image is added to first paint. Client image size and hosted OCR/upload performance still need an actual disposable upload test.
- Private API fetches explicitly use `no-store`; existing API middleware emits `Cache-Control: private, no-store`. No shared HTTP/Next.js cache was introduced for contacts, chat, or source records. A capture text draft uses the current user's session-storage key and is cleared after confirmed save/sign-out; it is not a shared server cache.
- The later dependency audit detected `opentelemetry-api` 1.44.0 / CVE-2026-114603, a CPU-exhaustion issue in trace-header parsing. Its [maintainer advisory](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-xcq7-p3pf-p88h) fixes versions through 1.45.0 in 1.45.1. Only that transitive version and its verified hashes changed in `uv.lock` and the exported `requirements.lock`; the regenerated lock audit returned **No known vulnerabilities found**. Audit-only Lighthouse/axe packages stay in ignored local tooling. React Query's unused root provider was removed from the render graph without rewriting the JS dependency lock.
- A subsequent JS audit identified Next.js advisories [GHSA-2464-fhr4-w9xw](https://github.com/advisories/GHSA-2464-fhr4-w9xw) (critical image optimization / upstream memory issue) and [GHSA-p3m5-59mp-jv5r](https://github.com/advisories/GHSA-p3m5-59mp-jv5r) (high Server Actions CPU exhaustion). Updated Next.js and its matching lint config from 15.5.27 to **15.5.28**; the lock resolves **sharp 0.35.5** and the matching Next toolchain, with related lint transitive updates. `pnpm audit --prod` returned **No known vulnerabilities found**. Lint reported no warnings/errors and the patched production build generated all 41 pages. Production deployments were not changed.

## Verification and honest boundaries

Raw runs, traces and reports live under `.test-tmp/mobile-overhaul/`; fixtures contain fictional people and text. Selected reviewable screenshots and compact JSON evidence are copied into this directory. CI artifacts are linked in `EVIDENCE.json` when available.

- Final browser matrix: Chromium and WebKit, widths **320, 360, 375, 390, 412, 430, 768, 1024, 1440**, reduced motion, touch emulation on phones. A Pixel 5/iPhone preset is browser emulation, not a physical-device pass.
- Tests cover the five primary routes; no horizontal page overflow; control sizing; Home error/retry versus empty state; People pagination/full search/failed save; contact create/edit/refresh/archive confirmation; duplicate Send, source wrapping, offline retry; same-session Capture draft; drawer/search focus/Escape/return focus; 200% text reachability without navigation covering Send; delayed responses; six secondary saved-tool routes; note canonical payload/source refresh. Axe checks run at 390px in both engines.
- The first full local 252-case run had **241 passes, 5 failures, 6 intentional keyboard-simulation skips**. It found real enlarged-text/navigation issues alongside worker-load timeouts. Those failures are retained; they were not relabeled as passes. Later 54-case focused acceptance had **53 passes, 1 intentional secondary-width skip**, after fixes. Final all-width and CI counts are recorded in `EVIDENCE.json`.
- Earlier implementation CI passed 475 backend tests, 74 frontend tests and the 324-case browser matrix at `dc54f46`; the final code's independently passing gates are above. The local pre-composer-fix full matrix had 304 passes, 4 WebKit enlarged-text failures and 16 skips; those are retained. A later final-candidate CI run found one remaining enlarged-text overlap at WebKit 1024px (307 pass / 1 fail / 16 skips). Navigation now anchors to the scrolling document only in enlarged-text conversations. The repaired 390px and 1024px cases passed **10/10 repeated checks**, their screenshots were inspected, and the final full CI matrix passed all 308 applicable cases. A separate real Next.js public-authentication matrix passed **54/54**, across all 18 browser/size profiles. Earlier invalid fork-worker runs were not counted as passes.
- The first full local backend run had **469 passes and 3 failures**. Two document-worker timeouts passed when rerun without competing workers. A query-budget failure exposed implicit ORM relationship loads; that code was fixed, not the budget raised. Focused relationship/error tests then passed **11/11**. Full current CI is required before declaring regression-free.
- Migrated PostgreSQL CI passed independently at the earlier implementation and final code, including the dashboard NOT NULL audit regression and tenant/schema checks. SQLite tests alone do not prove RLS.
- A Vercel preview was created on the existing staging project with production promotion unset. Its default ignored-build step canceled the first attempt; a per-deployment `exit 1` override allowed a real READY build. Final source SHA/deployment ID/HTTP verification are recorded separately.
- The earlier protected preview verified login, native invalid-email validation, protected-route redirect and disposable-account sign-in at 390px. The final source-matched protected preview and its real browser/API checks are above. Automatic approval review previously rejected a bypass link; no bypass was generated and protection remains enabled.
- Existing Render staging service is **live** on audited backend source `ac7d4bf3b2aa899a0d5dbd458c9445f03ca98dbb`, deployment `dep-dbd5nsafngtc73fnc71g`, with the two user-approved CORS additions. Later frontend-only changes do not change this backend source. Health metadata initially reported a stale pinned `RELEASE_SHA`; the fix now prioritizes Render's runtime commit. It passed 13 focused tests and live health returned the exact patched runtime SHA. Production and the configured release branch were not changed.
- Two disposable staging test accounts were created through the authenticated Supabase staging dashboard, with credentials only in the ignored local E2E file. Project-wide email verification was not changed. Real API checks proved contact persistence, account B receiving 404 for account A's synthetic contact, and contact cleanup.
- Real Next.js connected to staging Auth/API subsequently passed **9/9** checks across Chromium/WebKit at 320px and 390px: sign-in, all five primary pages, same-session draft reload, and contact create/edit/refresh/cancel-archive/confirmed-archive. This is hosted-service integration through the existing allowed local origin, not protected-preview acceptance. Earlier runs exposed a real WebKit draft-loss race and form input arriving before hydration; Capture now waits for its user-specific recovery key and writes input synchronously, while the person form waits for hydration before accepting edits. Six focused fixture checks and all 74 frontend component tests passed after these changes. One earlier edit navigation unexpectedly redirected to Home; the later phone run passed, but the intermittent auth behavior is not proven absent. The artifact directory retains failed traces locally; credentials and tokens are not copied into the report.
- The real staging capture/retrieve/act journey passed **2/2** (including sign-in) with Next.js 15.5.28 at 390px: reviewed capture saved, a task was created, the record persisted, a supporting source was retrieved, and a private portfolio draft was saved. Public publication stayed disabled by the existing release gate. The earlier attempt exhausted its 120-second budget; it is retained. Manual capture fallback was observed when AI extraction was unavailable; passing this journey does **not** establish Gemini extraction/provider delivery, physical microphone behavior or public publication.
- **Hosted integration failure found and fixed:** the preview initially showed Home `NETWORK_ERROR` because the staging API's CORS list excluded it. Automatic approval review rejected expanding that boundary. The user subsequently explicitly approved exactly the earlier protected preview address and the stable protected branch alias. Those two addresses were appended to both existing staging origin lists, all existing entries were preserved, and the same audited backend source was redeployed. Positive/negative preflight checks and the authenticated protected-preview Home/Ask/source journey then passed. No wildcard, protection bypass, proxy workaround or production change was applied.
- Physical iPhone/Android, real software keyboard, VoiceOver/TalkBack, provider delivery and the five-task human usability exercise are **pending**, not PASS. Secondary routes outside the explicitly tested saved tools and main flows are listed with their actual coverage in `ROUTE_INVENTORY.md`.

## Release decision and follow-up

Implementation, the final automated gates and the executed protected-preview journey **PASS**. Overall release acceptance remains **PARTIAL**: mobile LCP still exceeds 2.5 seconds, first-run performance varies, and physical-device/provider/human gates remain open. No critical failures remain in the executed final matrix; that is not a guarantee covering every untested feature or physical device. No production promotion or merge was performed. The ready build was followed by actual authenticated browser/API/source verification.

Human five-task exercise: capture a note; add/find a person; find a saved promise; ask and open a supporting source; find current work. Record completion without coaching, errors, time, and a short explanation of confusing terms. No completion-rate claim is made without participants.

Three contacts left by interrupted tests were archived only in the dedicated disposable account, matching the exact synthetic name prefix. The fictional capture/task/private-draft proof remains available there for review. No customer records were used for screenshots or test writes.

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
# Existing allowed local origin, real staging services, disposable credentials only:
cd apps/web
pnpm exec playwright test --config=playwright.staging-mobile.config.ts --project=chromium-320 --project=chromium-390 --project=webkit-320 --project=webkit-390
pnpm exec playwright test --config=playwright.staging-mobile.config.ts --project=provider-journey
cd ../..
# Run timing measurements without competing builds/browser suites.
cd apps/api
python scripts/mobile_checks.py benchmark
python scripts/mobile_checks.py tests/test_mobile_home.py tests/test_mobile_integrity_errors.py --no-cov
```

Hosted auth uses the existing E2E harness and staging-only local credentials. Never commit `.env.local`, browser auth state, test passwords, provider secrets or customer screenshots.
