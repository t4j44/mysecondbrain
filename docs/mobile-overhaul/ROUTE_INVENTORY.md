# Route coverage inventory

Generated from all 40 current page.tsx files. Shared-shell improvements apply to dashboard routes, but shared layout/build success does not establish each route's complete functional acceptance. No untested route is marked PASS.

| Route | Actual evidence boundary |
| --- | --- |
| `/` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/achievements` | Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED |
| `/assistant` | 18-profile synthetic matrix; real staging primary flows at 320/390px; protected Home/Ask/source verified after approved exact-origin CORS change. See EVIDENCE.json. |
| `/capture` | 18-profile synthetic matrix; real staging primary flows at 320/390px; protected Home/Ask/source verified after approved exact-origin CORS change. See EVIDENCE.json. |
| `/content` | Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED |
| `/dashboard` | 18-profile synthetic matrix; real staging primary flows at 320/390px; protected Home/Ask/source verified after approved exact-origin CORS change. See EVIDENCE.json. |
| `/documents` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/forgot-password` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/ideas` | Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED |
| `/kpis` | Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED |
| `/login` | 54 real Next.js public-auth tests across 18 profiles; authenticated protected-preview login at 390px; Lighthouse before/after |
| `/meetings/[meetingId]` | Existing meeting-component CI at 3 widths; hosted audio/provider/complete route lifecycle NOT VERIFIED |
| `/meetings` | Existing meeting-component CI at 3 widths; hosted audio/provider/complete route lifecycle NOT VERIFIED |
| `/memories/new` | Synthetic create/edit/source persistence tests; real hosted contact results recorded separately |
| `/memories` | Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED |
| `/oauth/consent` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/organizations` | Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED |
| `/p/[token]` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/people/[personId]/edit` | Synthetic create/edit/source persistence tests; real hosted contact results recorded separately |
| `/people/[personId]` | Synthetic create/edit/source persistence tests; real hosted contact results recorded separately |
| `/people/new` | Synthetic create/edit/source persistence tests; real hosted contact results recorded separately |
| `/people` | 18-profile synthetic matrix; real staging primary flows at 320/390px; protected Home/Ask/source verified after approved exact-origin CORS change. See EVIDENCE.json. |
| `/portfolio` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/projects` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/reset-password` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/ai-access` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/appearance` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/export` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/integrations/google/callback` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/integrations` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/privacy` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings/profile` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/settings` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/signup` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/sources/[kind]/[id]` | Synthetic create/edit/source persistence tests; real hosted contact results recorded separately |
| `/tasks` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/ventures` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/verify` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/work/commitments` | Source/build only; full route-specific mobile behavior NOT VERIFIED |
| `/work` | 18-profile synthetic matrix; real staging primary flows at 320/390px; protected Home/Ask/source verified after approved exact-origin CORS change. See EVIDENCE.json. |
