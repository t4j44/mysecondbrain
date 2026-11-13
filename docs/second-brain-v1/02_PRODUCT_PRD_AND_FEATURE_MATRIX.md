# V1 Product Requirements Document and Feature Matrix
**Status:** Proposed product contract; verify actual implementation from code and hosted tests. **Not a claim that all features exist.**

## 1. Product thesis
Second Brain is a permissioned, source-backed personal context workspace for people who repeatedly lose track of conversations, relationships, promises and follow-ups. Meeting recording, booking, files, CRM, AI Ask and integrations are **ways to capture or use context**, not independent apps that force users into separate experiences.

> North-star outcome: user asks "What did I promise Sarah, what changed, and what should I do next?" and gets a correct, source-linked answer with an optional action they confirm.

## 2. Initial customer and urgent job
- **Primary:** solo founders, consultants, recruiters, small-agency owners, lawyers or other professionals conducting ~3+ meaningful conversations/week and losing commitments across tools. Different professional risk levels warrant different data policies; no confidential law/client data on a free AI tier where prohibited.
- **Secondary:** researchers, creators, job seekers and executives with complex relationship networks.
- **Avoid:** 'everyone' as a single acquisition segment. Product can be accessible to anyone, but launch/marketing should target one measurable use case.
- **Current alternatives:** Notion, CRM, calendar, Fireflies, Otter-like recorders, Timetics/Calendly, ChatGPT memory, personal notes. Users switch only if context is more accurate, unified and actionable with less work.

## 3. First-time success journey
1. Invite/access → one-sentence value → optional 30-second demo → consent/privacy.
2. Choose one path: "Add a person", "Capture a thought", "Record/upload meeting" or "Ask something".
3. Source information stored under the user's account with clear source type and date.
4. AI suggests structured outputs with linked original evidence; user can verify/edit/reject before writing durable memories or commitments.
5. Home highlights one useful next step, follow-up or upcoming meeting; avoids a dashboard of empty charts.
6. User returns before a next meeting, opens a concise brief, confirms a follow-up and gets a reliable sourced answer.
7. Optional: booking link reduces scheduling effort; scheduling remains a module inside Meetings.

## 4. V1 feature map
Key: **Existing code** means located in repo; **not hosted-accepted** means real-user flow unproven. **P0** release-critical, **P1** first expansion, **P2** advanced. Re-evaluate after current git/QA inspection.

| Capability | Baseline (repo evidence, subject to retest) | P0 pilot | P1 / P2 roadmap |
|---|---|---|---|
| Auth, account, invite-only | Auth, privacy drafts, invite-only work merged in prior PRs | Signed-in hosted acceptance, consent, export/delete | SSO/orgs later |
| Home dashboard | `apps/web/app/(dashboard)/dashboard` exists | Clear Today/Next/Recent, empty states | Personalized brief |
| People/Relationships | Pages + relationship services exist | Person CRUD, interactions, confirmed commitments, source timeline | Enrichment and graph exploration |
| Capture | Capture page/services, file/photos foundation | 1-click text/file/photo/voice; recovery/error UX | Cross-app capture agents |
| Memory/Ask | memory, indexing, Ask and source services exist | Correctable source-backed recall, hard abstention | Advanced multi-source synthesis |
| Meetings | `capture-panel.tsx`, `meeting_audio.py`, transcription and intelligence | Hosted record/upload/consent, review, speaker corrections | Conferencing bots/live coaching |
| Audio playback | GET `/meetings/{id}/recording` and meeting player code | Owner-only playback verified | Clips/sharing |
| Original audio download | No clear meeting UI download action in audited main | **Implement**, test MIME, expiry, unauthorized denial | Batch export |
| Action/decision extraction | Existing meeting intelligence, output review, source segments | Cite timestamp, confirm before writing to People/Work | Domain-specific AI Skills |
| Meeting preparation | Existing preparation service/component | Display previous discussions, promises and sources | Agenda suggestions |
| Cross-meeting Ask | Retrieval architecture exists; efficacy unproven | Ground claims across meetings + individual source timestamps | Relationship-aware long-range reasoning |
| Reusable AI skills | Extraction schema foundation | 3 reviewed templates: founder, client, user research | Extensible skills registry |
| Calendar + booking | Calendar/integration groundwork unverified | Verify connect; minimal invite scheduling/ICS only if secure | Two-way sync, booking rules, round robin |
| Timetics-style public booking | No verified complete module | Scoped single-host link if ready; feature-flag else | Team, embeds, service sales |
| Reminders/notifications | Commitment outbox and callbacks in backend | Proven in-app reminders/manual export; limit outbound | Email/SMS automation with retries |
| AI scheduling agent | Not verified | Architecture + feature flag, **not advertised** | Natural-language scheduling with confirmation |
| Meeting bots/live assistant | Not verified | Explicitly off | Consent-based joiner, live assistance |
| MCP & integrations | Existing MCP tokens/permissions | Revoke/authorize/auth boundary acceptance | More clients/providers |
| Analytics/support | Mixed implementation | Minimal privacy-first events, support contact, error alerts | Commercial billing and team analytics |
| Opportunity Scout | GitHub issue #33 planned | Off | Opt-in weekly context intelligence |

