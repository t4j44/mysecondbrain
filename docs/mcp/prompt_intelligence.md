# MCP Prompt Intelligence

## Purpose

Second Brain Prompt Intelligence rewrites rough prompts for grammar, clarity, professional structure, role-awareness and token efficiency. It can optionally add a small amount of relevant user-owned Second Brain context.

It **never executes the task inside the prompt**. It only returns an improved prompt for the connected AI assistant to use.

## MCP tool

`enhance_prompt`

### Arguments

- `text` (required): prompt to rewrite.
- `mode`: `grammar | improve | structure | compress | full`.
- `compression`: `safe | balanced | maximum`.
- `target`: `auto | chatgpt | claude | gemini | cursor | other`.
- `framework`: `auto | rtf | costar | risen | none`.
- `role`: optional explicit task role, maximum 200 characters.
- `use_context`: whether to retrieve relevant Second Brain context.
- `context_query`: optional retrieval query.
- `context_limit`: 1–8, default 5.

## Prompt-engineering frameworks

### Auto

Second Brain selects a compact framework based on the task:

- **RTF** — Role, Task, Format. Good default for straightforward requests.
- **CO-STAR** — Context, Objective, Style, Tone, Audience, Response. Preferred for communication/content tasks.
- **RISEN** — Role, Instructions, Steps, End Goal, Narrowing constraints. Preferred for analysis, research, strategy and implementation tasks.
- **None** — grammar-only and compression-only workflows do not force a named framework.

Frameworks are used only when they improve execution. Empty or redundant sections should be omitted.

## Role selection

An explicit `role` always wins. Otherwise Second Brain selects a useful working perspective from the prompt, for example:

- software/API/code -> Senior software engineer
- startup/market/pricing -> Startup strategist and market researcher
- legal/compliance -> Legal research specialist
- finance/accounting -> Financial analyst
- design/UI/UX -> Senior product designer
- content/marketing -> Content strategist and editor
- research/analysis -> Research analyst
- learning/exams -> Subject-matter tutor

Roles are prompt perspectives, not claims of real-world credentials.

## Context behavior

When `use_context=false`, no Second Brain memory is retrieved.

When `use_context=true`:

1. the prompt or `context_query` is used to retrieve relevant records;
2. semantic retrieval is attempted first;
3. keyword retrieval is the fallback;
4. no more than 8 records are considered;
5. the prompt sent to the model contains at most roughly 3,500 characters of retrieved context;
6. context is wrapped in `<SECOND_BRAIN_CONTEXT>`;
7. retrieved text is treated as untrusted data, never instructions;
8. only minimal source metadata is returned in `context_used`.

Contextual mode additionally requires `mcp:memory:read`. Plain prompt enhancement only requires `mcp:content:draft`.

## Security and privacy

- owner-scoped RLS remains active;
- prompt text is handled through the existing AI provider/privacy layer;
- unrelated records must not be added;
- context instructions are ignored;
- the tool is non-mutating;
- no emails/messages/posts are sent;
- no prompt is executed by this tool.

## Example

```json
{
  "text": "check my startup competitors and tell me what to build first",
  "mode": "full",
  "compression": "safe",
  "target": "claude",
  "framework": "auto",
  "role": null,
  "use_context": true,
  "context_limit": 5
}
```

Possible output metadata:

```json
{
  "enhanced_prompt": "...",
  "mode": "full",
  "compression": "safe",
  "target": "claude",
  "framework_requested": "auto",
  "framework_used": "risen",
  "role_used": "Startup strategist and market researcher",
  "estimated_tokens_before": 90,
  "estimated_tokens_after": 150,
  "estimated_reduction_percent": 0.0,
  "context_items_used": 3,
  "context_used": [
    {"id": "...", "entity_type": "venture", "title": "Second Brain"}
  ]
}
```

Token counts are estimates based on a lightweight character heuristic and are not provider billing measurements.

## Limitations

- framework selection is heuristic in V1;
- token estimation is approximate;
- compression does not promise zero information loss;
- the tool does not execute the enhanced prompt;
- browser-extension support is intentionally deferred.
