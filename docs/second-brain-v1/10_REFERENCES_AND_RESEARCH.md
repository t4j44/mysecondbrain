# Reference Research — What to Borrow, What to Avoid
**Research date:** 2026-11-12. Public sources change; verify current docs, licenses and release SHAs before running installer commands.

## A. User-provided references
### 1. UI UX Pro Max Skill
- Repository: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill (GitHub repository currently shows MIT license).
- README describes design-system generation, style/typography/color/UX reasoning rules, Next.js/React/shadcn guidelines, page-specific overrides, and pre-delivery anti-pattern checks.
- **Useful for Second Brain:** create one `design-system/MASTER.md` plus page overrides; drive accessible semantic components and responsive patterns. Audit current design before automatically modifying it.
- **Not useful by itself:** proven usability, IA for the actual product, release testing, security. Skill output is guidance; no magic 'award-winning UI' guarantee.
- Installation is optional and requires reading source/CLI permissions before using it in the coding-agent environment.

### 2. Dribbble repository UI search
- Website: https://dribbble.com/search/repository-ui
- A design gallery, not a code library, usability study, product spec or licensed asset pack.
- **Useful:** spacing, editorial hierarchy, grouping, table/list variations and simple card patterns.
- **Avoid:** copying layouts/graphics/branding, making every view a dense analytics dashboard, ignoring accessibility and mobile because desktop screenshots look attractive. Use inspiration only and validate against real user tasks.

### 3. GitHub UI/UX topic collection
- Website: https://github.com/topics/ui-ux
- Broad discovery category, not an audited recommendation. Avoid installing a collection of random libraries. Prefer the existing Next.js component stack; review any addition for maintenance, license, security and bundle cost.

### 4. REA (Reverse Engineer Anything)
- Repository: https://github.com/morluto/rea (MIT per current GitHub metadata), site https://rea.tools/.
- README describes agent/MCP-assisted investigation of app behavior, JavaScript/Electron/native binaries and runtime evidence. **It is NOT a UI architecture library.**
- **Useful safely:** instrument and analyze our own application to understand a complex old feature, trace broken signed-in screens, produce behavioral evidence and regression test assumptions.
- **Avoid:** invasive analysis of competitors, bypassing access controls, DRM, unlicensed reuse of hidden source or extracting personal data. Not necessary for basic React layout work. Review/pin installations; use ordinary source/Playwright inspection first.

### 5. Cloudflare Security Audit Skill
- Repository: https://github.com/cloudflare/security-audit-skill (MIT per current GitHub metadata).
- README describes six-phase security audit with reconnaissance, coverage-led hunting, candidate validation, machine-readable verified findings, independent record verification and reports.
- **Useful:** architecture coverage ledger, confirmed/needs-validation/rejected finding taxonomy, evidence provenance, focus on app-specific trust boundaries.
- **Not useful by itself:** proof of no vulnerabilities, legal/privacy compliance, independent pen test, production monitoring. Pin/review skill before installation; run authorized scope only.

## B. Competitive reference: Fireflies.ai
- Website: https://fireflies.ai/
- Official site lists recording/transcription, speaker recognition, meeting search with timestamps, AskFred, summaries/action items, AI Skills, MCP, CRM integration and bot/mobile/desktop capture; feature availability varies by plan and date.
- **Second Brain opportunity:** personal context with user-correctable sources, confirmed person/commitment continuity, before/after-meeting usefulness, across assistants.
- **Difference not to overclaim:** Fireflies already has broad integrations and cross-meeting AI; simply 'meeting notes + CRM + MCP' is not unique.

## C. Competitive reference: Timetics.ai
- Website: https://timetics.ai/
- Official site highlights AI scheduling, calendar management, availability and booking rules, configurable pages, reschedule/cancel, reminder/notifications, team scheduling, monetization and integrations.
- **Second Brain opportunity:** make scheduling one input to the existing meeting/person/context flow rather than a separate booking-business platform.
- **Initial scope tradeoff:** solo booking links + timezone + ICS first if real demand; payment/team round-robin, website builder and agentic booking need distinct testing and support, not core pilot blockers.

## D. Standards and service terms
- WCAG 2.2: https://www.w3.org/TR/WCAG22/ ; UX QA targets AA, keyboard navigation, text contrast, non-obscured focus, accessible touch targets.
- Vercel Hobby terms (personal/non-commercial limitation): https://vercel.com/docs/plans/hobby . The current free account plan may not permit external commercial startup beta; verify or change to compliant hosting before such a beta.
- Gemini API pricing/data use: https://ai.google.dev/gemini-api/docs/pricing and https://ai.google.dev/gemini-api/terms . Free tier can use content for product improvement; avoid sensitive/confidential user data absent suitable terms.
- Render service plans: https://render.com/docs/free . Free service sleeping/reliability limitations should be disclosed and load-tested before external invitations.
- Supabase backups: https://supabase.com/docs/guides/platform/backups . Managed backup features depend on plan. `pg_dump` by itself is not complete Supabase Auth/Storage recovery.
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/ ; ASVS-level controls tailored to B2C multi-tenant SaaS.

## E. Repo-derived Second Brain evidence (current default branch snapshot)
- `apps/web/components/meetings/capture-panel.tsx`: consent fields, browser recording, live transcript fallback, private upload, local recovery affordance.
- `apps/web/app/(dashboard)/meetings/[meetingId]/page.tsx`: evidence-linked meeting review and transcript player; download button not located in inspected main.
- `apps/api/app/api/v1/endpoints/meeting_intelligence.py`: owner-scoped endpoint for recording; private storage signed URL or response bytes.
- `apps/api/app/services/meeting_audio.py`: bounded file access and media formats.
- Existing PRs #45/#46 and issue #32 track unresolved hosted E2E and real recovery.
- Repo README describes a broader 'Founder Terminal' product, but descriptions are **not proof that a feature is hosted or accepted**. Update documentation with actually tested V1 behavior.

## F. Research conclusions (recommendations, not source facts)
1. Prioritize **task clarity, identity and trustworthy evidence** over more navigation categories or glossy design.
2. Join Fireflies meeting intelligence + Timetics scheduling around one human relationship and commitment timeline.
3. Use UI UX Pro Max to standardize design; use Dribbble to inform visual judgment; use usability testing as the real quality gate.
4. Use Cloudflare audit process as structured security evidence; do not claim a library makes security perfect.
5. Use REA only where authorized behavioral investigation provides value beyond existing tests.
6. Build backend extensibility for advanced features, but release them only after independent gates. A one-session prompt can coordinate work, **not eliminate the need for multiple reviewed PRs, actual browser tests and human approvals**.

## G. Copyright/source hygiene
- Don't copy Dribbble illustrations, text, screenshots, logos or component design verbatim.
- MIT repositories allow certain code reuse subject to license/notice obligations; copy only necessary code after source review and retain license notices where required. Avoid silently bringing entire skills/CLI into the product runtime.
- Never reverse-engineer a competitor service beyond authorized public/documented use; learn conceptual patterns through permitted observation.
