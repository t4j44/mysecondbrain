# $0-Incremental Pilot Stack, Provider Eligibility and Operating Plan
## 1. What $0 means
The user requests **zero additional infrastructure spending during pilot preparation**. This means reuse existing eligible free tools and already-granted credits **only when authorized and provider terms permit the usage**. It does NOT mean a 24/7 commercial service with guaranteed uptime, privacy or unlimited AI at no cost.

| Layer | Current proposed provider | Limitation / gate |
|---|---|---|
| Web UI | Existing Vercel preview | Hobby is limited to personal/non-commercial use; real startup beta may require compliant alternative/tier |
| API/worker | Render staging | Free instance sleeps, constrained CPU/memory, not production-grade guarantee |
| DB/Auth/objects | Supabase Free staging | Limits, project pausing, no assumed managed daily backup, RLS and storage quotas |
| AI | Existing Gemini API integration | Free-tier submitted content may be used to improve provider products; do not send confidential real-user data absent appropriate terms |
| CI & code | GitHub / Actions | CI minute/artifact limits; don't store secrets or real dumps |
| Backup | Owner-private Google Drive | Only encrypted backup; real upload/read-back/restore must be evidenced |
| Calendar / email | Existing permissible provider/ICS | Token scopes, mail quotas, anti-spam and consent; fall back to manual ICS |
| Monitoring | Existing logs + minimal alerts | Must record failures and spending limits; not content |

## 2. Provider terms check before inviting external users
- Vercel Hobby docs: https://vercel.com/docs/plans/hobby explicitly restrict non-commercial/personal use. Determine whether the external beta qualifies; don't simply claim that free Vercel is compliant. A hosting alternative or paid plan is a **decision**, not an automatic purchase.
- Gemini pricing/terms: https://ai.google.dev/gemini-api/docs/pricing, https://ai.google.dev/gemini-api/terms. Free models may use submissions to improve Google's products. Keep AI processing of sensitive user info off until paid-service/data-protection terms or acceptable approved alternative.
- Render Free docs: https://render.com/docs/free; cold starts and performance limits impact availability.
- Supabase plan and quota docs: https://supabase.com/pricing . Verify current features, not old screenshots.
- $2,000 Google Cloud startup credits, if awarded in another startup context, should **not** be assumed transferable to this product. Do not create billing-enabled cloud services without explicit approval.

## 3. Pilot feature flags (recommended)
```
PILOT_INVITE_ONLY=true
ENABLE_PUBLIC_SIGNUP=false
ENABLE_REAL_PAYMENTS=false
ENABLE_AUTOJOIN_MEETING_BOT=false
ENABLE_LIVE_COACHING=false
ENABLE_AI_SCHEDULING_AGENT=false
ENABLE_OPPORTUNITY_SCOUT=false
ENABLE_SOCIAL_AUTOSCRAPE=false
ENABLE_AUTOMATED_EXTERNAL_WRITES=false
ENABLE_CALENDAR_SYNC=false  # until OAuth/security/provider acceptance
ENABLE_BOOKING_LINKS=false  # enable only after guest route + DST/race tests
ENABLE_AI_CONFIDENTIAL_DATA=false  # until processing terms accepted
```
These are proposed semantics; reconcile with actual app configuration, never assume unrecognized env vars work. Mirror server-side checks; a hidden button alone is not a feature flag or security boundary.

## 4. Operations checklist
- Owner contact: one accountable person monitors release issue #32 and staging alerts.
- Test/backup status checked before any schema changes; rollback plan and separately stored encryption key.
- Capture anonymized error rates, unexpected 401/403, job queues and expensive AI requests; redact PII.
- Document minimum support response procedure, data deletion/export flow and known limitations.
- Review rate limits for Ask, uploads, audio processing, guests, booking and MCP.
- Implement quota and per-user safeguards before widening beyond 5–10 users.
- Preserve canonical access logs for incidents without retaining transcripts or tokens in app logs.
- No secret screenshots or credentials in GitHub issues, PRs or chats.

## 5. Founder’s four-step execution
1. Let Astra implement/review the work in `docs/second-brain-v1/` through small PRs, evidence and feature flags.
2. Provide private owner actions only if unavoidable (credential setup, scoped OAuth, account eligibility); do not share values in chat.
3. Personally verify the simple signed-in UX on real desktop + phone and do 7-day dogfood with fictional or non-sensitive records.
4. Invite 5–10 real users only after G2 signed-off; record interviews and aggregate usage evidence for a cofounder or accelerator.

## 6. When to upgrade
Upgrade to paid/compliant infrastructure when any of the following occurs: provider terms don't permit intended external activity; confidential AI processing needs paid data terms; cold starts cause missed user sessions; quotas/storage exceed margins; backups/restores need managed reliability; user count/paid revenue warrants uptime expectations. Budget based on observed per-user audio minutes, storage and AI tokens, not generic estimates.

## 7. Launch state statements
**Allowed now if true:** "Private development preview; limited synthetic/non-sensitive testing."  
**Only after G2:** "Invite-only beta; explicit privacy limitations and supported use cases."  
**Only after G4:** "Public commercial launch" with sustainable hosting, lawful billing, privacy, support, backup and incident readiness. Never imply SOC 2, HIPAA or GDPR certification merely by copying another tool's patterns.
