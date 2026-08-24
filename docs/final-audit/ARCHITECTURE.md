# SECTION 2 — COMPLETE ARCHITECTURE

## System Map

- **User**: Interacts via the Next.js Frontend (Command Center / Retro-Futuristic Terminal).
- **Next.js**: Serves the user interface (`apps/web`), currently heavily relying on empty states for advanced modules. Hosted on Vercel.
- **Vercel**: Next.js deployment target.
- **Supabase Auth**: JWT-based tenant authentication providing Row Level Security (RLS) contexts.
- **FastAPI**: The robust backend (`apps/api`) handling domain services, REST routes, and MCP.
- **PostgreSQL**: Hosted by Supabase, holding normalized relational data.
- **pgvector**: Stores embeddings for AI semantic retrieval (`768` dimensions for Gemini).
- **Gemini**: Core LLM (`text-embedding-004`, `gemini-1.5-pro`) handling generation, chunking, and embeddings. Simulated locally in development.
- **MCP (Model Context Protocol)**: Exposes tool mutations to the LLM. Mounted as a Streamable HTTP Server inside FastAPI (`/mcp`), not a separate service as documented.
- **Google OAuth / Drive / Calendar / Contacts**: **SIMULATED**. The implementation in `apps/api/app/integrations/google_client.py` and sync handlers uses mocked tokens (`1//0e_simulated_refresh_token_for_{user_id}_{code[:10]}`) and hardcoded sync responses (e.g., `{"synced_files_count": 14}`).
- **Background Jobs**: Powered by `apps/api/app/jobs/` using a PostgreSQL-backed queue. Handles markdown exports and simulated Google syncs.
- **File Storage**: Supabase Storage for files.
- **RAG**: Document upload -> Chunking (500 tokens / 100 overlap) -> Embedding (Gemini) -> pgvector -> Hybrid Search (cosine similarity + trigram keyword).
- **Knowledge Graph/Evidence**: `ai_conversations` link to `decisions`, `tasks`, and `achievements` to automatically trace portfolio generation back to root evidence.
- **Portfolio**: Generated dynamically by `PortfolioService` with strict zero auto-publishing and claim validation rules.
- **External AI Clients**: MCP tools exposed for external AI connections (using HMAC secured tokens).

## Data Flow
1. **Client Request**: Next.js -> FastAPI (with Supabase JWT).
2. **Auth & Security**: FastAPI validates JWT and enforces RLS in PostgreSQL.
3. **Operations**: Reads/Writes use SQLAlchemy models mapped to Supabase migrations.
4. **AI/RAG**: Document -> Chunked -> Embedded -> `pgvector` -> Hybrid Retrieval -> Gemini Context -> Zero-Publishing Output.
5. **Portability**: Database -> Background Job -> Markdown File -> `.storage_buckets` -> Expiration URL.
