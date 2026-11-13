# Second Brain V1 — Start Here
**Specification pack version:** 2026-11-12  
**Goal:** One cohesive, simple, secure Second Brain web application; release first as an invite-only pilot, then expand toward the full Fireflies-style intelligence + Timetics-style scheduling vision.  
**Repository:** https://github.com/t4j44/mysecondbrain  
**Release tracker:** https://github.com/t4j44/mysecondbrain/issues/32  
**Companion roadmap:** https://github.com/t4j44/mysecondbrain/issues/33

## Use in one Astra/Codex conversation
1. Extract this ZIP **into the root of the existing repository**, so the folder becomes `E:\second brain\docs\second-brain-v1\` (adjust if your checkout uses another location). **Do not overwrite or reset existing code.**
2. Open the existing repository in **one coding-agent session**. Select GPT-6 Astra if available. Do **not** launch another agent editing the same branch concurrently.
3. Paste the complete text of `01_MASTER_ASTRA6_EXECUTION_PROMPT.md` into that coding-agent conversation. It instructs the agent to read **all** pack files, inspect live code and then implement in dependency order.
4. Grant only necessary, scoped access. Never paste Supabase passwords, encryption passphrases, API secrets, recordings or customer data into chat or Git.
5. Let the agent produce small testable PRs, not a single unreviewable giant change. Follow `11_EXECUTION_BACKLOG_AND_HANDOFF.md` and request a final evidence-backed GO/NO-GO.
6. **You, the founder,** complete only unavoidable private credential entry, product acceptance on real devices, consent/policy decisions and the actual pilot interviews.

## Product in one sentence
> Second Brain keeps a correctable, user-controlled, evidence-backed history of conversations, people, decisions and commitments, and helps you know **what you promised, what changed and what to do next**.

## Hard separation: V1 architecture vs pilot release
**Design the complete coherent V1 architecture and user experience now.** Implement release-critical features before invitations. Advanced features are represented in the same product model and can be built behind flags, but they are **not** allowed to delay security/recovery or be marketed as live until accepted.

### Exact initial navigation
`Home` · `People` · `Meetings` · `Work` · `Ask`, plus a global `+ Capture` action, universal Search, and a small `More`/Settings area. Calendar and bookings live under **Meetings**, not as extra primary navigation.

### Verified snapshot, NOT a declaration of readiness
- As of connected-account checks on **2026-11-12**: Supabase staging `rpkjmdrralzxhdsgceal` is ACTIVE_HEALTHY; Render staging live after a confirmed DB-connection rotation; CI security/schema workflows previously passed.
- GitHub release issue #32 remains open. Draft **PR #45** corrects the obsolete hosted E2E URL but is unmerged; draft **PR #46** has backup/encryption and restore tooling that passed **synthetic** tests, but a real encrypted staging → off-device copy → independent restore has **not** been evidenced.
- Unverified: deployed signed-in V2 UX, full real-account A/B isolation, actual hosted end-to-end meeting/citation/booking workflows, compliance of current free hosting for external commercial beta, exposed separate old-project DB credential rotation.
- Fireflies-like or Timetics-like capabilities not seen in the current codebase MUST be treated as **proposed**, never represented as implemented.
- No public production promotion, live payment collection, or real user-data invitation until issue #32's gates pass.

## File map
| File | Why it exists |
|---|---|
| `01_MASTER_ASTRA6_EXECUTION_PROMPT.md` | The **single prompt** to paste to Astra/Codex |
| `02_PRODUCT_PRD_AND_FEATURE_MATRIX.md` | Personas, V1 contract, existing vs proposed, priorities |
| `03_UI_UX_INFORMATION_ARCHITECTURE.md` | Navigation, design tokens, every major screen, mobile, accessibility |
| `04_MEETINGS_BOOKING_MEMORY_WORKFLOWS.md` | Fireflies + Timetics adapted to Second Brain; acceptance criteria |
| `05_TECHNICAL_ARCHITECTURE.md` | Existing-stack-first design, APIs, entities, jobs, source evidence |
| `06_SECURITY_PRIVACY_AUDIT.md` | Cloudflare-style audited threat model, privacy gates, tenant isolation |
| `07_QA_E2E_RELEASE_GATES.md` | Exact acceptance matrix; blockers; pilot vs public GO/NO-GO |
| `08_ENCRYPTED_DRIVE_BACKUP.md` | Free pilot backup + independently verified recovery, no new cloud infrastructure |
| `09_PILOT_GTM_EVIDENCE.md` | Founder dogfood, 5–10 testers, analytics, interviews, testimonials, accelerator evidence |
| `10_REFERENCES_AND_RESEARCH.md` | What the requested repos and competitor sites really offer; licenses/limitations |
| `11_EXECUTION_BACKLOG_AND_HANDOFF.md` | Ordered PR sequence, evidence logs, durable handoff for long agent tasks |
| `12_UI_COPY_WIREFRAMES.md` | Concrete low-fidelity desktop/mobile layouts and user-facing copy |
| `13_FREE_STACK_AND_LAUNCH_OPERATIONS.md` | Provider limits, AI privacy, feature flags, incident response and upgrade triggers |

## Founder decisions fixed for this pack
- **Start:** English-first, responsive web app. Other languages later; no compulsory mobile app for first beta.
- **Pilot:** 7-day founder dogfood (synthetic/non-sensitive data), then 5–10 invited users; 20–100 only with explicit acceptance and real retention signals.
- **Costs:** Target $0 **additional infrastructure spending** in the prototype/pilot preparation stage. A free stack is not automatically acceptable for real-data external business beta; flag terms and privacy gaps rather than silently violating them.
- **Backup:** Private encrypted Google Drive folder, passphrase stored separately; independent recovery test; migrate to managed backup/hosting later if justified.
- **AI:** Free-tier providers only for synthetic/non-sensitive data where terms allow provider product improvement. Confidential user data requires suitable privacy arrangements, not merely a checkbox.
- **No deceptive claims:** No fabricated traction, testimonials, uptime, security certifications, AI accuracy or claims that synthetic tests equal hosted acceptance.

## Definition of success
A first-time nontechnical user can invite/enter, capture information, find a person, record or upload a meeting, review accurate grounded outputs, create/confirm a commitment, retrieve the right answer with source proof, export/delete their data, and book or manage a meeting **when the scheduling feature is actually accepted**. They should never have to understand MCP, embeddings, pgvector, jobs, tokens, JSON or infrastructure.
