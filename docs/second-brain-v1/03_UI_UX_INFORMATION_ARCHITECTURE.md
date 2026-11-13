# UI/UX — Information Architecture, Design System and Navigation
## Governing rule
**All powerful features must remain discoverable without making the interface intimidating.** An unfamiliar user should find a person, capture something or ask a question without opening documentation. Design for founders/professionals first, accessible to broader audiences later.

## 1. Primary navigation (fixed)
- **Home** — Today, follow-ups, changed context, recent activity, next useful action.
- **People** — Search, list, person profile, relationship history, verified contextual notes.
- **Meetings** — Upcoming/Done, Record, Upload, Schedule, Booking links, calendar connections nested within Meetings.
- **Work** — Confirmed commitments, next steps, tasks/projects, deadlines, associated people.
- **Ask** — Natural-language questions with source citations and saved searches.
- Global `+ Capture` button and `Search` field accessible from every section; `More` contains Files/Knowledge, Projects, Integrations, Settings, Privacy, Help and less-used legacy capabilities.

**Avoid:** separate primary tabs for Insights, CRM, Calendar, Sources, AI Skills, Chat, Knowledge, Studio, Agents, MCP, Dashboard, Tasks and Capture. These can exist as nested or contextual routes, not dozens of competing destinations.

## 2. Desktop navigation
Top bar: logo + search/shortcut + `+ Capture` + help + profile. Left sidebar: five nav destinations, compact collapsed state. Main panel: primary content in a readable max-width. Right context rail only when it adds a clear task outcome (e.g. Person summary, citations); otherwise full-width.
- One obvious primary action per view.
- Non-primary actions in a single accessible overflow menu.
- Breadcrumbs only on deep paths; back button works.
- Preserve scrolling, selected tab and filters on navigation.
- Use contextual side panels/drawers instead of modal piles.
- Do not cover content with sticky overlays, Chat bubble, or popups.

## 3. Mobile navigation
- Bottom bar with **Home, People, Meetings, Work, Ask**; top `+` Capture entry (or dedicated center action if it does not obscure a destination).
- No horizontal tables unless absolutely necessary. Cards and detail accordions instead.
- Avoid mixing bottom tabs with a second persistent floating bar.
- Recording shows stable timer, clear pause/resume/stop, permission and data-mode explanation, background/lock-screen limitation.
- Every action usable on 320px width, with practical ~44px touch targets; no tap hover-only behaviors.

## 4. Design language
Name: **Quiet Context Workspace**. Calm, modern, familiar; editorial clarity over cyber-dashboard aesthetics. **Light theme default**, optional dark theme with equal a11y quality; preserve recognizable Second Brain brand only after reviewing existing identity.

### Suggested starting tokens (adjust to maintain existing branding)
```
Canvas:        #F7F8FA
Surface:       #FFFFFF
Text primary:  #17212B
Text muted:    #5A6876
Border:        #E2E7EC
Brand accent:  #176D68    (muted teal; contrast-test buttons)
Focus:         #245CE7    (high visibility)
Success:       #18784B
Warning:       #8A5B00
Danger:        #B42318
Dark surfaces: #111827 / #1D2939; recheck all contrast ratios
Spacing grid:  4/8/12/16/24/32; layout max-width ~1160–1280px
Font body:     system-ui/Inter-like, 16px default, >=1.5 line-height
```
Tokens are **proposals**, not audited WCAG-compliant finished combinations. Use tested semantic color pairs; don't communicate statuses by color alone.

### Components that must be standardized
PageShell, Navigation, MobileTabBar, CommandSearch, GlobalCapture, RecordButton, SourceChip, QuoteWithTimestamp, PersonBadge, CommitmentStatus, ReviewSuggestion, EmptyState, InlineError, Skeleton, ConfirmationDialog, InviteNotice, PermissionExplanation, Toast, ConsentBanner, FileUploadProgress, AudioPlayerDownload.

## 5. Key screens and information order
**Home / Today**: one contextual greeting (no vanity metrics), "Next up", "Outstanding promises", "Recent conversations", "Continue where you left off", 1–2 helpful suggestions. Empty Home offers a three-step start.

**People / Directory**: search, recent people, alphabetical list; easy add via name/card/note. Person detail: summary; last interaction; what you promised; upcoming meeting; evidence-linked timeline; notes/files; correct or merge duplicate. No heavy graph visualization as default.

**Meetings / List**: `Upcoming` and `Past`, with `Record` and `Upload` actions. Nested `Schedule`: booking types, connect calendar, booking links. Meeting detail: short overview; action items and decisions awaiting review; participant verification; transcript search; audio playback/download (with expiry), sources, exports. Booking details integrate with Person record.

**Work**: `Today`, `Upcoming`, `Waiting`, `Done`, with person/project filters. A commitment always shows where it came from, whether AI-suggested or user-confirmed. Accept/reject before permanent writes.

**Ask**: focused question field, useful examples, conversation; every sourced factual claim opens a source; optional `Propose action` must ask approval. No fabricated evidence links. `I couldn't verify that` must be a friendly default.

**Capture**: choose 1) Write a note 2) Record audio 3) Upload file/image 4) Add person. After saving, show what was captured, source + suggested next action. Persist draft/retry; never lose data on network error.

**Settings**: Profile, Privacy/data export/deletion, Connected apps, Notifications, Recording retention, Appearance, Help/Feedback; experimental features and developer/MCP controls in Advanced.

## 6. Microinteractions and states
- Clear status ladder: `Saved` → `Processing` → `Ready to review` → `Confirmed` (or `Needs attention`).
- Distinguish AI suggestion from verified fact. A summary is always an AI draft until confirmed or independently validated.
- Explaining consent: `I have permission to record this conversation.` Separate from provider-processing authorization.
- Error: message says what failed, whether original audio/draft is safe and what one action repairs it.
- Empty states: show the minimal single next step, never a blank dashboard.
- Optimistic writes only for reversible UI state; do not falsely confirm server persistence.
- Quick search opens relevant People, Meetings, Work, Files and citations; keyboard shortcut optional.
- Undo within safe window for non-destructive actions; real deletion confirmation is explicit and cannot be silently undone.

## 7. Accessibility / usability requirements
- Target WCAG 2.2 AA: keyboard-only full journey, visible focus, focus not obscured, semantic landmarks, correct heading hierarchy and aria labels; errors described in text and associated with fields; meaningful icons with text labels; respect reduced motion.
- Text contrast >=4.5:1 for ordinary text, scalable to 200%; minimum 24x24 CSS px pointer target per relevant AA criterion where applicable, prefer 44x44 on mobile.
- Test with screen reader on key journeys, Android Chrome, iOS Safari, 320px, tablet and desktop.
- Test first-use comprehension: 3–5 unfamiliar testers find a person, start capture, download recording and follow a source without coaching. Record time, misclicks and confusion.
- Accessibility is tested behavior, not a mere "accessible" design label.

## 8. Developer implementation requirements
- Audit current pages/routes first: preserve routing compatibility and old user bookmarks.
- Start with shared navigation/semantics and states; update one vertical flow at a time; screenshot diff after **signed-in deployment**.
- No decorative graphs, gradient cards, endless badges or giant hero stats without demonstrable value.
- Use the UI UX Pro Max skill as guidance **after reviewing its files**, never as authority over actual user tests.
- Performance targets (proposals, p75): LCP <2.5s, INP <200ms, CLS <0.1; log measured results rather than assume success.
- Each screen accepted by design review **and** one real-browser E2E with network failure/empty state.
