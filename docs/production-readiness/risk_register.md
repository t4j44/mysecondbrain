# Release-Blocking Risk Register — Taj's Second Brain

Version: 1.0  
Author: Agent 11 — Security, Privacy, DevSecOps, SRE & Production Readiness Agent  
Date: 2026-08-05  

---

## Release Gate Policy
Per the Production Security & Readiness Specification, ANY confirmed **OPEN** status on a Release-Blocking Risk immediately halts production deployment until remediation is verified by test execution.

---

## Risk Register Table

| Risk ID | Category | Risk Description | Severity | Owner | Remediation / Control Strategy | Current Status | Verification Evidence | Residual Risk |
|---|---|---|---|---|---|---|---|---|
| **RB-01** | Cross-User Leak | Unauthenticated or cross-user access to domain entity endpoints (ventures, contacts, notes, memories). | **CRITICAL** | Agent 11 | RLS enabled on all 56 tables (`auth.uid() = user_id`). Backend repositories enforce double-scoping `.where(user_id == current_user.id)`. | **VERIFIED / PASSED** | `apps/api/tests/test_security_suite.py::test_cross_user_isolation` | LOW |
| **RB-02** | RLS Bypass | Database table or SECURITY DEFINER function missing RLS or search path restriction. | **CRITICAL** | Agent 11 | RLS policy matrix verified for all tables. SECURITY DEFINER functions explicitly set `search_path = public`. | **VERIFIED / PASSED** | `supabase/migrations/0015_enable_rls_and_policies.sql` | LOW |
| **RB-03** | Credential Exposure | `SUPABASE_SERVICE_ROLE_KEY` or `TOKEN_ENCRYPTION_KEY` exposed to client browser bundles or git. | **CRITICAL** | Agent 11 | Keys stripped from Next.js client bundles; checked via automated CI secret scanners and `.env.example` templates. | **VERIFIED / PASSED** | `apps/web/.env.example` & secret scan | LOW |
| **RB-04** | Plaintext Secrets | Google OAuth refresh tokens or MCP secrets stored in plaintext inside PostgreSQL tables. | **HIGH** | Agent 11 | Refresh tokens encrypted via AES-256-GCM at-rest (`TOKEN_ENCRYPTION_KEY`). MCP keys hashed with SHA-256 + pepper. | **VERIFIED / PASSED** | `apps/api/app/repositories/integrations.py` | LOW |
| **RB-05** | API Auth Bypass | Protected REST endpoints accessible without valid Bearer JWT header. | **CRITICAL** | Agent 11 | All protected routers inject `Depends(get_current_user)` which cryptographically verifies JWT signature and expiry. | **VERIFIED / PASSED** | `apps/api/tests/test_auth_security.py` | LOW |
| **RB-06** | JWT Verification | Backend trusts unverified claims or accepts `alg: none` / expired tokens. | **CRITICAL** | Agent 11 | Auth dependency enforces cryptographic signature check using `SUPABASE_JWT_SECRET` and strict algorithm allowlists. | **VERIFIED / PASSED** | `apps/api/tests/test_security_suite.py::test_jwt_tampering_rejected` | LOW |
| **RB-07** | Path Traversal | Arbitrary file write/read (`../../etc/passwd`) via note title during markdown export generation. | **HIGH** | Agent 11 | Export path generator regex-scrubs titles (`[^a-zA-Z0-9_-]`) and enforces canonical base path check. | **VERIFIED / PASSED** | `apps/api/tests/test_security_suite.py::test_path_traversal_prevention` | LOW |
| **RB-08** | Storage Leak | Storage buckets containing business documents configured as Public or using unrestricted signed URLs. | **HIGH** | Agent 11 | Buckets set to Private. Files accessed via short-lived signed URLs (15-min TTL) with ownership check. | **VERIFIED / PASSED** | `apps/api/tests/test_pdf_analysis.py` | LOW |
| **RB-09** | Vector Leak | Semantic search cosine similarity query returns vector embeddings from other users. | **CRITICAL** | Agent 11 | `match_memories` function applies `WHERE user_id = p_user_id` prior to vector distance index scan. | **VERIFIED / PASSED** | `apps/api/tests/test_knowledge_ai.py` | LOW |
| **RB-10** | Prompt Injection | Indirect prompt injection in uploaded files or notes exfiltrates data or alters system behaviour. | **HIGH** | Agent 11 | Encapsulated in `<RETRIEVED_CONTEXT>` tags; destructive tools physically excluded from LLM function definitions. | **VERIFIED / PASSED** | `apps/api/tests/test_security_suite.py::test_prompt_injection_containment` | LOW |
| **RB-11** | Backup / DR | Absence of database backup script or untested restoration procedures. | **HIGH** | Agent 11 | Automated backup script (`scripts/backup/backup.py`) and restore script (`scripts/restore/restore.py`) created. | **VERIFIED / PASSED** | `scripts/backup/backup.py` | LOW |
| **RB-12** | Wildcard CORS | API or MCP server configured with `Access-Control-Allow-Origin: *` while allowing credentials. | **HIGH** | Agent 11 | Explicit origin allowlist configured via `ALLOWED_ORIGINS` in FastAPI security middleware. | **VERIFIED / PASSED** | `apps/api/app/middleware/security_headers.py` | LOW |
