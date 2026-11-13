# Security, Privacy and Independent Audit Plan
**Security cannot be perfect.** Aim for defined protections, tested boundaries, documented residual risks and rapid remediation. Code scanners or an agent audit are not a certification and cannot replace authenticated hostile tests.

## 1. Threat model for Second Brain
Assets: private relationship histories, business cards, meeting recordings/transcripts, commitments, personal files, search embeddings, OAuth calendar tokens, MCP credentials, encryption keys, backups and booking guest contact data.
Threat actors: anonymous booking spammers, another authenticated tenant, compromised browser/session, third-party AI service, malicious file/document prompt injection, leaked CI secret, overprivileged integration, compromised coding tool or misconfigured deployment.
Trust boundaries: browser ↔ API; API ↔ Supabase; public booking ↔ private calendar; MCP tools ↔ account; AI output ↔ canonical writes; Storage signed URL ↔ owner; Windows backup runtime ↔ Google Drive; CI ↔ staging credentials.

## 2. Cloudflare security-audit-skill methodology
Reference: https://github.com/cloudflare/security-audit-skill (MIT; review pinned source before installing). The official project describes a **six-phase** process:
1. Reconnaissance: inventory attack surfaces/trust boundaries, maintain `architecture.md` and `coverage-ledger.json`.
2. Coverage-led hunting: systematically check modules, create evidence-backed candidate findings.
3. Candidate validation: an independent verifier tries to disprove each candidate.
4. Structured output: `findings.json` statuses **confirmed / needs_validation / rejected** using the repository schema.
5. Independent record verification: re-evaluate final claims against current exact SHA.
6. Neutral reports: `REPORT.md`, `FINDINGS-DETAIL.md`, `NEEDS-VALIDATION.md`.
Use this process only on assets owned/authorized. Review installer and transitive dependencies; don't paste secrets into audit prompts. Never interpret `0 confirmed findings` as "secure" if coverage is incomplete.

## 3. Mandatory attack-class matrix
| Boundary | Tests and required behavior |
|---|---|
| Supabase RLS | Real authenticated A/B API and SQL-context checks for read/write/update/delete across people, meeting, commitment, source, vector, account settings; A cannot access B |
| Privileged functions | Review `account_active(owner uuid)` SECURITY DEFINER owner check and grants; prove it cannot query unrelated owner; do not revoke blindly if policies use it |
| Auth/session | Signed JWT verification, expiry, revoke, refresh, guest boundaries, auth header stripping, csrf/cookie flags, signup closed by default |
| Recording Storage | Private buckets, signed URL scope <= minutes, MIME/path validation, owner checks, retention/expired denial, no access to B object even with guessed ID |
| Downloads/exports | Source authorization and no cross-user data leakage, sanitized filenames, no insecure temporary public URLs, encrypted portable export |
| Meeting consent | Permission to record and separate AI-provider-processing notice; delete/pause operation; app doesn't secretly record in background |
| Public booking | Enumeration, spam/rate limiting, timing leaks, calendar privacy, guest PII minimization, idempotency/race double-booking, signed cancellation links |
| OAuth calendars | Min-scoped tokens encrypted server-side, CSRF state, redirect allowlist, revoke, provider domain validation, webhook signature/replay |
| MCP | Token revocation, user scope, tool injection, unintended write capability, SSRF, leakage through agent responses and logs |
| LLM/RAG | Prompt injection via transcript/doc, fabricated citations, hidden commands in files, context poison, unsafe connector/autonomous actions, PII crossing provider policy |
| CI/supply chain | Dependency lock/audit, secret scanning, branch protection, least-privileged workflow tokens, no auth traces/screenshots in public artifacts |
| Recovery | Encryption key custody, file integrity/remote sync, offsite download, isolated restore, Storage bytes and Auth managed-service scope, deletion propagation |
| Availability | Oversized uploads, audio bombs, expensive prompts, retries, denial-of-wallet, sleeping backend, upload races, worker backlog |

## 4. Pre-beta blockers
- Previously exposed **separate legacy/production database password** was not yet verified rotated in prior release snapshot. Identify *exact* dependent services and remediate before real-user pilot; avoid mixing it with already-rotated staging credential.
- Independently verified encrypted offsite backup and restore. Synthetic encryption roundtrip != real-data recovery.
- Actual A/B isolation in **deployed** app, not only mock tests.
- Check Supabase advisors: leaked-password protection if supported by current plan; SECURITY DEFINER guard; intentionally policy-less server tables must deny client access.
- Privacy notice, lawful provider terms for recordings, consent, user data export/deletion, retention and incident plan. No public paid/commercial deployment on disallowed hosting plan.
- Audit of current signup, public booking links and recording exposure, file upload validation and unsafe logging.

## 5. Security acceptance
- **Zero unresolved Critical or High vulnerabilities that could expose one tenant to another, corrupt data, enable unauthorized external actions or permanently lose the system of record** before real external users.
- No absolute claim of zero risk; medium/low findings have owner, remediation plan and disclosure decision.
- Every confirmed finding contains exact commit, reproducer (safe synthetic), expected vs observed behavior, affected boundaries, fix PR and regression test.
- Evidence records stripped of real PII and credentials; never upload production database dumps to GitHub Actions.

## 6. Privacy / legal controls
- Default private. Explicit invitation, recording permission, separate provider terms, clear deletion/retention window, accessible export, automatic deletion policies actually running.
- Data-minimal analytics (event names/counters/times), not transcripts/contacts/recording samples.
- For Gemini API free tier, official pricing states submitted content can be used to improve Google's products; do not feed confidential meetings or client data without a suitable privacy arrangement. Check current terms for other providers and hosting.
- Guest booking confirmation shouldn't expose an authenticated person's secret relationship or meeting notes. Email invites/notifications should be opt-in and respect marketing laws and anti-spam rules.
- Product should allow the user to see and correct AI-derived facts and revoke assistant/MCP integration rights.

## 7. Incident and rollback operations
- If credential leaked: revoke/rotate, identify dependents, redeploy, inspect logs and tell affected users if legally required.
- If cross-tenant leak: disable offending endpoint, preserve minimal evidence, assess scope, fix/verify with two users, do not quietly continue rollout.
- If AI provider cost spike: disable costly feature via flags, keep source data safe, show user-friendly paused state.
- If data lost: stop writes/unsafe migrations, restore from verified snapshot to isolation, reconcile and assess data loss; never overwrite cloud data during proof-of-recovery.
- Maintain support contact, incident log and consent records.

## 8. REA use boundary
REA (`https://github.com/morluto/rea`, MIT) can assist **permitted** behavioral analysis and evidence collection on our own app, route/API tracing and regression. It is not a security audit substitute, not required for UI redesign, and should not be used to bypass third-party access controls, DRM or competitor terms. Prefer ordinary browser tests and source inspection whenever sufficient.
