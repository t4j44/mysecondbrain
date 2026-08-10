# Architecture Decision Records (ADRs) - Taj's Second Brain

Version: 1.0  
Status: Approved & Implementation-Ready  
Author: Agent 1 — Architecture and Contracts Agent  
Approved by: Agent 0 — Lead Orchestrator  

---

## ADR-001: Monorepo Structure

### Status
Accepted

### Context
Taj's Second Brain requires a synchronized development ecosystem spanning a web front-end, a backend API service, an MCP server for external LLM clients, shared TypeScript/Pydantic schemas, UI styling tokens, AI prompts, and database migrations. Coordinating multiple repositories risks schema drift, duplicated authentication logic, and broken integration boundaries across agents.

### Decision
Adopt a unified workspace monorepo structure managed via pnpm workspaces (for TypeScript/JS packages) and standard Python virtual environments/UV workspaces (for backend services).
The folder hierarchy will strictly separate application entry points (`apps/`), modular shared packages (`packages/`), persistent local knowledge archives (`knowledge/`), database infrastructure (`supabase/`), architecture documentation (`docs/`), and end-to-end quality validation (`tests/`).

```text
apps/
  web/          # Next.js App Router frontend
  api/          # Python FastAPI backend service
  mcp-server/   # Python MCP server standalone entry point
packages/
  ui/           # Shared Tailwind/Shadcn/Framer UI components & themes
  shared-types/ # JSON schemas & TypeScript interface definitions
  prompts/      # Versioned AI prompt templates and system instructions
  database/     # DB interaction utilities, ORM models, migration helpers
  config/       # Centralized ESLint, Tsconfig, Tailwind, and Python linter rules
supabase/
  migrations/   # SQL migrations for Postgres schemas, RLS, pgvector, functions
  seed/         # Seed data for testing and development environments
  tests/        # pgTAP and pg_prove database & RLS validation scripts
knowledge/      # User-owned canonical markdown files (git-ignored or separate repository)
  Founder_OS/   # Root folder for portable user knowledge exports
docs/           # Comprehensive architecture, API, DB, and security specs
tests/          # System-wide E2E and cross-service integration test suites
```

### Alternatives Considered
1. **Multi-Repository Setup (Separate Frontend, Backend, and MCP repos):** Rejected due to complex cross-repository CI/CD orchestration and schema synchronization friction across parallel agent teams.
2. **Single Unstructured Monolithic Application:** Rejected because blending Next.js API routes with complex Python AI processing and pgvector interactions forces unsupported serverless execution patterns and creates tight coupling.

### Consequences
- **Positive:** Clear file ownership boundaries enable multi-agent parallel development without cross-agent git conflicts. Shared schemas guarantee API contract adherence between Next.js and FastAPI.
- **Negative:** Require dual build systems (Node.js/pnpm for frontend/UI, Python/UV for API/MCP) within a single root container.

### Security Implications
- Secret `.env` files must be clearly decoupled per app (`apps/web/.env.local`, `apps/api/.env`, `apps/mcp-server/.env`).
- Client-side code in `apps/web` is cryptographically and physically restricted from importing server-only Python modules or private credentials in `apps/api` and `apps/mcp-server`.

---

## ADR-002: FastAPI Database Access Strategy

### Status
Accepted

### Context
The Python FastAPI backend needs high-performance, type-safe access to Supabase PostgreSQL, supporting advanced pgvector cosine similarity searches, complex transactions, relational JOINs, and strict Row Level Security (RLS) enforcement. We evaluated using the raw Supabase Python SDK versus SQLAlchemy (with AsyncIO and asyncpg).

### Decision
Adopt **SQLAlchemy 2.0 (AsyncIO with asyncpg)** as the primary relational persistence and vector querying framework for FastAPI, supplemented by **Supabase Python SDK** exclusively for Authentication verification, Storage bucket operations, and edge administrative tasks.