## 5. P0 acceptance criteria (product)
**Person:** create a record with a name and at least one contextual note; edit, search, link a meeting, inspect source, delete; unrelated account cannot find it.  
**Meeting:** permissions + privacy consent before recording; upload or capture; show status and graceful failure; correct transcript and speakers; find source segments; download original within retention; past expiry = clear message, not broken link.  
**Commitment:** suggestion never silently becomes fact; user sees exact quote/source, owner, due date, status; can confirm/edit/reject; subsequent Ask and Home read the canonical confirmed record.  
**Ask:** grounded answer linking to actual source and timestamps; cross-meeting recall; distinct "not enough evidence" response; correction flows persisted.  
**Scheduling pilot if enabled:** create a booking type + timezone-aware public link; prevent conflicts atomically; revoke link; reschedule/cancel; no public access to private person context.  
**Trust:** export, delete, revoke integration, privacy notice and known limitations all findable via Settings.

## 6. Explicit out-of-scope for first invited beta (unless accepted separately)
- Paid bookings / payment collection; commercial subscriptions; public self-serve signup.
- Always-on bots joining calls without consent; covert recording or transcription.
- Automatic emailing, rescheduling, CRM writes or cross-app changes without review.
- Advanced multi-tenant teams, white-label builder, complex payment pages.
- Guaranteed 100% AI extraction or "perfect security" assertions.
- Non-essential agent marketplaces, social scraping, Opportunity Scout and broad autonomous actions.

## 7. Core metrics & success hypothesis
- Activation = a user saves one meaningful person/note **and** completes one sourced retrieval or confirms a meeting-derived action within first 7 days.
- Weekly return = user with substantive view/capture/Ask/commitment action, not merely login.
- Suggested directional targets: >=70% activation and >=50% week-two return among first 5–10 users; zero confirmed cross-tenant leaks; >=90% core E2E pass on verified staging; measured AI citation correctness with manual gold data.
- Interview each dropout. Ask what they use instead and whether they would pay; "they loved the UI" is not adequate evidence.
- Technical learning before metrics: use only synthetic/non-sensitive test data until processing/hosting terms support valuable personal user content.

## 8. No-code/manual validation before adding advanced AI
- Give 5 founders a one-page meeting brief manually after an approved interview.
- Ask them to confirm which commitments are correct; measure review time and follow-up utility.
- Offer a manual scheduling link (existing free scheduling provider or calendar invite) to see if calendar feature is urgent.
- Only automate the workflow after repeated demand is observed. Keep raw evidence separate from marketing testimonials.

## 9. Scope decision rules
Prioritize by `frequency × pain × privacy safety × evidence of switching`, not number of features. For each proposed feature document: user, trigger, current alternative, why switch, observable metric, $/user variable cost, security risk, manual alternative, integration dependency and kill condition. **Feature complete** requires deployed/authenticated acceptance, not just code merged.
