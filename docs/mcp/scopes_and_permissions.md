# MCP authorization and scopes — V1.5

OAuth is authorization-code + PKCE S256, with Supabase browser sign-in and explicit
consent. All tool calls derive the owner from the verified token. They check scopes
before running shared services under PostgreSQL row-level security (RLS).

| Permission | Capability |
|---|---|
| `mcp:people:read` | Contacts and organizations |
| `mcp:memory:read` | Memories; optional relevant cross-domain context for prompt rewriting when draft scope is also granted |
| `mcp:projects:read` | Projects and ventures |
| `mcp:tasks:read` | Tasks |
| `mcp:relationships:read` | Relationship history |
| `mcp:calendar:read` | Saved meetings |
| All six read scopes | Cross-domain context/document retrieval and relevant contacts |
| `mcp:tasks:write` | Create/update tasks |
| `mcp:memory:write` | Save memories |
| `mcp:people:write` | Create/update contacts |
| `mcp:projects:write` | Create/update projects |
| `mcp:decisions:write` | Save decisions |
| `mcp:sessions:write` | Save session records |
| `mcp:content:draft` | Prepare content drafts and rewrite prompts; no publishing, messaging or execution |
| `offline_access` | Rotate refresh tokens until grant expiry; does not grant tool access |

`finalize_work_session`, reviewed capture and interaction finalization require the
session, task, decision, memory and people write scopes together because they can
create those related records atomically. Missing any permission fails closed.
OAuth offers granular scopes only; it never offers `mcp:all`, `*`, or broad write scopes.
Legacy keys retain their existing compatibility rules in `app/mcp/security.py`.

`enhance_prompt` requires only draft scope for plain rewriting, which reads no
private records. `use_context=true` additionally requires memory scope. Its bounded
context can include relevant people, projects, events and document excerpts;
consent describes that boundary. See [Prompt Intelligence](prompt_intelligence.md).

Only requested scopes can be approved. Token exchange cannot change code scopes;
refresh can narrow scopes but cannot increase them. Tokens are bound to this issuer,
resource, owner and client. Exact redirect matching, one-use codes and PKCE prevent
code theft/replay. Revoked/expired grants and closed accounts fail every access check.
OAuth vault tables are server-only; owners may read their own connection metadata.
Raw token, code, request and client-secret values are hashed at rest and omitted from exports.

OAuth authorizes the selected capabilities; it does not certify every AI-generated
write as fact. Important changes still follow review and explicit confirmation in the
client workflow. Existing identities are not silently changed on a create/deduplicate
call. Ambiguous identities require selection, and partial project names do not auto-link.
External AI clients have separate data policies; access to approved private context
must be a deliberate user choice. No tool sends WhatsApp/email messages.
