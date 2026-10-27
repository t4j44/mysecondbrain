# V2 navigation and capture slice

Review as a separate change on top of the integrity PR. Existing paths, records and domain APIs remain canonical.

- Mobile: Home, People, central Capture, Meetings, More. More opens the existing focus-trapped navigation drawer; Ask has a persistent header shortcut. Work, Documents and Settings remain available.
- Desktop: Home, People, Meetings, Capture, Ask, Work, Documents and Settings. Sidebar can collapse without removing accessible names. Page search de-duplicates destinations.
- Capture: four entry choices route to the existing recorder, person form, note/voice editor and document/photo tools. Opening recording consent never requests microphone access automatically. Expanding photo tools preserves the typed note and the existing review-before-save flow.
- Default light mode uses the existing light palette. Stored theme preferences continue to win. Authentication screens and common buttons now use theme tokens; password flows no longer describe passwords as passkeys or claim a secure enclave.
- Meetings filters meet the 44px target at desktop widths as well as mobile. Home hides stale content when a refresh fails.

Verification: navigation/type tests and an initial focused browser run passed except for a 39.6px meeting filter and a transient WebKit color reading while the fixture changed theme. The filter was fixed. Theme testing now starts in the requested theme (matching a saved preference) and checks both palettes. Targeted recheck: 8 passed, 1 intentional width skip, including authentication forms in Chromium/WebKit. The expanded final matrix and exact-commit CI are separate receipts and must be recorded when complete.

Still pending: progressive meeting-detail layout, source correction/action revision audit, Telegram, scheduled briefs, watchlists/Scout, hosted/provider/device/usability acceptance. No unavailable feature is added to navigation.
