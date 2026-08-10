# Agent File Ownership & Domain Boundaries - Taj's Second Brain

Version: 1.0  
Author: Agent 0 — Lead Orchestrator  
Status: Active & Mandatory  

---

## 1. Ownership Principles

1. **One Owner per Path:** Every file and directory within the repository has an explicit primary agent owner.
2. **No Silent Modifications:** Agents must not silently modify files outside their assigned domain. If an agent requires a contract or helper from another domain, it must request the change through Agent 0 or utilize approved shared extension points.
3. **Single Render Service Consolidation (ADR-013):** Both REST endpoints (Agent 3) and MCP endpoints (Agent 10) execute within a single Python runtime in `apps/api/`. Agent 10 mounts its Streamable HTTP application at `/mcp` inside Agent 3's ASGI server and consumes shared domain services without duplicating repositories.

---

## 2. Definitive Ownership Table

| Agent ID | Agent Role & Name | Owned Directories & File Paths | Permitted Shared Extensions & Read-Only Dependencies | Forbidden Paths |
|---|---|---|---|---|
| **Agent 0** | Lead Orchestrator | `agent_task_board.md`, `integration_status.md`, `docs/orchestration/**`, repository root config governance | Reads all files; supervises merges and resolves cross-agent conflicts. | Specialist application feature code |
| **Agent 1** | Architecture & Contracts | `Tajs_Second_Brain_PRD_TRD.md`, `implementation_plan.md`, `database_schema.md`, `api_contracts.md`, `security_and_privacy_plan.md`, `development_roadmap.md`, `docs/architecture/**` | Reads all existing implementations to verify contract compliance. | Feature implementation code in `apps/`, `src/`, `supabase/migrations/` |
| **Agent 2** | Database & RLS | `supabase/config.toml`, `supabase/migrations/**`, `supabase/seed/**`, `supabase/tests/**`, `packages/database/**`, `docs/database/**` | Can update database sections of `database_schema.md` and `security_and_privacy_plan.md`. | `apps/web/**`, `apps/api/**`, `packages/ui/**`, `packages/prompts/**` |
| **Agent 3** | FastAPI Backend & Domain Services | `apps/api/app/main.py`, `config.py`, `dependencies/**`, `middleware/**`, `models/**`, `repositories/**`, `schemas/**`, `services/**` (excluding specialized AI/Export/MCP internals), `routers/**`, `apps/api/requirements.txt`, `pyproject.toml` | Consumes `packages/database`. Shares domain service layer with Agent 10. | `apps/web/**`, `supabase/migrations/**`, `apps/api/app/api/v1/endpoints/mcp.py` |
| **Agent 4** | Frontend Foundation & Design System | `apps/web/package.json`, `apps/web/app/layout.tsx`, `apps/web/app/(auth)/**`, `apps/web/components/layout/**`, `apps/web/components/ui/**`, `apps/web/lib/auth/**`, `apps/web/lib/api/**`, `packages/ui/**`, `docs/frontend/**` | Defines navigation and shell extension points for Group B and C UI agents. | Backend APIs (`apps/api/**`), Database migrations |
| **Agent 5** | Founder Dashboard & Execution | `apps/web/app/(dashboard)/dashboard/**`, `ventures/**`, `projects/**`, `tasks/**`, `apps/api/app/routers/dashboard.py`, `ventures.py`, `projects.py`, `tasks.py` | Consumes UI components and backend domain service repositories. | Auth middleware, database migrations, security rules |
| **Agent 6** | CRM & Memory System | `apps/web/app/(dashboard)/people/**`, `organizations/**`, `memories/**`, `meetings/**`, `apps/api/app/routers/crm.py`, `interactions.py`, `meetings.py`, `memories.py`, `docs/features/*crm*.md` | Consumes frontend shell and backend shared domain services. | Auth, core UI primitives, database migrations |
| **Agent 7** | Knowledge Export, GDrive & GCal | `apps/web/app/(dashboard)/settings/integrations/**`, `settings/export/**`, `apps/api/app/routers/integrations.py`, `exports.py`, `apps/api/app/integrations/**`, `apps/api/app/jobs/handlers/sync_*.py`, `export_*.py`, `knowledge/Founder_OS/**` | Utilizes shared job runner and token encryption interfaces from Agent 3. | Unrelated feature routers, DB migrations |
| **Agent 8** | Semantic Search, RAG & AI Assistant | `apps/api/app/ai/**`, `apps/api/app/routers/search.py`, `assistant.py`, `documents.py`, `apps/api/app/jobs/handlers/document_processing.py`, `apps/web/app/(dashboard)/assistant/**`, `packages/prompts/**` | Consumes `pgvector` queries via Agent 2 abstractions; integrates with `BaseLLMProvider`. | Non-AI backend routers, core Auth |
| **Agent 9** | Idea Vault, KPIs, Portfolio & Content | `apps/web/app/(dashboard)/ideas/**`, `kpis/**`, `achievements/**`, `content/**`, `weekly-reviews/**`, `apps/api/app/routers/ideas.py`, `kpis.py`, `portfolio.py`, `content.py`, `weekly_reviews.py`, `packages/prompts/content/**` | Consumes RAG retrieval service and AI Provider from Agent 8. | Direct LLM vendor SDK imports, core foundation |
| **Agent 10** | Secure MCP Server & External Access | `apps/api/app/api/v1/endpoints/mcp.py` (or `/mcp` mount runtime), `apps/api/app/services/mcp/**`, `apps/api/app/schemas/mcp.py`, `apps/api/app/repositories/mcp.py`, `docs/mcp/**`, client configuration files | Mounts inside Agent 3's FastAPI ASGI app (`apps/api/app/main.py` via explicit mount contract). Calls shared domain services. | Standalone separate deployed services; duplicating business repositories or raw SQL |
| **Agent 11** | Security, Privacy, DevOps & Production | `tests/security/**`, `docs/security/**`, `docs/privacy/**`, `docs/production-readiness/**`, deployment configs, Dockerfiles, GitHub Actions workflows | Audits all application code, logging configurations, RLS policies, and secret isolation. | Application feature implementations |
| **Agent 12** | E2E QA & Browser Automation | `tests/e2e/**`, `tests/integration/**`, `apps/web/test/**`, `apps/web/__tests__/**`, `apps/api/tests/**`, `docs/qa/**` | Executes tests across all endpoints and UI components; logs defect registers. | Modifying production logic to pass tests |
| **Agent 13** | Documentation & Handover | `README.md`, `walkthrough.md`, user guides, operations runbooks (`docs/runbooks/**`), final release documentation | Summarizes system features, CI/CD pipelines, and disaster recovery workflows. | Source code modifications |

---

## 3. Ephemeral Filesystem Governance (Render Free-Tier)
Because the application runtime executes on an ephemeral filesystem:
- No agent may configure file-based database architectures (e.g., SQLite, local JSON DBs).
- No agent may treat local disk folders (including `knowledge/Founder_OS/` or `.storage_buckets/`) as permanent storage in production.
- All persistent data must write directly to **Supabase PostgreSQL**, **Supabase Storage**, or encrypted **Google Drive** synchronization buckets.
