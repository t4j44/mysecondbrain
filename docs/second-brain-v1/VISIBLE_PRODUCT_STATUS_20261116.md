# What is built, and what the founder can actually open

## Verified mismatch

The founder is signed in at `https://second-brain-web-staging-seven.vercel.app/dashboard`. Read-only Vercel lookup resolves this to deployment `dpl_Xg3JMM8uuaDzoPzjYhBBgTT2yfF4`, commit `c94c63219d4699901a637b4843f6fae4068915ff`, branch `codex/second-brain-release-hardening`. The project is the existing staging project, although this alias is its Vercel **production target**. It is not the current V1 review candidate.

The earlier agent login checks used a different protected branch alias, serving `2ec0928`. Those checks did not establish whether the founder was signed in at the URL they actually used. Native Chrome inspection now confirms the signed-in Home, missing Meetings navigation and old onboarding. Home loaded during that inspection; the earlier screenshot's service error was not reproduced or diagnosed. Do not call it fixed.

The light purple Connections/Promises screenshots supplied by the founder were local component/browser evidence from earlier work, not deployed acceptance. The newer teal screenshots here are also **local synthetic browser renders**, explicitly not hosted proof. The work exists, but the delivery gap is real.

## Feature map

| Feature | Current candidate source | Delivery status |
|---|---|---|
| Home, People, Meetings, Work, Ask; global Capture/Search | `apps/web/lib/navigation.ts`, `components/layout/*` | Implemented; founder's current alias still has old navigation |
| Direct note/meeting/person choices on Home | `app/(dashboard)/dashboard/page.tsx` | This change; local browser verified, not deployed |
| Recording/upload, review, transcript/source controls | `app/(dashboard)/meetings/*`, `components/meetings/*` | Reused existing implementation; hosted candidate/provider acceptance outstanding |
| Owner-only original audio download | `app/api/v1/endpoints/meeting_intelligence.py`, `app/services/meeting_outputs.py` under `apps/api` | PR #49; API/byte/auth tests pass; hosted original download unverified |
| Founder/client/interview templates | `apps/api/app/services/meeting_templates.py`, `apps/web/components/meetings/meeting-outputs.tsx` | PR #52; local evidence/interaction tests pass; not accepted on current hosted candidate |
| Manual calendar draft | `apps/web/app/(dashboard)/meetings/schedule/page.tsx`, `apps/api/app/services/calendar_drafts.py` | PR #54; local calendar/download tests pass; no booking, availability reservation, invitation sending, sync or reminders |
| Promises and Telegram controls shown in earlier screenshots | `apps/web/components/relationships/commitment-card.tsx`, `components/settings/telegram-connection.tsx`, `telegram-reminders.tsx` | Source preserved; provider operations remain gated, not promised live |
| Full booking links, conflict prevention, reschedule/cancel, automatic calendar workflows | See specification acceptance B1–B7 | Not delivered as a working hosted booking system |

## This UI correction

- Home offers three direct actions without requiring a contact-first sequence. Meeting capture remains reachable when saved-context loading fails.
- Five primary destinations remain visible. Desktop secondary tools use More; the mobile More drawer starts expanded. Collapsed desktop tools retain labeled icons.
- The phone header fits a normal 320px viewport in one row; enlarged text can still wrap and scroll.
- Calendar copy is shorter while retaining manual/unsaved/no-reminders limits.
- The synthetic full-shell route now resolves `/meetings/schedule` correctly rather than treating `schedule` as a meeting ID. Tests navigate Home → capture consent → Schedule → Meetings, including a failing Home request.

Actual renders: `evidence/home-desktop-20261116-synthetic.png`, `meetings-desktop-20261116-synthetic.png`, `home-mobile-20261116-synthetic.png`. Fictional account/data; no real account content or credentials copied.

## Concrete staging delivery boundary

Latest read-only Render observation: staging API service `srv-dbbjrp4s728c738mhsj0`, free plan, automatic deployment off; live source `7a986638850e5ff5e22742ec4be4d2be5e0f3273`. Comparing that source with this candidate shows **no Supabase migration or API model changes**. The API delta adds recording/template/calendar behavior and dependency fixes. A schema migration is not part of this proposed update.

Vercel project `prj_r27R5j3Oss8GpNlHLZO58h0MA2uJ` has preview SSO protection enabled. A prospective private review should use one explicitly verified protected preview URL and a matched API version. Preserve exact-origin CORS; if a new origin is required, add only that verified origin and retain existing ones. Do not expose a wildcard bypass.

Proposed scoped update, subject to owner approval because the owner previously requested unchanged staging: deploy the reviewed API commit to the existing free staging service; create a protected web preview of the same commit in the existing staging project; verify live revisions, protection, sign-in, navigation and synthetic critical journeys. No database migration, credential rotation, public promotion, billing, provider sends or external invitations. Retain the previous web deployment and API commit for rollback. Do not repoint the founder's public-looking `seven` alias silently.

Real backup/restore, two-user isolation and legacy credential remediation remain external-pilot release gates. Their unresolved status does not itself imply that a reviewed, schema-free private UI update is technically impossible. Private deployment permission and hosted compatibility still have to be established.
