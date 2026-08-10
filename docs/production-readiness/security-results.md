# Security Audit and Data Protection Report

**Date**: August 6, 2026  
**Repository**: `E:\second brain`  
**Security Target**: Zero-Trust Authorization, RLS Isolation, JWT Verification, MCP Key Cryptography

---

## 1. Security Architecture & System Invariants

### 1. Zero Trust Identity Extraction
- Client requests MUST NOT provide a trusted `user_id` query parameter or body payload to bypass identity checks.
- All request identities are extracted from verified Supabase JWT Bearer claims (`sub` UUID claim) in `app/dependencies/auth.py`.
- Automated test `tests/test_security_rls.py` verifies that forged token signatures and mismatched user UUID claims are rejected with `401 Unauthorized`.

### 2. Supabase Row Level Security (RLS) Policies
- Database tables (`profiles`, `people`, `organizations`, `interactions`, `meetings`, `memories`, `knowledge_documents`, `ideas`, `kpis`, `content_drafts`, `achievements`, `mcp_credentials`) enforce `auth.uid() = user_id`.
- Inter-tenant data leakage tests in `test_security_rls.py` confirm 0 cross-tenant data visibility.

### 3. MCP API Key Security & Capability Scoping (ADR-013)
- MCP credentials generated via `POST /api/v1/mcp/credentials` produce a secure key string formatted as `sb_mcp_<token_urlsafe>`.
- Plaintext API keys are NEVER stored in database columns. Only `key_prefix` (first 12 chars), `salt` (16-byte cryptographically secure random string), and `key_hash` (SHA-256 HMAC of salt + plaintext_key) are stored.
- Authentication checks in `app/mcp/security.py` execute constant-time `hmac.compare_digest` comparisons to eliminate timing attack side-channels.
- Granular capability scopes (`mcp:people:read`, `mcp:memory:read`, `mcp:projects:read`, `mcp:tasks:read`, `mcp:relationships:read`, `mcp:calendar:read`, `mcp:content:draft`) prevent over-privileged tool invocations.

### 4. Ephemeral Filesystem Isolation
- Local temporary files (PDF processing uploads, temporary exports) target transient paths under `/tmp` or scratch directories.
- Permanent state is persisted strictly to Supabase PostgreSQL or Google Drive API.

---

## 2. Security Test Audit Suite Results

| Security Check | Tested File / Endpoint | Verification Mechanism | Audit Result |
| :--- | :--- | :--- | :--- |
| **JWT Verification** | `app/dependencies/auth.py` | Validates JWT Secret, expiration, signature | **PASSED** |
| **Inter-Tenant RLS** | `tests/test_security_rls.py` | Query attempts across distinct user UUIDs | **PASSED** |
| **MCP Secret Storage** | `app/repositories/mcp.py` | Confirms salt + SHA-256 key hashing | **PASSED** |
| **MCP Timing Defenses** | `app/repositories/mcp.py` | `hmac.compare_digest` constant-time comparison | **PASSED** |
| **Scope Enforcement** | `app/mcp/security.py` | Rejecting ungranted capabilities with 403 | **PASSED** |
| **Rate Limiting** | `app/middleware/rate_limiting.py` | Sliding window throttling on strict endpoints | **PASSED** |