### Alternatives Considered
1. **Supabase Python SDK Only:** Rejected because PostgREST queries via the SDK lack robust native pythonic abstraction for dynamic complex SQL transactions, high-throughput batch vector embedding insertions, and complex polymorphic table JOINs required by our memory layer and RAG pipeline.
2. **Raw SQL with asyncpg:** Rejected due to lack of migration autogeneration capabilities, verbose boilerplate for 31+ tables, and higher risk of SQL injection in dynamic analytical queries.
3. **SQLAlchemy Only (No Supabase SDK):** Rejected because reinventing signed URL generation, bucket management, and Auth token verifications would duplicate core Supabase platform features.

### Consequences
- **Positive:** SQLAlchemy 2.0 provides production-ready Repository pattern abstractions, native integration with `pgvector-python`, explicit transaction control, and seamless integration with Pydantic via `orm_mode`.
- **Negative:** Requires maintaining SQLAlchemy declarative models alongside Supabase SQL migration files. To mitigate schema drift, SQL migrations in `supabase/migrations/` serve as the absolute database truth.

### Security Implications
- Database connection pools in FastAPI MUST authenticate using a specific application database role or dynamically set the PostgreSQL configuration session variable (`SET LOCAL current_setting('request.jwt.claim.sub') = user_id;` or `SET LOCAL role = 'authenticated'; SET LOCAL request.jwt.claims = '<json_claims>';`) within every transactional session to ensure PostgreSQL Row Level Security (RLS) executes flawlessly even over direct TCP pool connections.
- Direct repository queries must ALSO explicitly append `.where(Model.user_id == verified_user_id)` as defense-in-depth against configuration missteps.

---

## ADR-003: Authentication and JWT Validation

### Status
Accepted

### Context
Taj’s Second Brain operates as a high-security personal OS. Authentication across the Next.js frontend, FastAPI backend, and standalone MCP server must guarantee session integrity, support email/password and passwordless magic links, protect against XSS/CSRF, and prevent unauthorized horizontal authorization bypasses.

### Decision
Adopt **Supabase Auth (GoTrue)** issuing standard cryptographic JSON Web Tokens (JWT). 
- The Next.js frontend uses `@supabase/ssr` to manage secure, HTTP-only, SameSite=Lax cookies for browser sessions and server component rendering.
- The FastAPI backend implements an explicit OAuth2 Bearer Dependency (`get_current_user`) that extracts the JWT from the `Authorization: Bearer <token>` header, verifies the RSA/HS256 signature locally against the Supabase Project JWT Secret/Public JWKS endpoint without performing round-trip network calls per request, and extracts the verified `sub` (User ID).

### Alternatives Considered
1. **Custom OAuth / Auth0 / NextAuth (Auth.js):** Rejected to prevent third-party authentication dependency lock-in and because Supabase Auth natively couples with PostgreSQL Auth schema and RLS policies.
2. **Session Cookie storage only without API Bearer Tokens:** Rejected because non-browser clients (MCP server, CLI backup daemons, external automated cron jobs) require stateless API bearer token authentication.

### Consequences
- **Positive:** Zero round-trip authentication latency on backend API execution. Unlocks native integration with PostgreSQL `auth.users`. Supports instant token revocation tracking via refresh token expiry.
- **Negative:** Expired access tokens require automated client-side silent interception and reissue using the long-lived HTTP-only refresh token cookie before retried API calls.

### Security Implications
- **Never Trust Client-Supplied User IDs:** Under zero circumstances will any API endpoint accept `user_id` in a request body, query parameter, or route path to authorize actions. The operative `user_id` is derived strictly from the cryptographic signature of the verified JWT.
- Tokens must never be stored in browser `localStorage` or `sessionStorage` due to XSS vulnerability risks; `@supabase/ssr` cookie storage is mandatory.

---

## ADR-004: Canonical Data Source

### Status
Accepted

### Context
The system spans structured PostgreSQL relational tables, vector embedding indexes, object storage files, local Markdown export directories (`knowledge/Founder_OS/`), and remote Google Drive cloud backups. Without a clear hierarchy, concurrent updates between AI background processing, UI manual edits, and backup synchronization could corrupt or lose historical knowledge.

