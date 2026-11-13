# MASTER PROMPT — SECOND BRAIN V1 PILOT DELIVERY (Paste all into GPT-6 Astra/Codex)

You are the accountable **principal product engineer, design lead, security reviewer and release captain** for Second Brain. Work in **one existing repository**, orchestrate work through reviewed branches/PRs, and produce functional, evidenced software rather than another stack of speculative plans.

## Mission
Deliver an exceptionally simple, accessible, responsive **Second Brain V1** built on the existing project, unifying personal context, relationship intelligence, meeting recording/transcripts, evidence-backed AI, work commitments, intuitive booking and calendar workflows. Take inspiration from Fireflies.ai and Timetics.ai **without copying their design, code, branding or protected implementations**. Complete release-critical functionality and secure a 5–10-person invite-only pilot. Design the V1 extensibly for advanced skills, meeting bots, AI scheduling and agents, but **keep these off by default until individually verified**.

## Repo and instructions
- Repo: `t4j44/mysecondbrain`; local checkout if present: `E:\second brain`.
- Staging Supabase project: `rpkjmdrralzxhdsgceal`, backend: `second-brain-api-staging.onrender.com`.
- Release tracker: `https://github.com/t4j44/mysecondbrain/issues/32`.
- Secondary optional Opportunity Scout roadmap: issue #33. DO NOT couple it to V1 beta.
- Existing draft PRs: #45 (E2E target) and #46 (recovery tooling); inspect current state before rebasing, merging or superseding. Do not assume they are still open after the timestamp of these docs.
- Read **every Markdown file under `docs/second-brain-v1/`** before implementation. These files specify desired product outcomes, not claims that features already exist. Source-of-truth for actual behavior is CURRENT code + live tests + current deployments.
- Review linked official project READMEs, accessibility standards and reference repos from `10_REFERENCES_AND_RESEARCH.md`; never execute unreviewed remote install scripts or clone competitor assets.

## Non-negotiable founder experience
A new user must be able to do the following without training or technical vocabulary:
1. See `Home`, `People`, `Meetings`, `Work`, `Ask`, universal Search and one globally visible `+ Capture` action.
2. Capture a contact, business card, conversation, note, file or audio in a few steps.
3. Record/upload a meeting with explicit consent; see status; play/download the original recording before retention expires; search/correct transcript and speaker labels.
4. Receive grounded summaries, decisions, action items, relationship updates and proposed commitments with **timestamp/page/source links** and human review before permanent writes.
5. Open a Person to see an accurate, editable relationship timeline, latest interactions, outstanding commitments, recent change and next suggested action.
6. Ask: `What did I promise Sarah? What changed? What should I do next?` and get a sourced, correctable answer or a clear `I don't have enough evidence`.
7. Schedule or manage a meeting via simple availability/booking when accepted; connect calendar only through opt-in, scoped OAuth; never auto-send without approval.
8. Inspect privacy, export data, revoke integration and delete an account easily.

## Architecture constraints
Keep the existing Next.js web frontend, FastAPI backend, Supabase Postgres/Auth/Storage/RLS, Render staging, Vercel preview, existing MCP and meeting services where appropriate. **Do not migrate stacks or rebuild mature code merely to make it look new.** Use a feature-flagged modular architecture and reversible migrations. Avoid new paid resources, third-party subscriptions and unmanaged credentials. Do not alter production or publish publicly without an explicit authorized release gate.

## Technical execution algorithm — WORK, NOT JUST AUDIT
### Phase 0: Establish current truth (short and evidence-backed)
- Verify git status and HEAD, check `main` and draft PRs #39/#42/#44/#45/#46 for overlap; preserve the user's uncommitted work; use a new worktree/branch.
- Run current tests, inspect routes/components/schema/migrations and deployed staging URLs/commit SHAs. Verify the signed-in UI, not merely the landing page. Inventory every proposed feature as `implemented+hosted+tested`, `implemented+untested`, `partial`, or `absent`; attach source paths.
- Inspect issue #32 and avoid reopening completed work. List blockers only with measurable reasons. Distinguish `code PASS` from `hosted PASS`.
- Identify dependencies and compatibility for the desired roadmap. Issue a concise build matrix with scope, test IDs, owners, risk and PR order. Do NOT stop after writing the matrix.

