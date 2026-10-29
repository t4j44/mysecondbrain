# Source-backed meeting preparation

Planning: compact; context: existing meeting/participant junction, canonical commitments and relationship history; verification: owner isolation, deleted/stale records, bounded output and mobile error/reload behavior; delegation: none.

The existing MCP preparation tool returns the selected person's broader context. This slice adds a meeting-specific, on-demand view using the same canonical records. Only explicitly linked participants qualify; names in AI drafts or Calendar descriptions never create inferred people links. No provider call, model inference, autonomous message or new persistence layer is needed.

Each response includes up to five people, their saved profile notes, latest saved interaction and up to three active commitments. Every displayed fact links to its owner-scoped source. Archived/deleted people and interactions and deleted/closed commitments are excluded. All timestamps describe saved records; this view does not verify live Calendar synchronization. Reload recomputes from current canonical state and clears the previous display on failure.

Google OAuth acceptance and opt-in scheduled daily/weekly delivery remain separate unfinished gates. No scheduling, achievement or provider-delivery claim follows from this preparation view.