### Decision
Establish **Supabase PostgreSQL** (`public` schema tables) as the single **Canonical Source of Truth** for all active structured relationship metadata, entity attributes, interaction logs, tasks, KPIs, and AI conversation histories.
- **Supabase Storage:** Canonical source for binary file attachments, original document PDFs, and avatar graphics.
- **Markdown Repository (`knowledge/Founder_OS/`) and Google Drive Backups:** Defined as **Derived Snapshot Projections**. They are read-only backup representations generated deterministically from the canonical PostgreSQL database to guarantee user ownership and offline data portability.

### Alternatives Considered
1. **Local Markdown Files as Canonical Source (Obsidian/Logseq architecture):** Rejected because file system locks and plain text files cannot support high-concurrency multi-user transactions, sub-second complex relational filtering (e.g., finding all tasks linked to a specific CRM mentor across multiple ventures), or integrated pgvector similarity joins.
2. **Bidirectional Two-Way Sync between Markdown files and DB:** Rejected for Phase 1-6 due to massive merge-conflict complexity and race conditions between automated AI enrichment and manual text editing.

### Consequences
- **Positive:** Architectural simplicity. Database transactions guarantee ACID consistency. Backup recovery is straightforward: if the DB is destroyed, the restoration engine ingests the structured Markdown snapshots back into PostgreSQL.
- **Negative:** Users desiring offline file edits must understand that direct edits to exported `.md` files will be overwritten on the next sync cycle unless explicitly ingested via an intentional restore/import utility.

### Security Implications
- Derived Markdown snapshots written to the filesystem must undergo file-permission hardening (`0700` directory access on Unix/Windows equivalent ACLs) so unprivileged system processes cannot harvest exported founder intelligence.

---

## ADR-005: Markdown Export Strategy

### Status
Accepted

### Context
To enforce "Ownership First" and eliminate vendor lock-in, the system must export every database entity into a human-readable, universally structured Markdown repository that can be opened in Obsidian, VS Code, or any plain text viewer.

### Decision
Adopt a **Structured Frontmatter-Enhanced Markdown Pattern**. Every record exported to `knowledge/Founder_OS/` will consist of:
1. **YAML Frontmatter Block:** Storing immutable structural identifiers (e.g., `id: uuid`, `type: person`, `slug`, `created_at`, `updated_at`, and relational link UUIDs/slugs).
2. **Markdown Body:** Storing the clean human-readable titles, notes, summaries, transcription logs, key takeaways, and markdown tables of related records.

```text
knowledge/Founder_OS/
  People/
    yousuf-imran-[uuid-trunc].md
  Ventures/
    justor-ai/
      venture_overview.md
      Projects/
        legal-engine.md
      Tasks/
      Decisions/
  Meetings/
  Ideas/
  Achievements/
  Content/
  Weekly Reviews/
```

### Alternatives Considered
1. **Pure JSON Export:** Rejected because raw JSON files lack natural human readability, comfortable reading ergonomics, and compatibility with personal knowledge apps like Obsidian.
2. **Plain Text without Frontmatter:** Rejected because without structured UUIDs and timestamp attributes in YAML header blocks, reliable automated database restoration and relational linking would become impossible.

