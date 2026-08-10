# PostgreSQL Row Level Security (RLS) Policy Reference Matrix — Taj's Second Brain

Version: 1.0  
Author: Agent 11 — Security, Privacy, DevSecOps, SRE & Production Readiness Agent  
Date: 2026-08-05  

---

## 1. RLS Policy Guiding Principle

Every table in `public` schema activates Row Level Security.
Default Policy:
```sql
ALTER TABLE public.<table_name> ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Universal ownership isolation" ON public.<table_name>
    FOR ALL USING (user_id = auth.uid());
```

---

## 2. Table Policy Matrix

| Schema | Table Name | RLS Active | SELECT Policy | INSERT Policy | UPDATE Policy | DELETE Policy | Service Role Bypass Used | Browser Exposure Allowed | Test Status |
|---|---|---|---|---|---|---|---|---|---|
| `public` | `profiles` | YES | `id = auth.uid()` | `id = auth.uid()` | `id = auth.uid()` | `id = auth.uid()` | NO | YES | PASSED |
| `public` | `ventures` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `projects` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `tasks` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `people` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `interactions` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `memories` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `memory_embeddings` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO (via search func) | NO | PASSED |
| `public` | `ideas` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `decisions` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `documents` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `document_chunks` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | NO | PASSED |
| `public` | `kpi_metrics` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `portfolio_achievements`| YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `content_drafts` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `ai_conversations` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `ai_messages` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |
| `public` | `integrations` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | NO (tokens hidden) | PASSED |
| `public` | `background_jobs` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | YES (Runner) | NO | PASSED |
| `public` | `audit_logs` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | NONE (Immutable) | NONE (Immutable) | NO | YES (Read only) | PASSED |
| `public` | `mcp_clients` | YES | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | NO | YES | PASSED |

---

## 3. SECURITY DEFINER Functions Audit

All PL/pgSQL database functions created with `SECURITY DEFINER` (such as `match_memories` and `match_documents`) must be hardened as follows:
1. **Explicit Search Path**: Must set `SET search_path = public`.
2. **Mandatory User ID Verification**: Must accept `p_user_id UUID` and enforce `WHERE user_id = p_user_id` as the primary filtering condition.
3. **No Dynamic SQL String Interpolation**: All SQL operations use explicit parametrized parameters to prevent SQL injection.
