# MCP Scopes & Capability Taxonomy

## Purpose & Least Privilege Philosophy
Taj's Second Brain adopts a strict least-privilege capability architecture for Model Context Protocol interactions. Every external AI client key is assigned a specific set of granular authorization scopes upon creation or rotation. Any attempt to access a tool or resource outside these granted boundaries triggers an immediate JSON-RPC `-32002` exception and logs an automated security violation in `public.audit_logs`.

## Granular Scope Matrix

| Capability Scope | Tool Access Grant | Resource URI Access Grant | Description & Risk Profile |
| :--- | :--- | :--- | :--- |
| `mcp:people:read` | `search_people` | `mcp://people/{id}` | Read contacts, companies, executive titles, and CRM notes. |
| `mcp:memory:read` | `search_memory` | `mcp://memory/{id}` | Access internal reflections, strategic ideas, and founder insights. |
| `mcp:projects:read` | `get_projects` | `mcp://projects/active`, `mcp://portfolio/case-studies` | View active ventures, milestones, and strategic initiatives. |
| `mcp:tasks:read` | `get_tasks` | `mcp://tasks/pending` | Query operational TODO action items and execution deliverables. |
| `mcp:calendar:read` | `get_calendar` | `mcp://calendar/today` | Fetch upcoming meetings, participant lists, and agendas. |
| `mcp:relationship_history:read` | `get_relationship_history` | *N/A* | Traverse historical meeting logs and interaction takeaways with a contact. |
| `mcp:content:draft` | `generate_linkedin_post` | *N/A* | Synthesize founder memories into executive LinkedIn post drafts. |
| `mcp:case_study:draft` | `generate_case_study` | *N/A* | Generate executive STAR career case study prototypes from project data. |
| `mcp:weekly_review:draft` | `generate_weekly_review` | *N/A* | Aggregate completed tasks and reflections into a weekly retrospective draft. |

## Group & Wildcard Super-Scopes
For trusted local developer tools or founder-administered environments, group scopes simplify credential configuration while preserving functional categorization:
* `mcp:read`: Authorizes all 6 read-only exploratory scopes and resource URI handlers.
* `mcp:draft`: Authorizes all 3 content drafting and synthesis generators.
* `mcp:all` or `*`: Complete access to all MCP tools, drafting engines, and resources.

## Scope Violation Auditing
When an unauthorized scope invocation occurs:
1. Execution is cleanly blocked prior to touching any domain services or databases.
2. An audit entry (`mcp.security.scope_violation`) is written to `public.audit_logs` capturing the attempted client name, assigned scopes, requested scope, tool name, and timestamp.
