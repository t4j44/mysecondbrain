# Manual calendar fallback

Journey: Meetings → Schedule → enter a proposed time and two city-based time zones → review both dates/offsets → download an ICS calendar file → review/import/send manually in the user's calendar.

This is an **unsaved proposal, not a reservation**. It does not check availability, create a saved meeting/person, expose a guest page, send notifications, or connect to a calendar provider. It is not acceptance of B1–B7 booking requirements. Full booking types, weekly availability, atomic reservations, guest abuse controls, scoped cancellation/rescheduling and provider sync remain disabled/unimplemented until separately reviewed and verified.

Implementation uses the existing authenticated API boundary at `POST /meetings/schedule/preview`. Body-only title/location/time data is rendered into a bounded private no-store response. No saved context, emails, access tokens or meeting notes enter the file. The calendar marks the event tentative/private/transparent and contains no attendee or alarm properties. Do not treat the PRIVATE calendar classification as access control after sharing a file.

Time calculation uses IANA zones, rejects nonexistent local times, and requires an explicit earlier/later choice for repeated times. Duration is elapsed time across a clock change. Output uses UTC start/end; preview retains local offsets for both parties. Text escaping and UTF-8 content-line folding follow [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545).

Validation: 13 backend cases, 3 UI cases, TypeScript, lint and Ruff PASS; independent source review found no blockers. Real calendar imports, physical-device downloads and hosted sign-in are unverified. No invitations or provider actions were performed. Rollback: remove the Schedule entry and preview endpoint; there is no migration or persisted draft to reverse.
