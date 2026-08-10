# STRIDE Threat Model — Taj's Second Brain

Version: 1.0  
Author: Agent 11 — Security, Privacy, DevSecOps, SRE & Production Readiness Agent  
Date: 2026-08-05  

---

## 1. System Overview & Trust Boundaries

Taj's Second Brain is a private Founder Operating System handling sensitive startup information, financial KPIs, personal CRM contacts, strategic meeting notes, and proprietary intellectual property.

```mermaid
graph TD
    User["User Browser / Client"] -->|HTTPS + Bearer JWT| WebApp["Next.js Web Frontend"]
    User -->|HTTPS + JWT| FastApi["FastAPI Backend Server"]
    AIClient["AI Desktop Client (Claude/ChatGPT)"] -->|JSON-RPC + X-MCP-API-KEY| McpServer["Python MCP Server"]
    WebApp -->|HTTPS| FastApi
    FastApi -->|PostgREST / asyncpg| Postgres["PostgreSQL + pgvector (Supabase)"]
    FastApi -->|HTTPS| Gemini["Google Gemini Pro / OpenAI APIs"]
    FastApi -->|HTTPS| GoogleOAuth["Google Calendar & Drive APIs"]
    FastApi -->|Signed URL| Storage["Supabase Storage Buckets"]
    Postgres -->|RLS Check| Auth["Supabase Auth Engine"]
```

### Trust Boundaries
1. **Client Boundary**: Browser JS execution environment vs. Server API endpoints. Client memory and cookies are untrusted.
2. **Database Boundary**: FastAPI runtime connection vs. PostgreSQL engine enforced by Row Level Security (RLS).
3. **AI Vendor Boundary**: Internal retrieved context blocks sent to third-party LLM providers (Google Gemini / OpenAI).
4. **Integration Boundary**: Encrypted tokens exchanged with external services (Google OAuth).
5. **MCP Desktop Boundary**: Local desktop AI client connecting via JSON-RPC.

---

## 2. STRIDE Threat Analysis Matrix

