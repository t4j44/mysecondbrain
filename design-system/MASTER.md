# Second Brain V1 design system

Implemented source: `apps/web/app/globals.css`, `components/ui/*`, `components/layout/*`, `lib/navigation.ts`. These files own the tokens and behavior; this document records their intent and acceptance limits.

## Shared rules

- Five primary destinations on desktop and mobile: Home, People, Meetings, Work, Ask. Preserve existing route URLs and ownership checks.
- Capture and Search stay in the header at 320px. The mobile More drawer holds secondary destinations. Desktop secondary tools are separate from the five primary destinations.
- Light default: near-white canvas, white cards, dark slate text, deep teal primary action. Dark theme uses slate surfaces and lighter teal. Use semantic CSS variables, not new page-specific palettes.
- Body/input text uses the existing sans-serif stack; inputs are at least 16px. Main controls and navigation have at least 44px targets. Cards use 16px mobile padding and 24px where space permits. Shared radius is 12px.
- Blue focus outlines are distinct from selected teal states. Dialogs trap focus, close on Escape and return focus to the trigger. Keep the skip link and landmarks.
- Explain empty, loading, unavailable and retry states with text. Color alone never conveys a decision. Preserve multilingual source text and wrapping.
- Search submits explicitly to the existing authenticated search endpoint; keystrokes filter page destinations locally. Saved results link to source records or transcript segments. No generated answer is fabricated from a failed search.
- Original audio is separate from AI outputs. Show retention and unavailable states; download preserves original MIME and bytes. Review remains explicit before saving proposed facts.

## Page decisions and remaining deviations

| Surface | Current behavior | Remaining acceptance |
|---|---|---|
| Home | Today, one capture action, onboarding and follow-ups | Populated signed-in staging and unfamiliar-user comprehension |
| People | Existing list/detail/timeline; shared shell and tokens | Real corrections and cross-user denied access |
| Meetings | Existing upload/review; new original recording controls in separate change | Hosted playback/download and physical microphone |
| Work | Existing commitment/project routes retained | Hosted source-linked completion and conflict recovery |
| Ask | Existing conversation/source UI retained | Hosted evidence quality, abstention and two-user history |
| Capture | Existing recorder/file/note flow; global entry | Physical device and provider acceptance |
| Secondary tools | Files & sources, Projects, Integrations, Settings, Privacy | Legacy screens retain denser content; no claim of completed redesign |

## Evidence and boundaries

2026-11-13: 21 synthetic browser checks passed across Chromium 320/390/1440, six core pages and dialog keyboard behavior. The fixture includes automated WCAG-tagged checks at 390px. Screenshots in `docs/second-brain-v1/evidence/` are rendered local fixtures, clearly labeled, not authenticated staging proof. Tablet/WebKit, dark-theme coverage and human comprehension are recorded separately when run. No claim of WCAG certification or physical-device acceptance.

Reviewed inspiration: UI UX Pro Max guidance, Fireflies meeting evidence patterns and Timetics scheduling workflows. Existing product components are reused; no competitor assets, code or branding copied.
