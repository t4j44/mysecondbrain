# Master Blocker & Risk Log - Taj's Second Brain

Version: 2.0  
Author: Final Integration Orchestration System  
Last Reviewed: 2026-08-06  
Status: ALL BLOCKERS RESOLVED AND CLOSED  

---

## 1. Active Blocker Ledger

| Blocker ID | Severity | Affected Domain / Path | Assigned Owner | Root Cause / Description | Action Required / Resolution Gate | Status |
|---|---|---|---|---|---|---|
| **BLK-001** | **CRITICAL** | `apps/api/app/mcp/` | Orchestrator | Refactored MCP into `apps/api/app/mcp` and mounted at `/mcp` inside FastAPI per ADR-013. Standalone `apps/mcp-server` deleted. | Unified single Render Web Service container operational and tested. | **CLOSED / RESOLVED** |
| **BLK-002** | **HIGH** | `apps/web/` | Orchestrator | Designated `apps/web/` as canonical frontend. Integrated AI Chat area into `apps/web`. | Next.js production build passing cleanly. | **CLOSED / RESOLVED** |
| **BLK-003** | **MEDIUM** | `apps/api/app/api/v1/endpoints/` | Orchestrator | De-duplicated PDF router to `apps/api/app/api/v1/endpoints/pdf_analysis.py` and deleted dead directory. | All endpoints covered by passing test suite. | **CLOSED / RESOLVED** |
| **BLK-004** | **HIGH** | Ephemeral Filesystem | Orchestrator | Verified all persistent writes target Supabase PostgreSQL or Google Drive. | Render ephemeral FS compliance verified. | **CLOSED / RESOLVED** |

---

## 2. Risk Register

| Risk ID | Risk Title | Probability | Impact | Mitigation Strategy | Owner | Status |
|---|---|---|---|---|---|---|
| **RSK-001** | Render Free-Tier Cold Start Latency | High | Medium | Implemented terminal streaming UI & skeleton loaders in Next.js frontend. | Agent 4, 11 | **MITIGATED** |
| **RSK-002** | OOM during Vector Embedding Generation | Medium | High | Async batching implemented for Gemini embedding requests. | Agent 8 | **MITIGATED** |
| **RSK-003** | Silent Contract Drift between REST and MCP | Medium | High | Shared repository layer (`app/repositories/`) consumed by both REST and MCP. | Agent 1, 10 | **MITIGATED** |
| **RSK-004** | Google OAuth Refresh Token Exfiltration | Low | Critical | AES-256 field-level token encryption enforced in DB repositories. | Agent 3, 7, 11 | **MITIGATED** |
