# Relationship Intelligence V1 — implementation audit

September 25, 2026. Baseline local and remote: `0b3aadf4761a07e80462cff12ac0b695d063e0f7`, branch `codex/free-tier-beta`. Existing untracked recovery files and graph index changes are preserved. No merge to main.

## KEEP

- FastAPI, Next.js, Supabase Auth/PostgreSQL/Storage/RLS, Gemini Free Tier with private placeholders, pgvector, bounded document retrieval, MarkItDown, job queue, portable export and account closure.
- `services/capture.py`: proposal, explicit confirmation, atomic persistence, retry receipt and indexing jobs.
- `services/network.py`, `repositories/network.py`: affiliations, relationship history, commitments, stale-contact and venture queries.
- `ai/structured.py`: deterministic overdue/open queries and evidence-linked recommendations; `ai/indexing.py` and `ai/retrieval.py`: semantic/keyword retrieval.
- Existing MCP server/scopes; existing tasks, projects, ventures, meetings and document screens as Work destinations.
- PostgreSQL migration, RLS and dump/restore CI gates. Prior passing CI is baseline evidence, not verification of the revised product.

## REFACTOR

- Home currently contains hardcoded tasks, meetings and contacts; completion only changes React state. Replace with owner-scoped stored evidence and explicit, durable actions.
- Primary navigation already has five labels but Work leads only to Tasks; desktop/mobile order differs and generic OS terminology remains. Share navigation definitions and add a Work hub.
- Person detail displays identity and notes, while richer history/commitments exist only in backend/MCP. Bring those into one source-linked profile with explainable recency labels.
- Capture needs topic persistence, explicit person/work/task/commitment edges, editable meeting date, existing-record identity review and immediate links to saved context. Never invent relative dates or silently overwrite existing identity facts.
- Ask recognizes only a narrow set of phrases. Route relationship/history/network queries through bounded deterministic queries and existing semantic retrieval, retaining citations and no-evidence responses.

## REMOVE / HIDE

- Hardcoded Home data, simulated completion messages and unsupported relationship/confidence claims.
- Life KPIs, content engine, idea incubator and operator terminology from primary discovery. Keep legacy URLs/data and place optional tools in Settings.
- Technical terms in primary navigation. MCP remains Settings > AI assistant access.

## ADD

- A shared relationship capability service serving Home, People, Work, Ask and MCP; no new graph database or permanently running agents.
- Reviewed follow-up drafting, scheduling, dismissal and outcome recording with idempotency, current-evidence checks, linked tasks/interactions and no external sending.
- Two owner-scoped tables: reviewed public professional claims and relationship action receipts. Add RLS, account-active restrictions, ownership constraints, export/erasure coverage and PostgreSQL tests.
- Public enrichment adapters and source provenance: explicit public-page research/manual evidence, bounded fetching with public-address/redirect/robots checks, identity review, qualitative confidence with reasons, conflicts and explicit profile updates. No authentication bypass, bulk private-contact search or social scraping workaround.
- Activation checklist and private event counts for people/interactions/projects/commitments/Ask, weekly activity and confirmed relationship outcomes. No fabricated traction or billing implementation.

## Delivery and verification

Implement in coherent commits: navigation/Work; reviewed Capture; shared relationship profiles/Home/actions; relationship Ask/MCP; enrichment; analytics/onboarding. Cross-cutting privacy and tests accompany the relevant change. Complete backend/frontend checks, real PostgreSQL/RLS and restore CI on the final pushed SHA.

Fresh baseline public probes: web login returned 200; backend `/health/live` and `/health/ready` timed out at 35 seconds. GitHub reports a Vercel deployment for the baseline SHA; production association remains unverified. Hosted verification requires current staging credentials and provider access. This is an external release gate, not a reason to stop independent implementation.
