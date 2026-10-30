# MCP architecture — V1.5

The live application entrypoint is `apps/api/app/main.py`. It mounts the official
SDK transport from `app/mcp/server.py` after REST and discovery routes. Domain tools
reuse application services, the canonical Supabase migrations and existing pgvector
indexing. The separate historical `apps/mcp-server` directory is not deployed.

OAuth routes use SDK registration/authorization/token handlers and a database-backed
provider. The adapter enforces exact resource binding in token requests, verifies
hashed client secrets and supplies client IDs for standard Basic authentication.
Consent is a Supabase-authenticated UI using an expiring one-use pending request;
its secret is carried in a URL fragment then sessionStorage, not a server query log.
Authorization codes and opaque tokens have SHA-256 lookup digests. Refresh rotation
and revocation are durable PostgreSQL transactions. Legacy bearer keys are verified
through the existing credential repository. Vault access uses narrowly scoped server
sessions; domain calls use the verified owner's RLS claims.

Session finalization serializes per owner, preserves the submitted summary separately
from derived data, and records a context event with source/time/provenance links.
Equivalent stable session references replay the existing receipt. Erased sessions
cannot be resurrected through a replay. Recommendations and retrieval revalidate
owner, deletion, privacy and index fingerprints before exposing sources.

The free-redacted Gemini provider is unchanged. OAuth itself neither needs paid AI
nor passes through a Supabase/Google credential. See client setup for the DCR-only
compatibility boundary and staging acceptance; SDK-level tests do not prove live
ChatGPT/Claude interoperability.