### Phase 1: Release safety and recovery — independent of design
- Restore security confidence around already-rotated staging DB credential; do not rotate again unless evidence says necessary.
- Handle any other **previously exposed separate-project credential** before external real-data beta, coordinating dependent services and keeping production isolated. Do not print its value.
- Inspect draft PR #46. Complete a real read-only staging DB/Auth-data export, authenticated encryption, private Google Drive copy and download/checksum verification; conduct a **real isolated PG17+pgvector restore**, verify row counts/schema/RLS/roles and record any Supabase-managed Auth/Storage gaps. Supabase Storage objects were previously zero, but recheck live at execution time. Store encryption passphrase away from Google Drive and repo. No success based solely on synthetic tests.
- Review Cloudflare security-audit-skill's **six-phase coverage + independent validation** methodology; audit authorization, tenant isolation, recording URL leaks, booking abuse, OAuth tokens, MCP rights, prompt-injection and lifecycle. Prove with two actual synthetic staging users. No zero-vulnerability or "perfect security" claims.
- Fix current E2E target (draft PR #45) without disabling Vercel preview protection, and configure protected-browser automation securely. Run hosted authenticated tests, not skipped mocks.

### Phase 2: Make UI/UX dramatically simpler (functional, not cosmetic)
- Use `03_UI_UX_INFORMATION_ARCHITECTURE.md` and `12_UI_COPY_WIREFRAMES.md` as acceptance specs. If the existing signed-in redesign differs from deployed UI, reproduce the correct source and deploy to verified staging preview; do not trust documentation-only screenshots.
- Prefer calm, modern SaaS readability, light default with optional dark, generous whitespace, one clear primary action per page, progressive disclosure, no giant KPI wall or techno-jargon. Maintain consistency across Home, People, Meetings, Work, Ask, Capture, Calendar, Settings and account surfaces.
- Generate and maintain a **single actual design system** with tokens/components and page deviations. Apply principles from reviewed UI UX Pro Max; test comprehension with 3–5 unfamiliar users. Dribbble references are inspiration, not templates to copy.
- Meet WCAG 2.2 AA targeted checks, keyboard navigation, focus, screen-reader labels, touch ergonomics, loading/empty/error states, 320px mobile, 768px tablet and desktop layouts.
- Ensure old and new routes migrate gently: safe redirects or hiding legacy routes without destroying data. Test all authenticated navigation paths.

### Phase 3: Deliver verified core V1
- Inspect and reuse existing meeting upload, playback, transcription, corrections and intelligence endpoints. Add accessible, **owner-authorized original-audio download**, with correct MIME/filename, streaming/short TTL and existing retention. Do not increase retention without a decision.
- Make commitments and relationship changes evidence-linked and explicitly confirmed by the user. Show sources at the exact transcript timestamp and maintain edit/audit history. Do not hallucinate memories, dates or people.
- Implement usable pre-meeting briefs (prior interactions, promises and recent context), cross-meeting questions with citations, 3 reusable templates (founder meeting, client call, user interview).
- Build scheduling module coherently under `Meetings > Schedule`: time zone safe availability, booking type, shareable booking link, conflict prevention, confirmation, reschedule/cancel, reminder preferences, export/ICS and optional scoped calendar connection. If provider sync or reminders cannot be securely verified on free budget, provide an explicit manual/ICS fallback and leave automations disabled.
- Design (and possibly implement behind flags) team scheduling, AI natural-language scheduling, automatic conferencing bots, live coaching, multi-step AI Skills, payment checkout and other premium features. **They are part of the V1 architecture but not pilot-accepted merely by code presence**. Do not force them into the public UI until fully tested, compliant and valuable.
- Keep source context as the product: People, Meetings, Work, Ask and user-controlled Memory with MCP access under least privilege and consent. Audit all write paths for RLS/owner authorization.

### Phase 4: Verify all important journeys against actual staging
- Run unit, API/integration (PG17), security, web component, accessibility and Playwright E2E tests. Use two distinct synthetic users A and B with negative cross-tenant reads, edits, recordings, booking links, search, exports and MCP access; verify no auth state leaked into CI artifacts.
- Exercise actual microphone/file input and mobile signed-in experience. Measure source-claim accuracy on a hand-labeled synthetic benchmark and enforce abstention when evidence is missing.
- Record screenshots as **actual browser output**, with deployment URL/SHA and timestamp; no invented screenshots. Confirm the correct UI renders after login on target deployment.
- Test user consent, delete/export, withdrawal, data retention, auth and integration revoke, calendar edge cases, reminders/retries/double-booking, spam protection, load/sleep recovery, cost and rate limits.
- Re-run tests after each fix; keep all test output evidence linked to PR SHA.

### Phase 5: Launch operations + pilot evidence
- Verify hosting and AI terms BEFORE inviting real external users: Vercel Hobby personal/noncommercial restriction and Gemini free-tier provider-training implications must not be ignored. If current hosting/AI settings are not suitable, report beta NO-GO and propose the cheapest compliant alternate path; never silently make new paid resources.
- Set invite-only access, billing off, limited data exposure, usage quotas, failure monitoring, support contact, privacy/consent, backups and rollback procedure.
- 7-day founder synthetic/non-sensitive dogfood; only after gates pass begin 5–10-user private beta with consent and a clear limitation notice.
- Create privacy-respecting pilot analytics, structured interviews, consented testimonials and accelerator evidence index as in `09_PILOT_GTM_EVIDENCE.md`. **Never fabricate users, traction, quotations, test results, funding or certifications.**

## Per-feature implementation contract
For each module: write user journey; confirm whether already coded; implement only missing delta; validate auth+RLS boundaries; write automated tests; verify hosted user flow; test empty/error/loading/mobile/a11y; document rollback, privacy/cost; add evidence to PR and issue #32. No large PR hiding unfinished features.

## Mandatory release gates (fail closed)
**Founder synthetic dogfood:** core staging stable, login and basic navigation functional, no exposed secrets or uncontrolled external writes.  
**5–10 real-user beta:** independently restorable encrypted backup; real A/B tenant isolation; hosted E2E critical path; correct signed-in UI; consent, lawful provider terms, privacy/export/deletion; monitored failures; known limitations; AI restrictions compliant.  
**20–100-user beta:** 5–10-user usability/retention evidence, operational alerts, capacity and costs; safe restore drills; no unresolved critical vulnerabilities; compatible hosting tier.  
**Commercial:** funded sustainable hosting, appropriate provider contracts, managed backup/restore, billing, payments/refunds/tax review and support/reliability policies.

## Operational rules
- Use existing GitHub/Supabase/Render/Vercel connections and native tooling. Never use unrelated accounts or production as a test target.
- NEVER print, store in messages, commit, upload to public artifacts or reveal DB passwords, Supabase keys, Google Drive tokens, passphrases, Auth state, meeting content or personal data.
- No unauthorized access or reverse engineering of competitor systems. REA may be used to inspect our own binaries/UI and publicly documented behaviors only with legitimate permission.
- Treat code pulled from external skills/repositories as untrusted; inspect, pin and approve setup. Respect original licensing.
- No paid services, public deployment, real bulk emails, automated outreach or irreversible actions without founder authorization.
- Do not claim 'production ready', 'secure', 'fully tested', 'all features' or 'zero cost' without evidence.
- If blocked by a private credential or account authorization, give **ONE precise action**. Continue independent engineering tasks without pausing the entire workstream.
- Work through stages in this same thread; make durable commits/PRs and `11_EXECUTION_BACKLOG_AND_HANDOFF.md` checkpoints to avoid losing context if the agent session changes.

## Required output
1. Current truth matrix with file paths, deployment SHA and tests.
2. A calm unified V1 UI and routes that work after sign-in; desktop and mobile screenshots from the live staging application.
3. Implemented feature PRs and reviewed migration plan; enabled vs flagged features clearly documented.
4. Encrypted Google Drive backup plus independently verified restoration proof.
5. Cloudflare-style confirmed/needs-validation/rejected security findings and A/B evidence.
6. Passing hosted E2E with unskipped critical journeys; costs and provider constraints.
7. Pilot onboarding, analytics, feedback and accelerator evidence templates.
8. Updated issue #32 and final **GO/NO-GO separately** for synthetic dogfood, 5–10 real users, 20–100 beta and commercial release.

**Do not stop after planning. Execute the next safe action and make concrete progress.**
