# V2 feature evidence matrix

Baseline inspected at `5089044`. No row is PILOT_READY. Tests below must be filled with exact revision receipts, never copied from older reports.

| Capability | Code evidence | V2 status | Hosted acceptance |
|---|---|---|---|
| Auth, RLS, private Storage, export/erase | dependencies/auth.py, db/rls.py, migrations 20/26/35/36 | Existing; preserve | Two-account, Storage and recovery gates pending |
| People / context / commitments | models/entities.py, services/commitment_actions.py, services/relationships.py, services/context_events.py | Canonical revision-checked Done/Working/Snooze/Help implemented; active-state queries and shared-task completion preserved | Pending; see COMMITMENT_ACTIONS for isolated evidence |
| Meeting record/upload/recovery | components/meetings/capture-panel.tsx, services/meeting_intelligence.py, jobs/handlers/meeting_processing.py | Existing; recorder-collapse regression repaired | Real audio/provider/device pending |
| Five meeting outputs, sources, review | meeting-outputs.tsx, meeting_evidence.py, meeting confirmation tests | Progressive disclosure and filtered evidence navigation implemented; correction/action audit pending | Pending |
| Ask / documents / OCR / MCP | ai/, mcp/, documents services, photo-text-input.tsx | Existing; preserve canonical retrieval | Real external-client acceptance pending |
| Mobile premium UX | PR13/14 reconciliation plus V2 navigation/capture slice | Five mobile destinations, collapsed desktop sidebar, four capture choices, existing light/dark themes; meeting-detail refinement pending | Physical phones/usability pending |
| Google Calendar/Drive | Google services and release_gates.py | Existing; release gate remains required | OAuth/refresh/revoke pending |
| Telegram assistant/outbox/preferences | assistant_connections, notification_outbox, telegram_delivery and telegram_callbacks services; encrypted connection and hashed button vaults | Default-off linking, consent, bounded delivery attempts, canonical buttons and activity UI implemented in PR22; scheduled briefs remain incomplete | Mocked provider and disposable-database evidence only; no live bot acceptance; keep OFF |
| Daily/weekly assistant briefs | Founder deterministic brief and person context exist; no scheduled assistant digest | PARTIAL building blocks | Not advertised as scheduled delivery |
| Contact research | public_sources.py, enrichment.py, PublicProfileClaim | Existing review-safe enrichment; watchlists missing | Approved-source/identity acceptance pending |
| Opportunity Scout / Discover | Existing Home opportunities are recorded interaction hints, not a verified Scout | NOT BUILT | No invented opportunity feed |
| Work/projects/ventures/portfolio | Existing canonical models/routes retained | Preserve; publication gate remains | Optional publishing not accepted |
| Billing / measured economics | Meeting quota exists; no verified paid-pilot billing | NOT VERIFIED | No charging or paid activation |
| Oracle / voice calls / alternate memory engines | Optional research only | DEFERRED | No provisioning or model swap |
