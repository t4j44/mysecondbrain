# Pilot Program, Metrics, Feedback, Testimonials and Accelerator Evidence
## Principle
Engineering completion is **not** product-market fit. The initial pilot must prove the actual outcome, not the number of features, AI agents, models or frameworks. Founder/cofounder/accelerator narrative is grounded in real user behavior and source-backed evidence.

## 1. Recruitment cohort
**Target:** 5–10 carefully selected founders, consultants, recruiters or relationship-heavy professionals who hold at least ~3 consequential meetings/week; no regulated/confidential client data on AI/hosting terms that don't support it. Avoid only recruiting friends who will say nice things.
- Find candidates via personal founder/community network, universities/incubators and referrals. Ask for a concrete example of a forgotten commitment and current tools first.
- Start with 2 friendly synthetic/non-sensitive testers, then 5–10 after technical beta gates. Expand to 20–100 only if quality and retention hold.
- Invitation states: experimental product, data policy, expected limitations, recording consent, support/withdrawal and how to delete/export.

## 2. Timeline and checkpoints (not a promised delivery date)
**Preparation:** G2 security/recovery/hosting/privacy accepted.  
**Founder dogfood:** 7 days with synthetic/non-sensitive data, record obstacles and time per task.  
**Early external cohort:** 14-day observation with 5–10 opted-in users; baseline interview day 0, activation day 1–3, check-in day 7, return and WTP day 14.  
**Expansion decision:** stop, iterate or broaden based on observed blockers and value, not campaign hype.

## 3. Pilot tasks
1. Record/upload permitted fictional meeting or note and correct transcript/summary.
2. Confirm an extracted commitment, link person and source evidence.
3. Ask a real question about their source-backed information and inspect citations.
4. Prepare for a next conversation; confirm whether suggestions were useful.
5. If scheduling enabled, share booking link and reschedule across two timezones.
6. Export a copy of their own information and find account deletion/help.

## 4. Analytics and privacy contract
Event names, not raw content:
- `invite_accepted`, `onboarding_completed`
- `capture_started`, `capture_saved`, `capture_failed`
- `person_created`, `meeting_uploaded`, `meeting_processed`, `meeting_reviewed`
- `recording_downloaded`, `commitment_confirmed`, `commitment_completed`
- `ask_question`, `ask_citation_opened`, `ask_abstained`, `ask_feedback_positive/negative`
- `booking_created`, `booking_rescheduled`, `booking_cancelled` (only if feature enabled)
- `export_requested`, `account_deleted`, `integration_revoked`
- `error_bucket`, `ai_tokens_spent`, `worker_seconds_spent` (aggregate and scoped)

Event metadata: pseudonymous user key, coarse timestamp, feature, success/failure, latency, generic error code, model/processing tier and estimated marginal cost. **Do not record** phone, email, transcript, freeform Ask content, audio or access tokens into analytics. Publish a short consent/notice.

## 5. Measurable success criteria
- **Activation:** >=70% of 5–10 invited users save meaningful input and complete one grounded retrieval or confirmed follow-up in week one (directional threshold, small sample).
- **Week-two return:** >=50% of activated users actively use Second Brain in week two (meaningful interaction, not merely login).
- **Grounded accuracy:** manually score answers against source for 20–30 synthetic queries; log unsupported claim count and misattributed commitments; source citations must resolve to exact text/timestamp.
- **Time saved:** pre/post time to recall promise or prepare meeting; use actual measured tasks, not vague self-report alone. Show sample size and uncertainty.
- **Willingness to pay:** at least 3 specific price/intent conversations with people who actually used the product, not hypothetical survey yeses. Price hypotheses $5–15/mo require experiments, not assumption.
- **Security:** zero confirmed cross-user exposure, successful independent recovery demonstration and no unresolved critical/high issues in pilot release.

## 6. Interview scripts
**Baseline (day 0):** Tell me about the last time you forgot a commitment. What was the consequence? What did you do to recover it? Which apps do you currently rely on? How often does this happen? Are you permitted to upload such content?  
**Day 3:** What task did you try? Where did you get stuck? Did you trust the source? What surprised or worried you?  
**Day 7:** Walk me through the last useful answer and one wrong answer. Did you correct it? Was saving the data worth the effort?  
**Day 14:** What did you use instead when you didn't open Second Brain? What would you miss if it disappeared? What would you pay, and what proof would you need before uploading important data?

## 7. Feedback taxonomy
Categorize each user report: onboarding, comprehension, navigation, source accuracy, meeting privacy, upload/recording stability, permissions, scheduling, AI latency, billing concern, trust, retention, alternative competitor, explicit willingness to pay. Attach severity, reproducible journey, version, consent and resolution; redact personal details in shared accelerators.

## 8. Testimonials and evidence ethics
- Ask for testimonial only after observed value. Separate permission for publishing exact quote, name, photo, company and specific channel.
- Preserve original wording, timestamp, approval and withdrawal status; anonymous quotes permitted if explicitly consented.
- Never claim testimonial from a fictional test user, AI-generated copy or unconsented recording.
- Archive original feedback privately; share only de-identified aggregate results unless explicit consent.

## 9. Private Google Drive folder layout
```
SecondBrain_Pilot_Evidence/       (NOT same as encrypted database backups)
  00_Readiness/                    sanitized issue #32 release summaries, staging test references
  01_Research_Baseline/            consented baseline interview records
  02_Weekly_Metrics/              aggregate CSV / Google Sheets snapshots
  03_Usability/                   sanitized UI task observations/screenshots
  04_Feedback/                    redacted survey/interview themes
  05_Testimonials_Consented/      exact approved quotes and permission records
  06_Accelerator/                 pitch, problem, demo, milestones, cost model
```
Founder-controlled ACLs, minimized retention, no raw database dumps or encryption passphrase in evidence folder. Backups live in a separate restricted recovery folder.

## 10. Accelerator evidence one-pager
**Problem:** context loss across conversations and tools.  
**Who:** narrowly defined relationship-heavy early users.  
**Solution:** source-backed, user-confirmed memory of promises and relationships.  
**Why now:** increased AI assistant usage and meeting capture create more fragmented data (support with current credible sources before public claim).  
**What exists:** verified deployed flows and source code, NOT untested features.  
**Traction:** invite→active users, week-two retained, frequency, time saved, cited answers, testimonial consent.  
**Defensibility hypothesis:** permissioned cross-source context + corrected history + workflow integration; not simply MCP + transcription.  
**Cost:** measured AI spend/user, storage/meeting minutes, running limitations.  
**Ask:** specific user intros, cofounder skills, compute credits or pilot partners.  
**Risks:** source accuracy, user trust, data portability, providers/hosting terms, switching cost, competitor substitution.

## 11. Go-to-market sequence
- Weeks before validated beta: educational demos with fully fictional data, founder interviews and waitlist; no marketing claims of general availability.
- After 5–10 cohort: publish anonymized problem/insight findings and consented testimonials, short walkthroughs and targeted founder community outreach.
- After 20–100 evidence: investigate accelerators and technical cofounder based on traction and the highest recurring execution bottleneck. Don't split equity merely for passport or geography.
- Upgrade hosting and professional privacy/cost controls before paid/commercial user scaling.
