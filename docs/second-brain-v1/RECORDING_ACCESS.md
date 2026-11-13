# Original recording access

User journey: open an uploaded meeting, play the original or choose Download original audio before retention ends. The original format is preserved. Expired/deleted audio has an explicit unavailable state; a not-yet-ready upload can be retried. An audio failure does not become a transcript/review failure.

Implementation: `meeting_intelligence.py` reuses owner-scoped `capture_for` and bounded `AudioStorage`; `RecordingPanel` is mounted on existing meeting detail. The authenticated download proxy returns original bytes, safe MIME-derived extension and attachment disposition, private/no-store and nosniff headers. Playback signed URLs are capped at the smaller of 300 seconds and remaining retention. Another account or anonymous request is denied before storage access. No public storage URL is introduced for downloads. No migration or increased retention.

Validation: affected meeting API suite 110 PASS; final recording API 15 PASS and Ruff PASS after unavailable-state refinement. Frontend affected search/recording/meeting tests 25 PASS and TypeScript/lint PASS; final recording suite 8 PASS, including a stale-expiry-body regression, followed by TypeScript PASS. Tests use synthetic local data and do not establish hosted RLS, real Storage delivery, physical-device playback or large-file load behavior. Download buffering reuses the existing configured 50 MB ceiling; it is not a streaming service.

Independent review prompted the distinction between an unfinished upload and confirmed expiry, and invalidation on changed retention/deletion metadata. Review scope and remaining gates are in `WORK_LOG.md`. API and web must be deployed together to accept this feature on staging. The review branch has Git deployment disabled.

Rollback: revert the recording feature commit to restore existing playback. Existing meeting, transcript and recording data are unchanged by rollback. No invitation gate is cleared by these local tests.
