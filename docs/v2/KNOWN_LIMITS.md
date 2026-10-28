# Known limits of the V2 candidate

- Pilot is NO-GO. The source changes have automated receipts; the assembled hosted product has not been accepted.
- Navigation and capture are implemented. Meeting outputs now use progressive disclosure. Existing canonical records, workflows and light/dark branding are retained.
- Meeting notes have saved history and conflict checks. After-confirmation speaker/context correction and derived-record invalidation still need a complete reviewed workflow; do not describe them as finished.
- Telegram linking, consent, revocation, bounded sender attempts, canonical callback actions and reminder history have a default-off implementation. Explicit check-ins respect quiet hours and caps; ambiguous delivery never automatically retries. Scheduled briefs are incomplete. No live bot delivery has been tested; PR22's provider calls use mocked transport.
- Web commitment actions now record reviewed Done/Working/Snooze/Help requests. Done is owner confirmation; Help is an editable deterministic draft. Saving a check-in time does not deliver a reminder. Migration 38 and hosted action acceptance remain outstanding.
- Calendar remains behind its existing release gate. Research enrichment exists; watchlists and Opportunity Scout are not complete. No synthetic opportunities are displayed as real.
- Physical phones, real microphone/camera, actual external MCP client, hosted two-account Storage isolation and offsite Auth/Storage recovery remain unverified.
- No measured pilot costs, real tester count, customer revenue or paid entitlement activation is claimed. See COSTS and PILOT_GATES.
