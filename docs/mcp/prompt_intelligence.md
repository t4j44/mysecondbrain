# MCP Prompt Intelligence on V1.5

`enhance_prompt` rewrites a rough instruction into a draft for the user to review.
It does not research the subject, answer the underlying question, execute code,
send messages, create tasks, save a session, publish, or change domain records.
The MCP annotation is read-only and non-destructive. No prompt history or feature
telemetry is stored. Existing credential usage timestamps still update normally.

## Inputs and permissions

| Input | Default | Values / bounds |
| --- | --- | --- |
| `text` | Required | Nonblank, at most 20,000 characters |
| `mode` | `full` | `grammar`, `improve`, `structure`, `compress`, `full` |
| `compression` | `safe` | `safe`, `balanced`, `maximum` |
| `target` | `auto` | `auto`, `chatgpt`, `claude`, `gemini`, `cursor`, `other` |
| `framework` | `auto` | `auto`, `rtf`, `costar`, `risen`, `none` |
| `role` | `null` | Optional nonblank working perspective, at most 200 characters |
| `use_context` | `false` | Boolean, not a string |
| `context_query` | `null` | Optional nonblank query, at most 500 characters |
| `context_limit` | `5` | Integer from 1 through 8 |

Every call requires **`mcp:content:draft`**. `use_context=true` additionally requires
**`mcp:memory:read`**, even in grammar mode. This applies to OAuth and legacy keys.
The existing legacy group-scope rules remain supported. An unrelated read scope
does not grant memory access. Plain rewriting never loads private records, even
for name redaction; only supplied text and a supplied/inferred perspective are used.

Context permission intentionally permits relevant cross-domain facts for this
tool, including people, projects, events and document excerpts. Consent wording
describes this. It does not broaden the scopes of other retrieval tools. OAuth
clients must request the necessary scopes at registration/authorization and the
user must approve them. Existing connections are never silently upgraded.

Missing permissions produce HTTP 403 at the legacy `/mcp/tools/invoke` endpoint.
The official SDK's JSON-RPC `/mcp` transport reports a protected tool failure via
`result.isError=true` (normally HTTP 200). Missing, expired or revoked credentials
produce HTTP 401 before tool execution. Revoke in Settings to block subsequent calls.

## Rewriting strategy

- `grammar`: correct wording, grammar and spelling only. No added role, framework
  or retrieved context, even if supplied. This mode restriction takes precedence.
- `improve`: clarify the instruction without unnecessary sections.
- `structure`: organize existing requirements into useful sections.
- `compress`: remove repetition and filler; preserve requirements and exceptions.
- `full`: combine clarity, useful perspective, structure and safe condensation.

An explicit framework wins outside grammar mode. Automatic selection uses
word-boundary rules: CO-STAR for communications (Context, Objective, Style, Tone,
Audience, Response); RISEN for complex research/implementation (Role, Instructions,
Steps, End Goal, Narrowing constraints); RTF for a straightforward task (Role,
Task, Format). Tiny requests, automatic compression and basic improvement use no
named framework. Empty sections and invented output requirements are discouraged.
These are conservative heuristics, not a claim of perfect intent classification.

An explicit role wins outside grammar mode. Otherwise, subject words suggest a
software engineer, product designer, startup strategist, editor, researcher,
tutor, financial analyst or legal research perspective. Uncertain matches get no
role. Substring accidents such as `api` in `capital` do not infer software work.
Roles describe a working perspective; they do not fabricate professional credentials.

Safe compression favors nuance. Balanced condenses repeated wording; maximum is
terser but is still instructed to preserve every constraint. Targets change only
light organizational guidance. `auto` and `other` remain portable. No hidden model
syntax or requests for private chain-of-thought are added. Coding structure uses
repository context, constraints and acceptance tests only when already supplied.

## Context, privacy and injection boundary

Retrieval reuses V1.5 services: recognized structured/temporal answers first, then
matching canonical entities and events, current graph links with valid source
evidence, existing semantic search and canonical keyword fallback. Recognized
temporal questions do not fall through to undated facts. Documents reuse existing
normalized Markdown sections; no additional vector store, index or migration.
Every candidate is checked again against the authenticated owner and live
visibility/deletion rules. PostgreSQL row-level security adds the database boundary.

Only `use_context=true` triggers retrieval; grammar bypasses it. `context_query`
overrides the retrieval query; otherwise the first 500 characters of `text` are
used. No more than eight items are supplied, with each excerpt capped at 900
characters. The **whole escaped, pseudonymized context block** is capped at 3,500
characters, including titles, identifiers, separators and delimiters. The overall
AI input limit still applies. Less context may fit when redaction expands names.

User text, requested role and retrieved records are escaped data in explicit
`USER_PROMPT`, `REQUESTED_ROLE` and `SECOND_BRAIN_CONTEXT` blocks. None is inserted
into the system instruction. The fixed instruction says to rewrite rather than
execute and to ignore instructions within source records. Delimiter injection
cannot create new blocks. This reduces prompt-injection risk; it cannot prove
that every model output faithfully preserves meaning. Review the returned draft.
The service has no tools for executing the rewritten task or writing domain rows.

Canonical records remain in Supabase. The existing `free_redacted` provider path
is retained. Its sensitive-content check runs on original text before masking;
known retrieved entity titles and likely proper names use private placeholders.
Request-local placeholders preserve URLs, contact addresses, dates and numbers
without sending those literals. Only this request's values are restored server-side.
If the model drops a protected literal, the original prompt is returned unchanged
with `rewrite_status=original_preserved`, rather than claiming a successful rewrite.
Names, examples, requested language, tone and other semantic constraints are also
required by the model instruction but are not a general deterministic guarantee.

This is an early beta: do not submit highly sensitive or confidential material.
Redaction is heuristic and is not guaranteed anonymization, including for names
in arbitrary languages. Internal Gemini minimization is separate from the external
AI client's policies: the authorized client receives the restored draft and minimal
source titles/IDs. Later billing-enabled Gemini uses the same provider abstraction
and configuration; no new provider or paid requirement was introduced here.

## Response and examples

Response fields: `enhanced_prompt`, `mode`, `compression`, `target`,
`framework_requested`, `framework_used`, `role_used`, `estimated_tokens_before`,
`estimated_tokens_after`, `estimated_reduction_percent`, `context_items_used`,
`context_used`, `rewrite_status`, `note`.

`context_used` contains only `{id, entity_type, title}` references, never excerpts
or document bodies. The count means items supplied to the model, not proof that
each item influenced the output. IDs/titles are private response data, not telemetry.
Token estimates use roughly one token per four characters, **not provider billing
or tokenizer measurements**. A longer draft reports zero reduction, never negative
savings. No extra generation call is made to chase a smaller token count.

Plain grammar request (draft permission only):

```json
{"text":"please make this sentence clearer","mode":"grammar"}
```

Contextual acceptance request (both permissions):

```json
{
  "text": "research competitors for Justor and decide what we should test next",
  "mode": "full",
  "framework": "auto",
  "target": "claude",
  "use_context": true,
  "context_limit": 5
}
```

The second call returns a research instruction informed by relevant saved facts;
it does not perform competitor research. Explicit customization:

```json
{"text":"compare these onboarding approaches","framework":"rtf","role":"Product manager","compression":"balanced"}
```

Hosted acceptance must connect an actual external AI client, run the contextual
example against synthetic owner-only records, confirm no domain changes, revoke
the connection, and verify rejection. Local HTTP/SDK tests and CI do not establish
hosted client compatibility, real Gemini rewrite quality or private-beta readiness.