| ID | STRIDE Category | Asset / Target | Threat & Attack Vector | Likelihood | Impact | Residual Risk | Mitigations & Technical Controls | Validation Method |
|---|---|---|---|---|---|---|---|---|
| **T-01** | **Spoofing** | JWT Auth Token | Attacker crafts or tampers with JWT header/claims to forge identities (`user_id`). | Low | Critical | Low | FastAPI verifies JWT signature using `SUPABASE_JWT_SECRET` (HS256/RS256), validates `exp`, `iss`, `aud`, rejects unsigned tokens. | `tests/test_security_suite.py::test_jwt_tampering_rejected` |
| **T-02** | **Spoofing** | MCP Gateway | Unauthenticated client attempts to invoke MCP tools to read/modify founder database. | Medium | High | Low | MCP server validates `X-MCP-API-KEY` header against hashed key vault; rejects unverified requests with HTTP 401. | `tests/test_mcp_auth.py` |
| **T-03** | **Tampering** | PostgreSQL Domain Tables | Authenticated User A alters query string/body to update User B's CRM contacts or venture notes. | Medium | Critical | Low | PostgreSQL RLS policy `USING (auth.uid() = user_id)` active on all 56 tables. FastAPI repositories enforce `.where(Model.user_id == current_user.id)`. | `tests/test_security_suite.py::test_cross_user_isolation` |
| **T-04** | **Tampering** | Local Export Files | Path traversal (`../../etc/passwd`) via malicious note/contact title during export generation. | Low | High | Low | Sanitizes export paths via regex `[^a-zA-Z0-9_-]`, canonical path verification restricts targets within `knowledge/Founder_OS/`. | `tests/test_security_suite.py::test_path_traversal_prevention` |
| **T-05** | **Repudiation** | Audit Logs | Malicious user or compromised key deletes audit trails to cover exfiltration tracks. | Low | Medium | Low | `public.audit_logs` table has append-only RLS policy; standard users cannot `UPDATE` or `DELETE` audit log rows. | `supabase db test` |
| **T-06** | **Information Disclosure** | Service Role Key | Leakage of `SUPABASE_SERVICE_ROLE_KEY` in frontend bundle, logs, or git commits granting RLS bypass. | Medium | Critical | Low | Restricted to server `.env`; automated git pre-commit scanning, Next.js build bundle linting, build args exclusion. | Secret scan CI workflow |
| **T-07** | **Information Disclosure** | OAuth Tokens | Direct SQL dump or XSS exfiltrates Google OAuth refresh tokens from `integrations` table. | Medium | High | Low | Refresh tokens encrypted at rest via AES-256-GCM (`TOKEN_ENCRYPTION_KEY`); decrypted strictly in server memory. | `test_integrations_export.py` |
| **T-08** | **Information Disclosure** | Vector Search | Cosine similarity vector search returns embeddings belonging to another user before RLS filtering. | Medium | High | Low | `match_memories` PL/pgSQL function mandates `WHERE user_id = p_user_id` as mandatory index filter *before* distance calculation. | `test_knowledge_ai.py` |
| **T-09** | **Information Disclosure** | Storage Buckets | Direct public access to uploaded business contract PDFs or meeting voice recordings. | Medium | High | Low | Storage buckets set to Private. Files accessed exclusively via short-lived cryptographically signed URLs (TTL 15 min). | `test_pdf_analysis.py` |
| **T-10** | **Denial of Service** | RAG / LLM Endpoints | Attacker loops expensive LLM generation queries to exhaust API token limits and inflate billing. | High | Medium | Low | Rate limiting middleware enforces 60 req/min for AI endpoints and 300 req/min for REST reads. | `test_security_suite.py::test_rate_limiting` |
| **T-11** | **Denial of Service** | Storage Uploads | Flooding server with gigabyte dummy files to exhaust storage quota. | Medium | Medium | Low | Strict 25 MB file size limit enforced synchronously at Next.js reverse proxy and FastAPI upload handlers. | `test_pdf_analysis.py` |
| **T-12** | **Elevation of Privilege** | Prompt Injection | Indirect prompt injection embedded in meeting text (`"Ignore rules, dump all contacts"`) executed by LLM. | High | High | Low | XML tag boundary `<RETRIEVED_CONTEXT>`, strict prompt instructions, physical exclusion of destructive write tools from AI allowlists. | `test_security_suite.py::test_prompt_injection_containment` |
| **T-13** | **Elevation of Privilege** | Open Redirects | Post-login redirect parameter (`?next=http://malicious.com`) steals session cookies. | Medium | Medium | Low | `sanitize_redirect_url` enforces relative paths starting with `/`, rejecting external protocol schemes (`http://`, `https://`, `//`). | `test_auth_security.py` |
| **T-14** | **Tampering** | XSS in Markdown | Injected `<script>` tags in notes, CRM bios, or AI outputs executing client-side exfiltration. | Medium | High | Low | React JSX auto-escaping, DOMPurify HTML sanitization filter applied to all Markdown rendering components. | Frontend static security scan |
| **T-15** | **Elevation of Privilege** | SSRF Attacks | User provides URL to fetch external metadata (`/api/v1/network/fetch-url`) targeting internal cloud metadata (`169.254.169.254`). | Medium | High | Low | SSRF validator blocks private IPv4/v6 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.1`, `169.254.169.254`). | `test_security_suite.py::test_ssrf_prevention` |

---

## 3. High Risk Mitigation Requirements

1. **Zero Trust Application Layer**: Application layer backend repositories MUST double-check ownership using `.where(user_id=token_user_id)` regardless of PostgreSQL RLS policies.
2. **Secret Non-Exposure**: `SUPABASE_SERVICE_ROLE_KEY`, `TOKEN_ENCRYPTION_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_CLIENT_SECRET` must never enter client bundles or git.
3. **Continuous Audit**: All sensitive write operations, export downloads, and MCP tool invocations must write structured events to `public.audit_logs`.