### Consequences
- **Positive:** Unites human editorial readability with programmatic parser consistency. Enables guaranteed 1:1 database rebuilds directly from backup folder structures.
- **Negative:** File generation engine must safely sanitize file system paths and handle illegal filename characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`).

### Security Implications
- File export jobs must run in background isolated execution contexts and verify that the target directory stays strictly bounded inside the designated user workspace, guarding against Path Traversal vulnerabilities (`../../etc/passwd` or overwrite attacks).

---

## ADR-006: AI Provider Abstraction

### Status
Accepted

### Context
Taj's Second Brain leverages LLMs for semantic retrieval, reasoning, drafting, and analysis. Relying exclusively on hardcoded vendor SDK calls (e.g., importing `google-genai` or `openai` throughout dozens of FastAPI route handlers) introduces architectural fragility, API vendor lock-in, and downtime vulnerability during vendor outages.

### Decision
Implement an explicit, decoupled **AI Provider Abstraction Layer (`BaseLLMProvider`)** within the FastAPI backend (`backend/app/ai/provider.py`). 
- **Primary Provider:** `GeminiLLMProvider` (utilizing Gemini Pro 1.5 / Flash models for generation and `text-embedding-004` for vectors).
- **Optional Fallback Provider:** `OpenAILLMProvider` (utilizing GPT-4o / embeddings-3-small).
All domain services (CRM, Idea Vault, Weekly Review, RAG engine) interact solely with the standardized interface methods:
  - `generate_text(prompt, system_instruction, max_tokens, temperature, tools) -> LLMResponse`
  - `generate_stream(prompt, system_instruction, ...) -> AsyncIterator[StreamDelta]`
  - `generate_embedding(text_chunks: List[str]) -> List[List[float]]`

### Alternatives Considered
1. **Direct Vendor SDK Usage:** Rejected due to tight coupling and maintenance overhead if primary API models are deprecated or pricing structures alter.
2. **LangChain / LlamaIndex Monolithic Frameworks:** Rejected because heavy external wrappers obfuscate error handling, introduce massive dependency chains, impede strict custom prompt-injection defenses, and complicate direct streaming protocol control.

### Consequences
- **Positive:** Complete control over prompt assembly, token budget tracking, unified automatic retry backoff mechanics, error translation, and seamless switching between Gemini and OpenAI via environment variable toggles.
- **Negative:** Requires custom implementation of standard tool definitions and structured output parsing within our lightweight provider wrapper.

### Security Implications
- All provider driver layers must inspect and sanitize prompt assembly inputs to prevent data exfiltration via malicious vendor logging or prompt-injection exploitation. Provider usage metadata (token counts, latency) is recorded in audit logs, but full prompt contents are strictly restricted from general system debug logs.

---

## ADR-007: Embedding and Vector Search Strategy

### Status
Accepted

### Context
Semantic knowledge search requires converting founder experiences, meeting transcripts, ideas, and document attachments into high-dimensional numerical vectors, then executing similarity rankings against user queries with ultra-low latency while preserving strict user isolation.

### Decision
Adopt **Supabase PostgreSQL with the `pgvector` extension** as the vector vector store, utilizing an **Inverted File with Flat Compression (IVFFlat)** index or **Hierarchical Navigable Small World (HNSW)** index on a dedicated `public.memory_embeddings` table.
- **Embedding Model:** Google Gemini `text-embedding-004` (configurable vector dimension size, default **768 dimensions**).
- **Search Paradigm:** **Hybrid Search** combining pgvector cosine similarity (`<=>`) with native PostgreSQL Full-Text Search (FTS `to_tsvector` and trigram matching via `pg_trgm`) to capture both semantic conceptual meaning and precise keyword/proper-name matching (e.g., exact startup brand names or obscure acronyms).

### Alternatives Considered
1. **Dedicated Vector DBs (Pinecone, Weaviate, Qdrant, Milvus):** Rejected to prevent data fragmentation across independent SaaS cloud boundaries, eliminate external vector database sync failures, and avoid complex distributed multi-tenant authorization enforcement.
2. **Dense Vector Similarity Search Only (No Keyword FTS):** Rejected because pure neural embeddings frequently fail to match exact acronyms, novel founder venture slugs, or specific proper nouns that do not appear in generic training distributions.

### Consequences
- **Positive:** Zero data egress out of our primary Supabase PostgreSQL boundary. Single atomic database backups cover both relational entities and neural memory vectors. RLS applies directly to vector similarity filtering.
- **Negative:** Requires careful PostgreSQL tuning of work memory and vector index lists as embedding rows scale beyond 100,000 chunks.

### Security Implications
- **Strict User RLS Pre-Filtering:** Vector search SQL queries must never compute similarity scores across global embeddings before filtering. Custom PL/pgSQL retrieval functions (`match_memories`) MUST enforce `WHERE user_id = p_user_id` as the leading filter index before calculating vector distance approximations to eliminate cross-user vector memory leakage.

---

## ADR-008: Background Job Strategy

### Status
Accepted

### Context
Ingesting multi-page document attachments, generating vector embeddings, executing Google Drive backups, generating weekly AI analytical reviews, and running bulk Markdown exports are computationally heavy, asynchronous tasks. Running them synchronously within HTTP request-response cycles causes rate limits, timeout exceptions, and degraded interface reactivity.

### Decision
For **Phase 1 through Phase 5**, adopt a **Database-Backed Job Queue Strategy** utilizing persistent Supabase PostgreSQL tables (`sync_jobs`, `export_jobs`, `document_processing_jobs`) orchestrated via **FastAPI Background Tasks** and asyncio event loop execution.
- Every asynchronous request immediately persists a job record with status `pending` and returns a `job_id` to the client (HTTP 202 Accepted).
- The FastAPI worker executes the job in the background, updating table status to `processing`, `completed`, or `failed` (with retry attempt tracking and detailed error logging).

### Alternatives Considered
1. **Celery with Redis / RabbitMQ Broker:** Rejected for initial deployment phases because provisioning, hosting, and securing separate Redis/RabbitMQ infrastructure instances adds unwarranted operational cost and maintenance complexity for a single-user founder operating system.
2. **In-Memory FastAPI Background Tasks Only (No Database State):** Rejected because process restarts or server crashes would silently abandon in-flight jobs without retry capability or auditability.

### Consequences
- **Positive:** Zero additional cloud infrastructure costs. Total visibility into background processing status directly via SQL queries and standard API status endpoints (`GET /api/v1/integrations/sync-jobs/{id}`). Provides an effortless evolutionary migration path: if job volume requires dedicated worker processes in Phase 7, a standard Python background daemon can poll the same PostgreSQL tables without altering API contracts.
- **Negative:** Requires efficient DB concurrency controls (`FOR UPDATE SKIP LOCKED`) if scaling to multiple concurrent backend container replicas.

### Security Implications
- Background tasks executing outside active HTTP request contexts cannot rely on incoming JWT request headers for RLS authentication. The background execution runner must explicitly bind the job's authoring `user_id` from the secure job database record and pass it into repository methods and explicit session role variables.

---

## ADR-009: Google OAuth Token Storage

### Status
Accepted

### Context
To sync tasks with Google Calendar and back up markdown archives to Google Drive, the backend must authenticate with Google APIs on behalf of Taj using OAuth2 Authorization Code flow with offline access. The resulting refresh tokens grant perpetual administrative read/write access to user files and schedules and represent high-value targets for compromise.

### Decision
Store Google OAuth access and refresh tokens inside a dedicated database table (`public.integrations`), **At-Rest Field-Level Encryption using Authenticated Symmetric Cryptography (AES-256-GCM / Fernet)**.
- The 256-bit encryption master key (`TOKEN_ENCRYPTION_KEY`) is stored strictly as an environment hardware deployment secret within the FastAPI service environment; it is never committed to database migrations, source code repositories, or log outputs.
- Tokens are decrypted strictly in real-time within server memory during active API execution calls to Google servers and wiped immediately after execution.

### Alternatives Considered
1. **Unencrypted Storage in PostgreSQL DB:** Rejected due to unacceptable risk; a database read vulnerability or backup leak would grant attackers total control over the founder's personal Google Drive and Calendar.
2. **Client-Side Token Storage in Browser:** Rejected because automated background cron jobs and server-side backup engines require access to refresh tokens when the browser is offline and closed.

### Consequences
- **Positive:** Robust defense-in-depth against data breach exfiltration. Complies with zero-trust security standards.
- **Negative:** Loss or rotation of the server `TOKEN_ENCRYPTION_KEY` without careful re-encryption migration will permanently invalidate all existing Google OAuth connections, forcing re-authentication.

### Security Implications
- OAuth application configuration must enforce **Minimum Necessary Scopes** (`https://www.googleapis.com/auth/drive.file` to access ONLY files created by the application itself or explicit app folder, and `https://www.googleapis.com/auth/calendar.events` for specific task calendars). Never request global full-drive access (`drive` scope).

