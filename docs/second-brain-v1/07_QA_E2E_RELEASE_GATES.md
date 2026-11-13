# QA, Hosted E2E and Release Gates
## Objective
Prove the product actually works on the deployed version, after login, using **two distinct synthetic accounts**. A green build or ready deployment is insufficient. Keep test accounts strictly segregated from production/legacy projects.

## 1. Test environments and truth
- **Local/unit:** fast deterministic mocks; useful but never hosted proof.
- **Isolated PG17 integration:** migrations, RLS, data model, restore and pgvector; no real user data.
- **Staging hosted:** project `rpkjmdrralzxhdsgceal`, Render backend + protected verified V2 Vercel preview. Pin exact web/backend commit and runtime config.
- **Prod/public:** NOT a test target. No promotions, migrations, payment or external sends until acceptance.
- E2E workflow under `.github/workflows/beta-e2e.yml` currently had an obsolete Vercel target in main as of inspected baseline; draft PR #45 corrects target but secure preview automation bypass and environment secrets still require validation. Preserve protection; never solve testing by making preview public.

## 2. Test accounts
Create synthetic A and B with distinct confirmed Auth identities, owned data and representative fixtures: Person A / Person B, different meetings and files, commitments, transcript segments, booking types. Use private GitHub environment secrets or an equivalent authorized runner, never plaintext code. Use test fixture aliases in evidence, not account emails/passwords.

## 3. Critical E2E scenarios (PASS only with browser/API proof)
| Test ID | User journey / assertion | Required evidence |
|---|---|---|
| E2E-01 | Invite/login/logout/session expiration/recovery | Browser run + backend log + exact SHA |
| E2E-02 | Home/nav loads after login and current signed-in V2 is deployed | Actual screenshots 320px/desktop + route check |
| E2E-03 | Global Capture saves note; list and Ask retrieve it | Round-trip ID plus source citation |
| E2E-04 | People add/edit/search/merge/delete with source timeline | A own success; B denied |
| E2E-05 | Record microphone or upload synthetic MP3/M4A/WebM with consent | Real device/browser, processing state |
| E2E-06 | Meeting transcript speaker labels and correction persist | Before/after segment checks |
| E2E-07 | AI summary/decision/commitment points to exact segment | Click-through opens timestamp; manual gold check |
| E2E-08 | Confirm/edit/reject extracted commitment; Work and Person update | Canonical record ID + audit evidence |
| E2E-09 | Ask across meetings with citations; unsupported query abstains | Source URL/segment IDs + negative case |
| E2E-10 | Open/download original recording before expiry | Owner download hash/MIME/filename, mobile acceptance |
| E2E-11 | Expired/deleted recording cannot download; transcript policy obeyed | Negative server and UI assertions |
| E2E-12 | Booking link + availability timezone/DST + confirmed slot | Two timezone cases + no double-book |
| E2E-13 | Cancel/reschedule link and invalid token negative cases | Transaction and notification state |
| E2E-14 | Calendar permission connect/revoke or explicit ICS fallback | Consent/scopes, sync status, no silent provider changes |
| E2E-15 | MCP user scope, revocation, read/write and no leakage | Independent two-user consumer integration |
| E2E-16 | Export/delete account + indexes/media/private objects | Scope + post-deletion negative searches |
| E2E-17 | Network failure, waking Render, retry, offline audio draft | No silent loss, clear recovery message |
| E2E-18 | Basic accessible navigation via keyboard and screen reader | WCAG checks + manual notes |
| E2E-19 | Public booking abuse/rate limits & PII restrictions | Rejected unauthorized requests |
| E2E-20 | Anonymous cannot see private meeting/person/contact routes | 401/403; no leaked snippets |
| E2E-21 | AI provider privacy gate for confidential data | Rejected/downgraded mode, explicit user explanation |
| E2E-22 | Feature flags disable bots, payments, Opportunity Scout and unfinished actions | UI and endpoint negative checks |

**Scheduling E2E-12 to -14 are mandatory only if the public booking feature is enabled in the pilot. If not accepted, flag and hide the unfinished feature and explicitly mark it NOT IN PILOT.**

