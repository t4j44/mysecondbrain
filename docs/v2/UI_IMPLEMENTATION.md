# V2 navigation and capture slice

Review as a separate change on top of the integrity PR. Existing paths, records and domain APIs remain canonical.

- Mobile: Home, People, central Capture, Meetings, More. More opens the existing focus-trapped navigation drawer; Ask has a persistent header shortcut. Work, Documents and Settings remain available.
- Desktop: Home, People, Meetings, Capture, Ask, Work, Documents and Settings. Sidebar can collapse without removing accessible names. Page search de-duplicates destinations.
- Capture: four entry choices route to the existing recorder, person form, note/voice editor and document/photo tools. Opening recording consent never requests microphone access automatically. Expanding photo tools preserves the typed note and the existing review-before-save flow.
- Default light mode uses the existing light palette. Stored theme preferences continue to win. Authentication screens and common buttons now use theme tokens; password flows no longer describe passwords as passkeys or claim a secure enclave.
- Meetings filters meet the 44px target at desktop widths as well as mobile. Home hides stale content when a refresh fails.

Verification: navigation/type tests and an initial focused browser run passed except for a 39.6px meeting filter and a transient WebKit color reading while the fixture changed theme. The filter was fixed. Theme testing now starts in the requested theme (matching a saved preference) and checks both palettes. Targeted recheck: 8 passed, 1 intentional width skip, including authentication forms in Chromium/WebKit. The expanded final matrix and exact-commit CI are separate receipts and must be recorded when complete.

Final phase-1 receipt: `ea6a7794219de746b693a94d66471e22bc65a777` passed [Security & Quality](https://github.com/t4j44/mysecondbrain/actions/runs/40494495931): 477 backend tests, 88 frontend tests, 350 browser passes / 46 intentional skips, three meeting scenarios, audits, lint, types and production build. [PostgreSQL CI](https://github.com/t4j44/mysecondbrain/actions/runs/40525464787) passed 67 cases each on fresh, upgraded and restored databases, plus the runtime container check. Browser counts use synthetic APIs, not real integrations.

Phase-2 meeting review: executive summary preview, visible decisions/actions, on-demand detailed summary, notes, minutes and downloads. Hidden panels remain mounted so drafts survive closing. Evidence navigation clears a conflicting transcript filter, opens the transcript and focuses the exact segment; stale meeting loads cannot replace the current route. An initial load failure offers an actual retry. The local meeting browser harness passed at 320/390/1440; full frontend suite passed 90 tests. Screenshots are generated in `.test-tmp/meeting-ui/` and are synthetic fixtures. These phase-2 results do not inherit phase-1 CI.

Still pending: source correction/action revision audit, Telegram, scheduled briefs, watchlists/Scout, hosted/provider/device/usability acceptance. No unavailable feature is added to navigation.

Phase-2 local lint, TypeScript and production build also passed. The initial build stopped at environment validation because no public URLs were supplied; rerunning with the same explicitly synthetic public URLs as CI succeeded. No production credentials were used. The 390px meeting screenshot was visually inspected; the CI evidence artifact now includes all three meeting screenshot widths.