---

## ADR-010: MCP Service Access Strategy

### Status
Accepted

### Context
The Model Context Protocol (MCP) server allows external AI desktop assistants (Claude Desktop, ChatGPT, Claude Code, Gemini CLI) to invoke tools that query Taj's Second Brain memory, projects, CRM contacts, and content drafting engines. We must decide whether the MCP server directly queries PostgreSQL tables or interacts through intermediary service layers.

### Decision
The MCP Server (`apps/mcp-server/` or `backend/mcp_server.py`) will function as an authenticated client that executes actions **Strictly via Shared Domain Service Repositories and Internal Business Logic Layers**, never executing raw untyped SQL queries directly against database tables.
- All MCP tool executions require a verified cryptographic access credential (`X-MCP-API-KEY` tied to an authenticated user session or dedicated long-lived personal access token).
- By default, all MCP tools operate in **Strict Read-Only Mode** (`search_people`, `search_memory`, `get_projects`). Any write-capable tools (`generate_linkedin_post`, `create_task`) require explicit structural input validation and must return staged drafts or request human confirmation flags rather than executing destructive modifications directly.

### Alternatives Considered
1. **Direct Database Raw SQL Queries from MCP Tools:** Rejected because bypassing core backend validation, RLS encapsulation, and business log logging risks schema corruption, unauthorized security bypasses, and split-brain business logic.
2. **HTTP REST API Calls from MCP Server to FastAPI over localhost:** Acceptable alternative, but leveraging shared internal domain packages within the Python monorepo workspace (`packages/database`, `backend/app/services`) reduces localhost network parsing overhead while enforcing identical security and validation rules.

