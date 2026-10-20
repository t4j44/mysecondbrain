# Meeting intelligence release contract

This extends the existing Meeting/MeetingCapture pipeline. Supabase PostgreSQL,
RLS, private Storage, durable jobs, pgvector and EntityEdge remain canonical.
No new migration or replacement system is introduced.

## Source and five outputs

`MeetingCapture.transcript_segments` retains complete original-language utterances,
segment/chunk IDs, speaker labels and start/end offsets. A summary never replaces
this source. `retained_until` identifies completed transcription; retry reuses
transcribed segments and validated extraction checkpoints. Audio follows the
existing retention/deletion lifecycle. User-authored notes never edit a transcript.

1. Executive summary: coherent short overview, separate from the legacy 4,000-char
   `summary` preview. Bounded at 32,000 characters; budget overflow fails explicitly.
2. Detailed summary: deterministic narrative from every distinct validated topical
   section, preserving secondary topics, objections, alternatives and conditions.
   It is not recursively compressed into the short preview. Sections remain stored
   independently; detailed narrative has a 2,000,000-character validation limit.
3. Structured notes: topical bullet outline with evidence, risks, ideas, questions
   and feedback. AI draft remains separate from user Markdown/revision history.
4. Minutes: actual date/time, known timezone/location, confirmed identities and
   selected decisions/actions. Unknown roles/deadlines remain unknown. Proposals,
   interpretations and confirmed selections have different labels.
5. Full transcript: searchable speaker/time-labelled canonical source; exact
   evidence opens its segment and seeks retained private audio without auto-play.

Schema v2 adds title/purpose/agenda proposals, executive/detailed summaries,
discussion sections, key points, risks/ideas/numbers and structured evidence.
Existing summary/topics/receipt consumers remain compatible. Legacy v1 conditional
proposals conservatively retain their entire quotation as the condition. Legacy
deadline quotes acquire canonical references, including separate utterances; new
supplied v2 references must substantiate those fields directly.

## Extraction and evidence

Batch whole canonical segments within the configured input budget (maximum 12,000
characters of segment JSON per call, lower when schema/speaker overhead requires).
Default maximum 80 batches; output budget 8,192 tokens per extraction call. A huge
single segment, too many batches, invalid JSON or missing substantial output fails
with source and successful batches preserved. Do not represent partial as complete.
Checkpoint fingerprints cover source, date, model, privacy mode and digest version.
Deterministic merge deduplicates exact equivalent candidates/sections while keeping
distinct material. Successful batches are reused; a provider call interrupted
before checkpoint persistence may still be charged on retry. Exactly-once provider
billing is not claimed.

Each consequential claim references canonical segment ID, speaker ID, exact
offsets and a substantive quote matching with whitespace normalization only.
Normalized-empty quotations, candidate evidence and conditions are rejected. The primary quote
and attributed speaker must match the SAME reference. Deadlines and conditions
must be attached to the candidate's canonical references. Date evidence needs an
unambiguous day/month/year (English/Bangla), matching the assigned date. Unknown
people and ambiguous dates never become invented identities or due dates. Speech,
document content and notes are untrusted data; extraction has no tool execution.

These checks establish source quotation integrity, not semantic truth. Live model
fidelity, omissions and unsupported paraphrases still require bilingual human
acceptance. A mock 90-minute transcript cannot prove real diarization or accuracy.

## Review, history, exports and graph

Meaningful manual title/agenda stays unchanged. AI title, purpose and agenda are
editable proposals. Owned existing venture/project can be linked, explicitly
created in existing Work screens, or ignored. Speaker mapping requires explicit
confirmation; a mention is not attendance.

Authenticated meeting routes under `/api/v1/meetings/{id}`:

| Route | Contract |
|---|---|
| `GET /notes` | User revision, version, history and separate current AI draft |
| `PUT /notes` | `{expected_version, markdown}`; 409 preserves concurrent edits |
| `PUT /review` | Versioned title/purpose/agenda/timezone/location/project/venture review |
| `GET /export/markdown?kind=notes\|minutes\|detailed\|all` | Private, no-store attachment; source IDs/time links; no signed audio URL |
| `POST /confirm` | Explicit all/selected candidate IDs; transactional retry receipt |

Notes use existing `Meeting.meta.meeting_notes`; at most 100,000 characters per
revision and 50 revisions. At the cap the API refuses more edits, preserving all
existing history. Capture/meeting row locks serialize version updates in PostgreSQL.
User edits survive refresh, reindexing and provider retry. Saving notes creates no
CRM facts. Reviewed metadata freezes after confirmation; generic meeting PATCH
cannot bypass these review/history contracts on a captured meeting.

Confirmation owner-proves both graph endpoints and adds typed temporal edges:
meeting→person `participated_in_by`, meeting→venture `about`, meeting→project
`related_to`, meeting→derived item `produced`; existing source-event references
remain. Shared event IDs, occurred_at/valid_from and evidence metadata preserve
provenance. No person→knows→person edge is inferred from attendance. Existing
deletion suppresses source/derived indices, clears note metadata and queues private
object erasure. Replay never grants permission to restore a deleted source.

## Retrieval and UI

Index executive/detailed/section text, separately labelled user notes and bounded
transcript chunks with owner/source/version/segment metadata. Multiple chunks from
the same meeting may be retrieved. Keyword fallback includes secondary topics and
last-chunk content. Ask citations link to authorized meeting segment anchors.
Read-scoped MCP `get_meeting_segments` returns at most ten owner-authorized segments,
optionally one exact segment. Official OAuth resource validation remains enabled;
Prompt Intelligence keeps draft-only and opt-in context scopes.

Phone-first review includes five outputs, visible secondary sections, searchable
transcript, evidence jumps, copy/download, history/conflict notices and selected
confirmation. Polling stops outside active processing. Chromium fixtures cover
320/390/1440 widths; real microphone, locked-screen behaviour, HTTPS auth and
physical-device accessibility remain separate hosted gates.

## Privacy and optional release controls

Text redaction does not sanitize raw audio. Free-mode creation requires an explicit
non-sensitive/non-personal recording attestation, recording permission and provider
terms acceptance (notice v2). Old audio consent cannot authorize new processing.
Hosted paid-private audio stays disabled until
`MEETING_PRIVATE_AUDIO_RELEASE_VERIFIED=true` after owner privacy/budget approval
and actual provider acceptance. No flag changes billing or establishes legal consent.
Google OAuth/sync and portfolio publication default disabled in hosted environments
until their respective release-verification flags are accepted; disconnect/revoke
remain available. Development/test fixtures do not enable hosted flows.
