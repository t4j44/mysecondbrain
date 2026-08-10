# Master Decision Log - Taj's Second Brain

Version: 1.0  
Author: Agent 0 — Lead Orchestrator  
Status: Active Governance Log  

This log tracks authoritative architectural, operational, and sequencing decisions that impact multiple agents. Once a decision is recorded here and approved by Agent 0, all specialist agents must abide by its constraints.

---

## Decision Record Ledger

| Decision ID | Title | Date Recorded | Target Domain / Agents | Summary & Architectural Rule | Status | Authoritative Ref |
|---|---|---|---|---|---|---|
| **DEC-001** | Canonical Data Source Hierarchy | 2026-08-01 | All Agents (esp. DB & Export) | Supabase PostgreSQL is the sole canonical source of truth for all relational & vector state. Markdown files and Google Drive backups are read-only derived snapshot projections. | APPROVED | ADR-004 |
| **DEC-002** | Cryptographic JWT Identity Invariant | 2026-08-01 | Agent 3, 4, 5-10 | APIs must never accept or trust client-supplied `user_id` parameters in query, path, or body. The operational identity must be extracted solely from verified Supabase Auth JWT Bearer claims. | APPROVED | ADR-003 / Security Plan |
| **DEC-003** | Soft-Delete & Archival Preservation | 2026-08-02 | Agent 2, 3, 5-10 | Destructive SQL `DELETE` statements are strictly forbidden for primary user knowledge records (`ventures`, `projects`, `people`, `memories`, `ideas`, `documents`). Records must use soft deletion or archival transitions. | APPROVED | ADR-011 |
| **DEC-004** | AI Provider Abstraction Invariant | 2026-08-02 | Agent 8, 9 | All LLM generation and vector embedding calls must execute through `BaseLLMProvider` (`GeminiLLMProvider` / `OpenAILLMProvider`). Direct imports of vendor SDKs within route handlers are prohibited. | APPROVED | ADR-006 |
| **DEC-005** | Read-Only & Confined MCP Default | 2026-08-02 | Agent 10, 11 | By default, all external MCP tool calls operate in strict read-only mode. Write-capable tools (content drafting) must produce internal staged drafts and cannot externally publish or delete canonical database records. | APPROVED | ADR-010 / PRD |
| **DEC-006** | Single Render Service for REST & MCP | 2026-08-05 | Agent 3, 10, 11 | To satisfy free-tier Render container constraints, the entire Python backend deploys as a single Web Service. Agent 10 mounts the Streamable HTTP MCP server at `/mcp` inside Agent 3's FastAPI ASGI runtime. REST and MCP share domain services but enforce strictly separate auth, rate-limiting, and audit boundaries. | APPROVED | ADR-013 |
| **DEC-007** | Ephemeral Filesystem Rule | 2026-08-05 | Agent 3, 7, 8, 11 | Because Render web containers have ephemeral disk storage, no features may depend on persistent local disk writes. Local scratch directories are solely for temporary in-flight processing before upload to Supabase Storage or Google Drive. | APPROVED | ADR-013 / TRD |
| **DEC-008** | Evidence-Based Completion Gate | 2026-08-05 | All Specialist Agents | No agent may claim task completion without verified existing files, demonstrable functional behavior, executed test evidence, and an honest completion report outlining passed/failed assertions. | APPROVED | Handoff Section 5 |
| **DEC-009** | Final Production Sign-Off | 2026-08-06 | Final Orchestrator | Full-stack A-Z integration verified. 56 backend test cases passed, Next.js frontend build succeeded cleanly. Decommissioned standalone mcp-server. System approved for immediate production release. | APPROVED | Production Sign-off |