## 4. Tenant-boundary negative matrix
A tries to directly access B's known IDs, signed URLs, transcript segments, person timeline, commitments, file search, embeddings, calendar connection, booking owner settings, exports, MCP tool results and deletion endpoints. Expected result: server denies or returns no data with no B identifiers or content, including error details/metadata. Repeat in both directions A→B and B→A, and with no auth.

## 5. Real recording QA
- Synthetic owner-approved multilingual test recording, varying speakers, background noise, long pauses and short commitments; no real client/confidential information on a disallowed AI tier.
- Gold review manual label: transcription intelligibility, speaker-attributed accuracy, commitment precision/recall, evidence exactness and abstention on unsupported answers.
- Define minimum benchmark from pilot observations; **do not claim 95%/99% accuracy without measured denominator and task definition**. For initial gate, no hallucinated confirmed commitments, no unaudited cross-account citations, all accepted extracted actions visibly reviewed.

## 6. UX quality gates
- First action visible without scrolling at 320px and 1280px.
- Five-tab IA consistent after sign-in, +Capture globally findable, search returns sources, no dead end without an explanatory CTA.
- 3–5 unfamiliar tester sessions: record task completion and confusion. Targets: >=4/5 can add a person, capture and find a record unaided; >=4/5 can locate download and review a suggestion when feature is available. Directional targets, not claims of current performance.
- Check keyboard full journey, focus visibility, screen-reader forms, reduced motion, mobile iOS Safari and Android Chrome.

## 7. Security, performance and operations
- Required passing Security & Quality CI, PG17 migration/RLS tests, real account isolation, Cloudflare-style reviewed findings, secret scan and dependency audit.
- Proposed page performance goals (actual numbers required): LCP p75 <2.5s, INP p75 <200ms, CLS <0.1; track cold start separately. Record max concurrent audio jobs and per-user budget, not invented capacity.
- Backup proof described in `08_ENCRYPTED_DRIVE_BACKUP.md`; a cloud-uploaded encrypted file without a real restore = NOT VERIFIED.
- Support contact, error alerts, rate limits, data retention and successful local/test rollback rehearsed.

## 8. Release decisions (separate gates)
### G0 — Internal synthetic testing GO
Site functional, API ready, test accounts isolated in staging, no live data and no unsafe side effects. Restoration pending can be accepted **only** if all test data is disposable.

### G1 — 7-day founder dogfood GO
Current signed-in UI validated, core Capture→People→Meetings→Ask flows, synthetic or non-sensitive data, known failure controls; no unauthorized real sends; prioritize recovery proof before valuable data.

### G2 — 5–10 external real-data beta GO
All of: real encrypted offsite backup + isolated restore; deployed A/B RLS; relevant E2E unskipped; privacy/consent/data export/delete; proper hosting/AI-provider terms; exposed credentials resolved; error/usage monitoring; no unresolved critical/high vulnerabilities. A single failure = NO-GO for valuable real user data.

### G3 — 20–100 person beta GO
G2 + retention evidence + operational support/runbooks, capacity test, quotas, approved billing/hosting terms, active backup schedule, observed cost/user, incidents managed and no critical regressions. Do not assume small-test success scales.

### G4 — Public paid production GO
Documented lawful payment/terms/refunds/tax, sustained paid hosting, suitable AI data-protection contracts, monitored backups, recovery rehearsal, production deployment and rollback, support policy and privacy review.

## 9. Standard test report schema
```
Gate: G2 External beta
Status: PASS | FAIL | BLOCKED | NOT_TESTED
Environment: staging / non-production
Web deployment URL & SHA:
Backend deploy ID & SHA:
Supabase project ref:
CI run IDs:
Browser run ID and test suite:
A/B tenant scenarios passed/failed/skipped:
Backup file SHA-256 (encrypted only), Google Drive remote read-back and isolated restore evidence:
AI/model/data processing mode:
Known High/Critical findings:
Costs / provider license status:
Evidence links:
Reviewer / date:
Next action:
```
Do not omit skipped tests or replace inaccessible links with invented links. Update GitHub issue #32 after any material change.