### Consequences
- **Positive:** Single unified validation gate. Audit logs uniformly record MCP actions alongside Next.js web application interactions. Prevents accidental deletion of founder records via hallucinations from external LLM clients.
- **Negative:** Changes to underlying domain service layers require running testing pipelines against both the REST API and the MCP server suite.

### Security Implications
- MCP Server credentials must support immediate revocation via dashboard configuration (`/settings/integrations`). Audit logs must tag all modifications originating from MCP tools with an explicit source metadata flag (`source: "mcp_client"`).

---

## ADR-011: Soft Delete and Archival Strategy

### Status
Accepted

### Context
A core goal of Taj's Second Brain is to build a "lifelong personal knowledge system" where accumulated intelligence grows over time. Standard cascading hard deletions (e.g., deleting a project deleting all historical tasks, meetings, and memories linked to it) destroys historical context and breaks AI conversational memory retrieval.

### Decision
Implement an explicit **Soft Delete, Archival, and Relationship Detachment Strategy** across all primary knowledge entities.
1. **Hard Delete Restriction:** Destructive database `DELETE` statements are prohibited for core intellectual property records (`ventures`, `projects`, `people`, `memories`, `ideas`, `decisions`, `documents`).
2. **Soft Deletion & Archival:** Primary tables incorporate a `status` state field (`active`, `archived`, `deleted`) or `deleted_at TIMESTAMPTZ` nullable column. Deleting an entity via UI transitions its state to `archived` or sets `deleted_at = NOW()`.
3. **Relationship Detachment:** Foreign key relationships from immutable history logs (such as `interactions`, `memories`, `task_comments`) to parent containers (`ventures`, `projects`, `people`) must use `ON DELETE SET NULL` or link to the archived parent entity rather than executing destructive cascading purges (`ON DELETE CASCADE`).

### Alternatives Considered
1. **Standard Relational Cascading Hard Deletion (`ON DELETE CASCADE` everywhere):** Rejected because deleting a closed venture would catastrophically eradicate all founder memories, mentor interaction notes, and career portfolio case studies tied to that startup journey.
2. **Append-Only Immutable Event Store (Event Sourcing):** Rejected due to excessive implementation complexity and performance overhead for straightforward CRUD operations and SQL tabular queries.

### Consequences
- **Positive:** Preserves permanent institutional memory for future AI coaching and pattern analysis. Protects against accidental user deletions or prompt injection tool executions. Enables recovery from trash bins.
- **Negative:** All operational list and dashboard API queries must explicitly filter active records (`WHERE deleted_at IS NULL AND status != 'archived'`), requiring careful repository query hygiene and indexing on `(user_id, deleted_at)`.

