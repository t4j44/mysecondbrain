# Canonical commitment actions

Implementation decision: extend the existing commitment ledger and source links. No parallel task store, provider activation or AI call. Planning: deep; context: dependencies and all current commitment writers; verification: backend, browser, PostgreSQL concurrency and migration/restore; delegation: none.

This slice adds revision-checked, replay-safe Done, Working, Snooze and Help actions. Existing completed/cancelled statuses remain; unfinished work includes open, in_progress, waiting and snoozed. Snooze records a separate reminder time and its IANA zone, preserving the promised deadline. Done is self-confirmation, not evidence that a message was sent or a third party accepted delivery. Help is a deterministic draft with source links, never an external send.

Every commitment update advances its revision, including older application paths and direct database writes. Action requests lock the owned row and match the reviewed revision. Receipts are owner-scoped and unique per request; changing an already-used request is a conflict. A deleted or foreign commitment is unavailable. Linked tasks are completed only when their current linked commitments are all completed.

Migration 38 is review-only until an owner-authorized staging migration. No Telegram sender, scheduled notification or live delivery is claimed by this slice.

Local evidence on 2026-10-28: the full isolated backend run passed 507 tests before the last two regressions and shared-task helper reuse. The final focused run passed 41 commitment, relationship, structured-answer and network tests, including owner-only account erasure and active-state retrieval. All 103 frontend tests passed. Four browser scenarios passed at Chromium 320/390/1440 and WebKit 390; the 390px screenshot was inspected after the final button styling change. The browser scenario exercises editable Help, explicit Snooze, conflict/reload and Done, plus overflow/accessibility checks. These use synthetic fixtures, not hosted/provider acceptance.

PostgreSQL cases are committed for identical/competing action races, direct SQL revision advancement, cross-owner foreign-key rejection and browser receipt denial. They require the disposable CI database; no local PostgreSQL pass is claimed. Exact-revision CI receipts belong in the release manifest after execution.
