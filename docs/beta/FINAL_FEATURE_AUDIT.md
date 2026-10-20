# Release audit — 2026-10-20

Production ready: **NO**. The initial audit below was written before implementation;
the final delta follows it. Current executed gates belong in RELEASE_EVIDENCE.md.

## Verified starting identity

- Remote: `https://github.com/t4j44/mysecondbrain` (fetched successfully).
- Starting branch: `feature/relationship-loop`, SHA
  `a97e8f64b55c0441a9d46d3570ecd98ea0ca1052`.
- Release branch: `codex/second-brain-release-hardening`, created from that SHA.
- Meeting `49d9f34d09037ac30bc4c6b85ac00ff115f958a0` is an ancestor, five
  commits behind. Prompt Intelligence `8862f70` is also included. Remote main is
  `55cfeaf`; local main has one unpublished commit and is not the base.
- No tracked modifications at start. All pre-existing untracked recovery docs,
  archives, .agents, graph snapshots and render.yaml are preserved. No clean/reset.
- 35 migration files (including 21b), through `20261013000034_email_contacts`.
  Versions 33/34 already exist: the specification's historical migration-32
  reference must not be interpreted as permission to reuse those numbers.
- Base CI: [security/quality 38318230717](https://github.com/t4j44/mysecondbrain/actions/runs/38318230717)
  and [PostgreSQL 38318230720](https://github.com/t4j44/mysecondbrain/actions/runs/38318230720)
  succeeded. The connector's PR-only workflow query missed these push runs;
  repository Actions API verified them. These are **base**, not final-candidate proof.
- Workflows: security_ci.yml, postgres.yml, beta-e2e.yml. The last requires manual
  staging dispatch and two ordinary users; test collection is not execution.
- Historical HANDOFF.md's “uncommitted” statement is stale: implementation is
  committed in c9ce949/b74fef8/49d9f34.

## Initial implementation gap matrix

Labels describe code, not hosted acceptance. EXISTS means reusable implementation;
WORKING BUT UNVERIFIED means hosted/provider/device proof is absent.

| Area | Status | Evidence / required extension |
|---|---|---|
| Auth, owner context, JWT, RLS | EXISTS / WORKING BUT UNVERIFIED | dependencies/auth.py, db/rls.py, migration 20, PG isolation tests; rerun final revision and hosted A/B |
| Context/card/moment/photos/temporal provenance | EXISTS / WORKING BUT UNVERIFIED | context_events, context media, capture review; private-object and physical-phone tests required |
| People/CRM/Action Queue/outreach receipts | EXISTS / WORKING BUT UNVERIFIED | relationships/person_context/outreach; opening a draft is distinct from explicit sent/outcome receipt |
| Work/ventures/tasks/decisions/memories | EXISTS | retain canonical models/services; regression suite and staging journey |
| Ask, keyword/pgvector retrieval | EXTEND | meeting_chunks indexes transcript segments; detailed sections/notes and exact evidence navigation missing |
| Documents/MarkItDown/private Storage | EXISTS / WORKING BUT UNVERIFIED | normalized Markdown/chunks, OCR fallback; retain converter isolation, hosted files/MCP journey required |
| MCP/OAuth/session finalization/Prompt Intelligence | EXISTS / WORKING BUT UNVERIFIED | official transport, scoped draft/context tool, revoke tests; real external client required |
| Google Drive/Calendar/multiple accounts/Gmail dates | WORKING BUT UNVERIFIED | newer lineage retained; live OAuth/sync not certified; gate optional integration if unverified |
| Portfolio approval/publication/revoke | WORKING BUT UNVERIFIED | existing review/revoke; optional release gating and signed-out acceptance required |
| Capture/upload/quota/private audio/live text | EXISTS / WORKING BUT UNVERIFIED | meeting_audio/usage/live, migration 32; raw audio is not redacted by text privacy mode |
| Diarization/full transcript/retry/worker | EXTEND | chunk-local IDs and persisted transcription; extract batches lack checkpoints, paid repeat inference risk |
| Executive/detailed summaries/side topics | FIX / EXTEND | extractor recursively compresses summary to 4,000 chars; no durable comprehensive section digest |
| Evidence | FIX / EXTEND | Candidate has quote only; validation against concatenated transcript can cross speaker boundaries; add canonical segment/offset proof |
| Editable notes/minutes/export | EXTEND | no independent versioned user notes, minutes or authenticated Markdown export |
| Title/purpose/agenda/timezone | EXTEND | preserve manual title; proposals and known timezone need explicit review; confirmation currently labels UTC unconditionally |
| Meeting graph | EXTEND | event→meeting/derived provenance exists; typed meeting→participant/venture/project/produced links missing |
| Deletion/export/closure | EXISTS / EXTEND | existing durable erasure; verify new notes/graph/index lifecycle and pending retries |
| Responsive web/PWA | WORKING BUT UNVERIFIED | existing 320/390/1440 synthetic fixture; extend reading/review tests; physical device proof absent |
| Runtime/Docker/FFmpeg/worker | WORKING BUT UNVERIFIED | Dockerfile installs ffmpeg; no Docker command available locally; actual image build required |
| Dependencies/build reproducibility | FIX | requirements caps google-genai below 1, pyproject does not; Docker/CI use ranges rather than uv.lock |
| Metrics/quotas/backup/recovery | EXISTS / WORKING BUT UNVERIFIED | durable jobs, health SHA, PG fresh/upgrade/restore CI; hosted storage recovery and worker interruption must be proven |
| New database/CRM/vector system/native app/billing | NOT NEEDED | canonical Supabase/pgvector/FastAPI/Next.js architecture retained |

## Ordered execution and policy

Policy: planning=deep, context_depth=dependency, verification_depth=full,
delegation=conditional impact-auditor/reviewer. Public meeting schemas and retrieval
have broad callers; an independent read-only audit and later adversarial review
reduce interface/security regression risk. Changes are reversible development work.
Hosted, destructive, production, credentials and billing operations are excluded.

1. Extend existing JSON schemas with versioned structured digests and exact segment
   evidence. Preserve legacy summary/Candidate API fields; deterministic lossless
   merge and extraction checkpoints, explicit bounded-budget failures.
2. Add user-note history/concurrency and reviewed metadata in existing meeting JSON;
   authenticated Markdown export and derived minutes. Do not overwrite transcript,
   user title/agenda, or user notes. No migration unless existing storage is unsafe.
3. Extend confirmation with owner-proved typed temporal graph links; retain explicit
   selection/idempotency and deletion semantics. Index all meaningful sections.
4. Extend current mobile review journey, evidence jumps, transcript search, copy and
   download; preserve recorder/adapters. Add focused synthetic bilingual 90-minute,
   API, graph, notes conflict/retry/deletion and UI coverage.
5. Repair confirmed operational/dependency gaps; run full local and final SHA CI,
   independent review, PG fresh/upgrade/restore, Docker and hosted read-only checks.
6. Prepare isolated staging runbook; execute only identified authorized staging.
   Real external MCP/provider, hosted A/B, physical phones, seven-day dogfood,
   consented beta and production authorization remain independent hard gates.

No keys or hosted test credentials are present in the current process environment.
That does not establish their absence on hosting providers. No hosted migration,
production deployment, billing change, merge or destructive operation is authorized.

## Implemented delta

Extended the existing extractor, capture/job retry, confirmation graph, indexing,
MCP reads and phone review. Added structured v2 sections/exact evidence, separate
executive/detailed/notes/minutes/transcript outputs, versioned user notes and review,
authenticated Markdown export, last-chunk/secondary-topic retrieval and segment
navigation. Existing recorder, CRM, private storage, OAuth, context and durable jobs
were reused. No schema migration was needed. Confirmation still gates CRM writes.

Fixed lossy summary merging, cross-speaker quotation acceptance, stale minutes,
legacy conditional/deadline compatibility, stale note concurrency, list payload
overfetch, dependency-manifest drift, vulnerable runtime families and Next async
server APIs. Added real PostgreSQL concurrency regressions and actual Docker/worker
CI steps. Independent review findings have focused reproducer/regression coverage.

Hosted Google OAuth/sync and portfolio publication are disabled by default pending
acceptance; users see a truthful notice, while disconnect/revoke remain available.
Free-mode audio needs an explicit non-sensitive attestation; hosted private audio
is separately blocked until verified privacy/plan acceptance. No billing enabled.

Deferred by explicit owner direction: separate staging provisioning/configuration,
hosted DB/Auth/Storage/provider/MCP/physical-device acceptance, unattended-runtime
budget, hosted recovery, dogfood, beta and production authorization. Production
credentials/data/storage were not used for these tests. One unsuppressed high build
dependency finding (`braces`, no upstream fix) remains documented in evidence;
runtime dependency audits are clean. No new products or decorative graph built.