### Security Implications
- If a user triggers an explicit statutory or GDPR-style **Full Account Destruction & Scrub Command**, a dedicated secure system purge routine will override soft deletes and physically wipe all PostgreSQL records, vector embeddings, cloud files, and Drive snapshots associated with the user ID.

---

## ADR-012: AI Streaming Protocol

### Status
Accepted

### Context
Interactive features like the "AI Founder Assistant", relationship intelligence summarizer, and content generation engine require real-time text streaming from Gemini/OpenAI models to the Next.js UI to prevent perceived UI freezes during multi-second LLM generation cycles.

### Decision
Adopt **Server-Sent Events (SSE)** adhering to the structured **Vercel AI SDK Data-Stream Protocol specification**, streamed directly from FastAPI asynchronous generator route handlers (`StreamingResponse(media_type="text/event-stream")`) to React Next.js client consumers.
The protocol streams explicit event type packets:
- `0:"string"\n` -> Text message delta chunk
- `e:{"type":"citation", "id":"...", "title":"..."}\n` -> Grounded citation source reference
- `d:{"finishReason":"stop", "usage":{"promptTokens":25, "completionTokens":120}}\n` -> Completion and billing usage metrics
- `3:"Error message detail"\n` -> Controlled streaming exception alert

### Alternatives Considered
1. **WebSockets:** Rejected because persistent duplex socket connections increase deployment hosting overhead, complicate stateful reconnection logic through serverless edge proxies, and are unnecessary for request-response LLM generation streams.
2. **Unstructured Chunked Plaintext Streaming:** Rejected because transmitting raw text blocks without structured metadata frames prevents simultaneously sending real-time RAG grounding citation link overlays, usage token counts, or interactive tool-call triggers during active text generation.

### Consequences
- **Positive:** Native out-of-the-box UI state synchronization with Next.js App Router hooks (`useChat`, `useCompletion`). Transparently traverses standard firewalls, HTTP reverse proxies, and Vercel edge infrastructure.
- **Negative:** Requires rigorous custom generator formatting formatting handlers inside FastAPI to format Python async yield streams into precise Vercel Data-Stream syntax frames.

### Security Implications
- Streaming endpoints require prior authentication token verification before initiating HTTP connection upgrades. If an authentication session expires mid-stream, the server cleanly aborts transmission with a structured error stream event (`3:"Unauthorized session termination"\n`).

---

## ADR-013: Single Render Service for FastAPI and MCP

### Status
Accepted & Implementation-Ready

