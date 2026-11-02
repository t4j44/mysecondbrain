# V2 Full-Experience Recovery — November 2, 2026

## Goal
Recover and preview the entire updated Second Brain experience—UI, UX and existing shipped features—without replacing the current application or claiming unbuilt features are live.

## Verified baseline
- Latest GitHub `main`: `35837bf0f353c8ee72a4bd876ef83c81d084b3da`.
- Public-facing staging alias `second-brain-web-staging-seven.vercel.app` still targets October 22 commit `c94c63219d4699901a637b4843f6fae4068915ff`.
- Later V2 branches for navigation/capture, meetings, Telegram foundation, English-first and profile corrections are ancestors of `main`; do not blindly cherry-pick them.
- Original UI PR #13 differs from `main` but diverged 11 commits ahead / 76 behind. Its original content is available for reference, but wholesale merging would risk regression.
- `apps/web/vercel.json` explicitly disables automatic builds on `main` and `codex/second-brain-release-hardening`.
- Current launch tracker #32 remains NO-GO for public/paid release.

## Preserve and verify
1. Maintain all V2 canonical data workflows: People, commitments, meetings, meeting review/correction, projects, documents, Ask/MCP, settings and privacy.
2. Preserve light/dark themes and mobile bottom nav (Home, People, Capture, Meetings, More) and desktop navigation (Home, People, Meetings, Capture, Ask, Work, Documents).
3. Compare all 8 files in design PR #13 against today's `main`, cherry-pick only non-regressive UI improvements with targeted unit and mobile tests.
4. Build a protected preview from this branch rather than publishing or changing a domain.
5. Verify 320/390/1440 CSS px, keyboard and safe areas; page readiness and core journeys with synthetic accounts.
6. Document which integrations are functional versus intentionally disabled: live Google sync, Telegram delivery, weekly Opportunity Scout (Crawl4AI/Agent Reach) and billing must not be presented as available until hosted verified.
7. No sensitive test data, paid provisioning, production promotion, release-flag weakening, or bypass of #32.
8. Preserve and separately validate database recovery, authenticated A/B isolation and release acceptance.

## Current evidence
- `main` dashboard source says “Today” and “Capture something”; older live dashboard screenshot says “Home” and “Capture a note.” This is concrete code/build drift.
- Attempting a one-off `main` preview in Vercel was canceled by the project's existing build-skip configuration.
- This branch exists specifically to allow safe preview deployment without changing release-protected branches. It is a recovery checkpoint, not completed UI or test acceptance.

## Acceptance
- Protected preview READY and exact branch SHA confirmed
- Key UI workflows and all feature availability states visually reviewed
- CI tests pass on exact SHA
- Issue #32 gates remain applicable and unmodified
