# Privacy and beta data inventory — V1.5

Canonical private data remains in Supabase. This early free-tier beta is unsuitable
for highly sensitive or confidential information. Redaction is pseudonymization, not
a guarantee of anonymity. The provider minimizes contact details and uses stable
owner-scoped entity placeholders where literal identity is unnecessary. High-risk
inputs are refused by the free AI path; private manual capture still works.

| Data | Storage / access | Export / deletion |
|---|---|---|
| People, projects, interactions, notes, tasks, commitments | Owner-scoped PostgreSQL + RLS | Active canonical records in JSON/CSV/Markdown; account erasure removes owner rows |
| Context events | Separate happened/recorded times, timezone, source, original text/payload and derived summary | Active records exported; event erasure clears original text/summary/payload and keeps only a replay tombstone |
| Graph and vectors | Existing entity_edges and pgvector; private/restricted and deleted-source checks | Vectors excluded; event erasure removes derived search context and provenance links |
| Card/moment photos | Private owner-prefixed Storage, re-encoded JPEG/WebP, no original or EXIF | Metadata exported, binary bytes not included; event/person erasure queues durable object deletion; account closure sweeps owner objects |
| Unconfirmed media | Private draft attachments, maximum two per capture | Existing worker expires unconfirmed media after 24 hours |
| Outreach drafts/outcomes | Private receipts and explicitly confirmed events | Open does not mean sent; erased event receipts retain content-free replay metadata |
| MCP OAuth | Hashed codes/opaque tokens/client secrets in server-only vault tables; owner-readable grant metadata | No vault secrets in exports; revoke checked on each call; account closure blocks access and removes owner vault records |
| Google OAuth | Existing encrypted integration-token vault | Excluded from exports; disconnect/account-erasure lifecycle retained |
| Pilot telemetry | Private audit events with type/count/IDs, no prompt/body/contact fields | Owner activity view; no inferred delivery, payment or testimonial; account erasure removes owner logs |

`private` context events are eligible for authorized retrieval. `restricted` events
are available through the owner's direct event view/export but excluded from semantic
and keyword retrieval. An external AI with approved read scopes receives approved
private context and has its own privacy policy. Free-tier redaction governs calls made
by Second Brain to Gemini; it is not a claim about an external assistant's retention.

Deleting an event removes its derived interactions, memories, tasks, decisions and
commitments from active access/search/export, invalidates linked publication drafts,
and queues its media for retryable erasure. Existing people/projects merely referenced
by that event remain. Deleting one derived record is not equivalent to deleting its
original event; use the event's Delete this context control to erase the whole capture.
Ordinary soft-deleted domain content is retained in the database until account erasure;
it is excluded from active retrieval and exports. Erasure is not an instant backup purge.

Exports contain no original attachment bytes and no integration/MCP token vaults.
CSV cells are escaped against spreadsheet formulas; JSON retains canonical text.
No automatic 90-day audit purge or instant full backup erasure is claimed. See the
runbook for separate hosted RLS, Storage, provider and account-erasure acceptance.
