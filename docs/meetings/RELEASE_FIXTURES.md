# Synthetic release fixtures

No customer recording, account secret or production object is needed locally.

`apps/api/tests/test_meeting_release.py::long_segments` generates 90 one-minute
sections. Minute 45 preserves `UAE expansion: দুবাইয়ের বাজার পরীক্ষা করব, যদি অনুমতি
পাই।` as a secondary section; minute 89 contains `cobalt invoice 417`. Other sections
discuss financing, alternatives, costs, objections and uncertainty. These are
synthetic timestamps/text, not a 90-minute provider transcription benchmark.

Run from repository root in the locked test environment:

```powershell
$env:PYTHONPATH='apps/api'
$env:APP_ENV='test'
$env:ENVIRONMENT='test'
python -m pytest apps/api/tests/test_meeting_release.py -q -o addopts=''
pnpm --filter @second-brain/web test
pnpm --filter @second-brain/web test:meetings-ui
```

Assertions: every digest/section retained; middle and final topic retrievable;
successful batch reused after failure; no cross-speaker stitched quote; forged
segment/speaker/offset/quote rejected; ambiguous due dates rejected; legacy
conditional/deadline compatibility; owner/anonymous denials; note 409/history/retry;
typed idempotent graph confirmation/deletion; bounded scoped MCP read. Real
PostgreSQL tests additionally race note versions and confirmation transactions.

Illustrative source-backed outline (not a live model result):

```markdown
# Synthetic financing meeting
## At a glance
Financing alternatives and conditional UAE exploration were discussed.
## Detailed summary — UAE market exploration
Market exploration depends on permission; no unconditional launch was agreed.
## Notes
- Permission remains required. [speaker c1:spk_1, 2700s, c1:45]
  > দুবাইয়ের বাজার পরীক্ষা করব, যদি অনুমতি পাই।
## Minutes
Status: Proposed — not confirmed
Timezone: Unknown unless explicitly supplied
Responsible person: Unassigned until mapped
Deadline: Not specified
## Source
c1:45 at 2700–2760s — UAE expansion discussion
```

Actual authenticated Markdown export uses the meeting ID and URL-encoded segment
anchors. The export/API regression checks absence of signed audio URLs. Synthetic
screenshots land in `.test-tmp/meeting-ui/`, never substitute for phone acceptance.

For real Gemini acceptance, create a consented NON-personal English/Bangla sample
with primary/secondary topics, an explicit conditional promise, an unambiguous
date and a late unique fact. Use only approved staging provider credentials and
`apps/api/scripts/meeting_provider_smoke.py`; see RELEASE_RUNBOOK before any call.
Human compares full transcript and all five outputs against the recording; record
omissions, speaker errors, false claims, latency and usage without publishing raw
audio/text. Streaming and physical-phone checks must be recorded separately.