### Context
To remain compatible with the intended free-tier hosting architecture (specifically Render's free Web Service tier), deploying two separate Python background/server processes (`apps/api` for FastAPI REST and `apps/mcp-server` for Model Context Protocol) is untenable due to container compute limits, cold-start latency, memory overhead, and resource allowances. Furthermore, running separate servers duplicates repository access patterns and domain logic across bounded contexts. A unified deployment model is required without degrading the architectural segregation between RESTful user interaction and AI agent tool execution.

### Decision
Deploy the entire Python backend as **One Render Web Service**, combining the FastAPI REST application and the MCP server into a single operational container and ASGI runtime instance.

#### 1. One-Service Architecture
- There must be **one Python application, one container, one start command, and one Render Web Service**.
- Do **not** create a separately deployed `apps/mcp-server` cloud service. (Existing standalone code in `apps/mcp-server/` must be refactored or integrated into the single service runtime rather than deployed independently).
- Do **not** combine everything into one unreadable Python source file; modular directory structure and boundaries must be preserved within the unified package.

#### 2. Agent Ownership Boundaries
- **Agent 3 (FastAPI Backend and Domain Services):** Owns the core FastAPI application lifecycle, REST API router hierarchies, repositories, domain services, user authentication middleware, background-job foundation, and shared backend infrastructure.
- **Agent 10 (Secure MCP Server and External AI Access):** Owns the MCP protocol layer, client credentials, access scopes, tool definitions, token revocation, rate limits, and MCP audit controls.
- **Mounting Contract:** Agent 10 must mount the MCP Streamable HTTP application inside Agent 3's existing FastAPI ASGI application lifecycle at the route mount point `/mcp`.

#### 3. Shared Domain-Service Strategy
- Both the REST API endpoints and the MCP tool handlers must execute business logic strictly by calling **shared domain services and repositories** (e.g., `app/services/` and `app/repositories/`).
- Do **not** duplicate SQL queries, repository accessors, or core business logic inside the MCP module. The MCP layer acts purely as a protocol adaptation and tool-routing schema layer over canonical domain services.

#### 4. Separate REST and MCP Security Boundaries
- Although they share underlying domain services, REST and MCP must retain **strict, separate authentication, authorization, rate-limiting, and auditing boundaries**:
  - **REST API:** Authenticated via Supabase GoTrue Bearer JWTs; authorization mapped to authenticated user sessions; rate-limited per user/IP; audit logging tagged with `source='web_rest'`.
  - **MCP Endpoint (`/mcp`):** Authenticated via cryptographic client API tokens (`X-MCP-API-KEY` or Bearer credentials); authorization governed by granular scope assignments and read-only defaults; rate-limited per client API key (default 60 req/min); audit logging tagged with `source='mcp_server'`.

#### 5. Streamable HTTP MCP Transport
- Instead of using standard JSON-RPC over stdio or legacy SSE architectures requiring dual-channel socket routing, the MCP server will utilize the modern **Streamable HTTP MCP Transport** spec mounted over ASGI at `/mcp`, allowing bidirectional tool interaction within standard HTTP POST/GET framing compatible with reverse proxies and serverless edge routers.

#### 6. Ephemeral Filesystem Constraints
- Render's container filesystem must be treated as **strictly ephemeral**. Any file written to disk during container runtime will be destroyed upon container restart, scaling event, or free-tier spin-down.
- Local folders such as `knowledge/` or temporary scratch directories can only be used as ephemeral transit workspaces during active processing (e.g., during PDF chunking or Markdown archive generation).
- **Permanent Data Persistence:** All permanent state and user knowledge must remain in **Supabase PostgreSQL** (canonical tables & vector embeddings), **Supabase Storage** (binary files & document buckets), or approved **Google Drive cloud backups**.

### Alternatives Considered
1. **Separately Deployed Render Web Services (`apps/api` and `apps/mcp-server`):** Rejected because free-tier hosting limits restrict the number of running container web services and RAM allocation, causing frequent out-of-memory crashes and excessive idle sleep spin-up delays.
2. **Monolithic Python Script (Combining endpoints, tools, and queries in `main.py`):** Rejected due to catastrophic loss of maintainability, modularity, testability, and multi-agent ownership boundaries.
3. **Lambda / Serverless Functions for MCP:** Rejected due to connection timeout limits during multi-step LLM reasoning cycles and incompatible state initialization overhead for AI provider connections.

### Consequences
- **Positive:** Fits within Render's free-tier memory and compute budget. Eliminates localhost network hops between MCP tool execution and database service repositories. Simplifies container orchestration, logging, and CI/CD deployment pipelines.
- **Negative:** Requires careful ASGI router integration between Agent 3 and Agent 10. Memory leaks or fatal unhandled exceptions in an MCP tool handler could impact the main FastAPI REST application if exception middleware is not appropriately isolated.

### Free-Tier Limitations
- **Cold Starts:** Free-tier instances spin down after 15 minutes of inactivity; initial requests may incur a 30–50 second boot delay. Background persistent timers must rely on database cron jobs or webhooks rather than long-lived OS daemon threads.
- **Memory Allocation:** Limited to 512MB RAM. Vector embedding generation and PDF document chunking must stream in small memory-bounded batches to prevent OOM termination.

### Future Migration Path
If system adoption and concurrent request throughput outgrow free-tier limits or single-node CPU bounds:
1. Because the MCP module interacts with core logic strictly via shared domain service repositories rather than tight coupling to FastAPI request state, the `/mcp` ASGI mount can be detached.
2. The MCP module can be re-packaged into a separate container (`apps/mcp-server`) communicating either directly with Supabase PostgreSQL over connection pools or calling the REST API over internal private networking without rewriting tool schemas or domain logic.

