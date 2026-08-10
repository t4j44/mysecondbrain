# Master Implementation Plan - Taj's Second Brain

Version: 2.0 (Comprehensive Implementation-Ready Specification)  
Author: Agent 1 — Architecture and Contracts Agent  
Approved by: Agent 0 — Lead Orchestrator  

---

## 1. Executive Architecture Summary

### Purpose of the System
Taj’s Second Brain is a private, AI-powered Founder Operating System (Founder OS) designed to ingest, organize, retrieve, analyze, and synthesize every critical dimension of Taj’s personal and professional startup journey. By unifying scattered operational data—including ventures, projects, tasks, relationship CRM interactions, meeting notes, personal memories, idea validations, life KPIs, career case studies, and content drafts—into an integrated intelligence platform, the system functions as an enduring second memory and interactive executive thinking partner.

### Major Architectural Layers & Communication
The application is architected across six strictly encapsulated domain layers:
1. **Frontend Presentation Layer (`apps/web`):** A reactive Next.js 14+ (App Router) React web application embodying a curated "Retro-Futuristic Founder Terminal" design aesthetic. It communicates with the backend via HTTPS RESTful JSON APIs and Server-Sent Events (SSE) streaming protocols.
2. **Backend Application Layer (`apps/api`):** A Python FastAPI domain web service that acts as the authoritative enforcement engine for authentication verification, business logic, asynchronous background job dispatch, and external API integrations.
3. **Canonical Persistence Layer (`supabase/`):** A cloud-hosted Supabase PostgreSQL 15+ database and Supabase Storage object system serving as the immutable canonical source of truth for all structured entities, neural vector embeddings (`pgvector`), and document attachments.
4. **AI Intelligence & RAG Layer (`backend/app/ai`):** A decoupled AI provider abstraction pipeline leveraging Google Gemini Pro/Flash (primary) and OpenAI GPT-4o (fallback) for semantic conversational retrieval, hybrid similarity search, automated summarization, and content drafting.
5. **Universal Portability & Backup Layer (`knowledge/`):** An asynchronous worker framework that continuously translates canonical relational database records into structured, YAML-frontmatter-enhanced plain-text Markdown files (`knowledge/Founder_OS/**/*.md`) and replicates them to Taj's personal Google Drive account.
6. **Model Context Protocol (MCP) Server Layer (`apps/mcp-server`):** A standalone Python MCP SDK desktop interface enabling trusted external LLM assistants (Claude Desktop, ChatGPT, Claude Code, Gemini CLI) to securely read and query founder knowledge tools without bypassing backend validation rules.

### Alignment with Core Design Imperatives
- **Privacy & User Ownership:** Taj retains total sovereign ownership over all operational data. No proprietary database formatting traps user memory; the system deterministically mirrors active knowledge into universal offline Markdown structures and independent cloud backups.
- **Scalability & Maintainability:** Strict monorepo folder decoupling and modular domain services enable rapid parallel engineering across autonomous agent teams without cross-module regression or schema drift.

---

## 2. System Architecture & Component Interaction

For deep-dive specifications and hardware integration rules, reference the dedicated architecture document: [docs/architecture/system_architecture.md](file:///e:/second%20brain/docs/architecture/system_architecture.md).

```mermaid
graph TD
    %% Client Tier
    subgraph Clients ["User Devices & AI Desktop Clients"]
        Browser["Next.js Web Browser (App Router)"]
        Obsidian["Local Obsidian / Markdown Viewer"]
        AI_Client["Claude Desktop / ChatGPT / Gemini CLI"]
    end

    %% Edge & Auth Tier
    subgraph Edge ["Authentication & Routing Edge"]
        Auth["Supabase GoTrue Auth (JWT / JWKS)"]
        Vercel["Vercel Frontend Edge Hosting"]
    end

    %% Backend Service Tier
    subgraph Backend ["Python Backend Cluster (Render/Railway)"]
        FastAPI["FastAPI Domain REST API & SSE Streams"]
        Workers["Asyncio Database-Backed Job Workers"]
        MCP["Python MCP SDK Standalone Server"]
        AI_Provider["BaseLLMProvider (Gemini / OpenAI Wrapper)"]
    end

    %% Data Tier
    subgraph Data ["Canonical Cloud Storage Tier"]
        DB[(Supabase PostgreSQL 15+\n31+ Tables + RLS)]
        Vec[(pgvector Embeddings\nIVFFlat + HNSW)]
        Buckets["Supabase Storage Private Buckets\n(PDFs, Memos, Avatars)"]
    end

    %% External Cloud & Portability Tier
    subgraph Portability ["Universal Ownership & Integrations"]
        MD_Files["Local Workspace Archive\nknowledge/Founder_OS/*.md"]
        GDrive["Google Drive API (Cloud Backup Folder)"]
        GCal["Google Calendar API (Two-Way Task Sync)"]
        LLM_Cloud["Google AI & OpenAI API Cloud Endpoints"]
    end

    %% Execution Flows
    Browser -->|HTTPS / React Server Components| Vercel
    Browser -->|Login / Session Cookies (@supabase/ssr)| Auth
    Browser -->|REST Bearer JWT / SSE Streams| FastAPI
    AI_Client -->|JSON-RPC via STDIO/SSE (X-MCP-KEY)| MCP
    
    FastAPI -->|JWT RSA Signature Auth check| Auth
    FastAPI -->|SQLAlchemy 2.0 Asyncio Pool| DB
    FastAPI -->|Hybrid Vector + FTS Query| Vec
    FastAPI -->|Signed Private Blob URLs| Buckets
    FastAPI -->|Dispatch Async Job Tasks| Workers
    FastAPI -->|Polymorphic Request| AI_Provider
    
    MCP -->|Call Shared Domain Repositories| DB
    MCP -->|Execute Read-Only Semantic Tools| Vec
    
    AI_Provider -->|TLS Rest Ingestion & Embedding| LLM_Cloud
    Workers -->|Export YAML-Frontmatter Snapshots| MD_Files
    Workers -->|AES-256-GCM Encrypted Token Exch| GDrive
    Workers -->|Sync High-Priority Task Due Dates| GCal
    Obsidian -->|Read Offline User Archive| MD_Files
```

---

## 3. Production-Ready Monorepo Structure

The workspace adopts a unified, multi-language monorepo managed via pnpm workspaces (for Node/TypeScript frontend architectures) and Python UV virtual environments (for backend API and MCP execution). For foundational architecture decisions, reference [ADR-001](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-001-monorepo-structure).

```text
e:/second brain/
├── apps/
│   ├── web/                     # Next.js 14 App Router React Web Application
│   ├── api/                     # Python FastAPI Domain Web Service
│   └── mcp-server/              # Standalone Python MCP SDK Server Execution Engine
├── packages/
│   ├── ui/                      # Shared Tailwind CSS, Shadcn UI & Framer Motion Components
│   ├── shared-types/            # Synchronized TypeScript Interfaces & JSON Schema structural models
│   ├── prompts/                 # Versioned System Prompt Instructions & AI Persona Definitions
│   ├── database/                # Shared SQLAlchemy ORM Models, Connection Pools & Repositories
│   └── config/                  # Centralized Tsconfig, ESLint, Tailwind, & Python Ruff/MyPy Rules
├── supabase/
│   ├── migrations/              # Authoritative SQL Migrations (Tables, RLS, pgvector, Triggers)
│   ├── seed/                    # Developer Sandbox & Integration Testing SQL Seed Data
│   └── tests/                   # pgTAP and pg_prove RLS Isolation & Database Verification Tests
├── knowledge/
│   └── Founder_OS/              # Universal Local Markdown Workspace Archive (Obsidian-Compatible)
│       ├── People/              # Exported Founder CRM relationship logs & contact cards
│       ├── Projects/            # Active project progress trackers and milestones
│       ├── Ventures/            # Core startup folders (Justor AI, Zqtion, IEXF, CMOOS)
│       ├── Meetings/            # Audio transcription summaries, conversation notes, takeaways
│       ├── Ideas/               # Idea Vault problem-solution briefs & AI market validations
│       ├── Achievements/        # Structured career proof artifacts and PM case studies
│       ├── Decisions/           # Strategic architectural and venture decisions log
│       ├── Content/             # AI Content Engine drafts, LinkedIn posts, publication history
│       └── Weekly Reviews/      # Automated reflection reviews and KPI achievement summaries
├── docs/
│   ├── architecture/            # Architectural blueprints, sequence workflows, and ADR records
│   ├── api/                     # OpenAPI 3.1 technical API endpoint documentation & tool definitions
│   ├── database/                # Complete table definitions, indexing specs, and RLS guidelines
│   ├── security/                # Threat models, prompt-injection defenses, token encryption rules
│   └── deployment/              # Container Dockerfiles, Render/Railway CI/CD workflows, configs
├── tests/
│   ├── integration/             # Cross-service API testing suite (FastAPI <-> Postgres <-> AI)
│   └── e2e/                     # Playwright / Cypress browser automation & terminal theme validation
├── Tajs_Second_Brain_PRD_TRD.md # Master Product & Technical Requirements Document
├── implementation_plan.md       # Primary implementation coordination document (this file)
├── database_schema.md           # Authoritative logical database table specification
├── api_contracts.md             # Authoritative REST endpoint & MCP tool contract specification
├── security_and_privacy_plan.md # Authoritative cybersecurity, encryption & data privacy plan
└── development_roadmap.md       # Multi-agent phased operational project orchestration schedule
```

### Folder Responsibilities & Ownership Boundaries
- **Import Boundaries:** Code inside `apps/web/` is strictly barred from importing backend server modules or Python runtime dependencies from `apps/api/` or `apps/mcp-server/`. Communication occurs exclusively via network HTTP APIs or shared static contracts in `packages/shared-types/`.
- **Shared-Type Ownership:** Managed by **Agent 1 & Backend/Frontend Foundation Agents**. When a Pydantic schema alters in `apps/api/`, a compilation tool regenerates corresponding TypeScript interfaces in `packages/shared-types/` to prevent contract drift.
- **Configuration & Prompt Ownership:** `packages/config/` is governed by Group A foundational agents; `packages/prompts/` is owned by the **AI Retrieval & KPI/Portfolio Agents**, insulating prompt instruction wording from API application logic.
- **Test Ownership:** Each agent group is responsible for deploying unit tests within their package folder; overall E2E test suites in `tests/e2e/` are governed by the **QA & E2E Testing Agent**.

---

## 4. Frontend Architecture

### Routing & Component Boundary Fundamentals
- **App Router Route Groups:** Organized cleanly into `app/(auth)/*` for unauthenticated entrance paths (`/login`, `/signup`) and `app/(dashboard)/*` for protected operational terminal views.
- **Server vs. Client Component Boundaries:** All layout frames, navigational shells, data summary tables, and profile overviews render as **React Server Components (RSC)** to eliminate hydration bloat and protect backend routing paths. Interactive UI components (search input bars, live SSE chat windows, Framer Motion modal drawers, Recharts interactive data visualizations) explicitly invoke the `'use client'` directive.
- **Data-Fetching & Caching Strategy:** RSC views fetch initial operational state via authenticated server fetchers leveraging Next.js fetch caching (`next: { revalidate: 60 }` for stable archives, `no-store` for live task boards). Client interactions leverage **TanStack React Query (SWR pattern)** to execute background polling, optimistic UI updates, and cached mutation reversals on network error.
- **Form Management & Input Defense:** All user input forms utilize **React Hook Form** tightly integrated with **Zod Schema validation**, executing client-side rule validation matching the backend Pydantic API constraints before firing network requests.
- **UX States & Design Aesthetics:** Every route guarantees curated UI states: skeleton loading animations during network data calls, informative empty states prompting quick action ("No active mentors tagged yet—Add your first advisor"), and non-blocking toast notifications on error. The styling architecture strictly deploys a **Retro-Futuristic Founder Terminal** visual motif (Deep purple `#12081d`, Cream text `#f7f4ea`, Black console backgrounds `#0a0510`, Neon green operational indicators `#00ff9d`) powered by Google Fonts editorial typography (*Outfit* & *JetBrains Mono*).

### Complete Application Route Structure (All 21 Required Routes)
```text
/login                 -> Founder terminal authentication portal (Email & Magic Link)
/signup                -> Secure account initial registration portal
/dashboard             -> Daily command terminal (Current mission, tasks, KPI widgets)
/ventures              -> High-level startup organization and portfolio overview
/ventures/[ventureId]  -> Individual venture execution view (Vision, roadmap, tasks)
/projects              -> Global project pipeline and deadline tracking view
/projects/[projectId]  -> Deep-dive project workspace and member collaboration log
/tasks                 -> Linear/Notion-inspired interactive task management view
/people                -> Network Intelligence Founder CRM directory and relationship graph
/people/[personId]     -> Individual CRM contact timeline, interaction history & next actions
/organizations         -> Company and enterprise entity directory view
/memories              -> Historical conversational memory stream and insight browser
/meetings              -> Meeting audio notes, summaries, participants, and takeaways
/ideas                 -> Idea Vault interactive market opportunity validator
/kpis                  -> Life KPI tracking matrix (Founder, Network, and Learning growth)
/achievements          -> Career proof builder and project milestone archive
/content               -> AI Content Engine studio for LinkedIn posts and founder stories
/assistant             -> Live streaming conversational AI Founder Coach chat interface
/settings              -> Founder profile attributes, application preferences, & theme toggles
/settings/integrations -> Google Calendar, Google Drive, and MCP access token manager
/settings/export       -> Manual Markdown offline export generator and download hub
```

---

## 5. Backend Architecture

For backend architectural patterns and database connection evaluation decisions, see [ADR-002](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-002-fastapi-database-access-strategy) and [ADR-008](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-008-background-job-strategy).

### FastAPI Domain Structural Design
```text
apps/api/
├── main.py                    # ASGI Application initiation, CORS setup, Lifespan events
├── config.py                  # Pydantic Settings environment configuration loader
├── dependencies.py            # Shared dependency injectors (DB Sessions, Current Auth User)
├── routers/                   # Versioned REST endpoints cleanly decoupled by domain module
│   ├── auth.py                # Profile & session status checks (/api/v1/me)
│   ├── dashboard.py           # Command center aggregation (/api/v1/dashboard/*)
│   ├── ventures.py            # Startup organization endpoints (/api/v1/ventures/*)
│   ├── projects.py            # Project milestone management (/api/v1/projects/*)
│   ├── tasks.py               # Action items and due dates (/api/v1/tasks/*)
│   ├── crm.py                 # People and Organizations directory (/api/v1/people/*)
│   ├── interactions.py        # Meeting logs and historical takeaways (/api/v1/interactions/*)
│   ├── memories.py            # Unstructured founder reflection captures (/api/v1/memories/*)
│   ├── ideas.py               # Idea Vault and AI validation engines (/api/v1/ideas/*)
│   ├── decisions.py           # Strategic decision records (/api/v1/decisions/*)
│   ├── documents.py           # File attachment processing & storage URLs (/api/v1/documents/*)
│   ├── search.py              # pgvector RAG keyword & hybrid retrieval (/api/v1/search/*)
│   ├── assistant.py           # Conversational AI SSE streaming routes (/api/v1/ai/*)
│   ├── kpis.py                # Growth matrix metrics and periodic entries (/api/v1/kpis/*)
│   ├── portfolio.py           # Career proof achievement case studies (/api/v1/achievements/*)
│   ├── content.py             # Social post drafts and version histories (/api/v1/content/*)
│   ├── weekly_reviews.py      # Automated reflection generation (/api/v1/weekly-reviews/*)
│   ├── integrations.py        # Google OAuth callbacks & sync triggers (/api/v1/integrations/*)
│   └── exports.py             # Markdown ZIP generator & download jobs (/api/v1/exports/*)
├── schemas/                   # Strict Pydantic v2 validation input & output data definitions
├── services/                  # Business logic rules, calculations, and domain orchestrators
├── repositories/              # SQLAlchemy 2.0 Asyncio Database execution layers & queries
├── ai/                        # BaseLLMProvider abstractions, Gemini & OpenAI drivers, prompt builder
├── workers/                   # Background job processors (RAG embedding, GDrive sync, export)
└── middleware/                # Request logging, rate limiting, exception wrapping, cors
```

### Database Access & Job Queue Evaluation Decisions
- **Database Access Strategy:** Adopt **SQLAlchemy 2.0 (AsyncIO with asyncpg)** as the primary persistence framework for FastAPI to support complex polymorphic relational joins, native pgvector similarity query filtering, and autogenerated SQL schema migrations. The Supabase Python SDK is leveraged exclusively for Authentication verification and Storage Bucket signed URL management ([ADR-002](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-002-fastapi-database-access-strategy)).
- **Background Job Execution:** For initial implementation phases, utilize a **Database-Backed Job Queue** combining PostgreSQL operational tables (`public.sync_jobs`, `public.export_jobs`) with **FastAPI Background Tasks (`asyncio` execution)**. Every asynchronous operation returns HTTP 202 Accepted with a trackable job ID. This eliminates the operational cost of managing external Redis/Celery clusters while preserving a clean migration path to dedicated background Python worker daemons as processing demands scale ([ADR-008](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-008-background-job-strategy)).
- **Middleware & Reliability Defenses:** Global ASGI middleware enforces structured JSON exception handling, request ID correlation tracking, IP-based API rate limiting (in-memory token bucket or Supavisor Redis), and sub-second `/health` system status monitoring.

---

## 6. Authentication Architecture

For detailed sequence diagrams, key isolation tiers, and security validation mechanics, see [docs/architecture/authentication_flow.md](file:///e:/second%20brain/docs/architecture/authentication_flow.md) and [ADR-003](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-003-authentication-and-jwt-validation).

### Auth Flow & Token Mechanics
- **Identity Provider:** Supabase Auth (GoTrue) handling secure Email/Password sign-ins and passwordless Magic Links.
- **Frontend Session Management:** Next.js uses `@supabase/ssr` to securely bind session JWT access tokens and refresh tokens into **HTTP-Only, Secure, SameSite=Lax cookies**. No authentication tokens are ever stored in vulnerable browser mechanisms like `localStorage`. Next.js edge middleware automatically intercepts unauthorized attempts to view `/dashboard` routes and redirects to `/login`.
- **FastAPI JWT Verification:** API route handlers inject `current_user: User = Depends(get_current_user)`. This dependency extracts the `Authorization: Bearer <token>` header and verifies the RSA/HS256 cryptographic signature locally against Supabase JWKS public keys without network round-trip delays, extracting the verified user ID (`sub`).
- **Zero-Trust Rule:** Under no circumstances will any API endpoint rely on a client-supplied `user_id` inside a JSON body or route path to authorize record modifications; ownership is explicitly extracted from the verified JWT token signature.

---

## 7. Storage Architecture

For canonical data rules, filesystem folder hierarchies, and backup restoration protocols, see [ADR-004](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-004-canonical-data-source) and [docs/architecture/export_and_backup_flow.md](file:///e:/second%20brain/docs/architecture/export_and_backup_flow.md).

### Storage Tier Roles & Canonical Source of Truth
1. **Supabase PostgreSQL (Canonical Source of Truth):** Acts as the absolute transactional master for all active structured relationships, tasks, CRM interactions, KPI entries, and AI chat histories.
2. **Supabase Storage (Object Blob Canonical Source):** Hosts uploaded file attachments, contract PDFs, meeting voice memos, and avatar graphics in **strictly private buckets** accessible only via cryptographically signed temporary URLs.
3. **Markdown Knowledge Repository (`knowledge/Founder_OS/`):** Functions as a **Derived Read-Only Projection** generated deterministically from PostgreSQL. Every file combines structural YAML frontmatter identifiers with clean human-readable markdown content, guaranteeing universal offline reading in apps like Obsidian and zero vendor lock-in.
4. **Google Drive Cloud Storage:** Serves as an external off-site disaster recovery vault, receiving scheduled compressed backup archives (`.zip`) and synchronized markdown structure snapshots from FastAPI asynchronous background sync jobs.

---

## 8. AI Architecture & Provider Abstraction

For complete specifications on the ten AI capability modules and abstract polymorphic driver patterns, see [docs/architecture/ai_retrieval_flow.md](file:///e:/second%20brain/docs/architecture/ai_retrieval_flow.md) and [ADR-006](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-006-ai-provider-abstraction).

### Capabilities & Provider Abstraction Layer
The AI architecture decouples operational business logic from direct external SDK dependencies by establishing a unified Python abstraction interface (`BaseLLMProvider` in `apps/api/app/ai/provider.py`).
- **Primary Provider Engine:** `GeminiLLMProvider` utilizing Google Gemini Pro 1.5 / Flash models for reasoning and text generation, paired with `text-embedding-004` (768 dimensions) for vector extraction.
- **Fallback Provider Engine:** `OpenAILLMProvider` utilizing OpenAI GPT-4o / Flash models and `text-embedding-3-small`, enabling automatic seamless failover during vendor cloud outages or rate-limit saturation.
- **Supported Operational Modules:** The AI layer delivers ten distinct analytical engines: (1) Semantic Memory Search, (2) Meeting & CRM Memory Retrieval, (3) Document & Transcription Summarization, (4) Command Dashboard Daily Recommendations, (5) Interactive Conversational Founder Coach, (6) Relationship Intelligence Briefing Generator, (7) Weekly Performance Strategic Reviewer, (8) Authentic Content Engine for social drafting, (9) Career Proof Portfolio Case Study Generator, and (10) Idea Vault Market Opportunity Validator.

---

## 9. Retrieval-Augmented Generation (RAG) Architecture

For the step-by-step 15-stage sequence diagram, vector database parameters, hybrid search equations, and prompt-injection defense encapsulations, see [docs/architecture/ai_retrieval_flow.md](file:///e:/second%20brain/docs/architecture/ai_retrieval_flow.md) and [ADR-007](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-007-embedding-and-vector-search-strategy).

### RAG Pipeline & Hybrid Search Mechanics
To prevent LLM hallucination and ensure generated intelligence grounds strictly in Taj's authenticated founder experiences, knowledge retrieval executes a strict 15-step pipeline:
- **Ingestion & Vector Indexing:** Ingested notes, documents, and transcripts are normalized and broken into **500-token chunks with a 100-token semantic sliding overlap**. Chunks are transformed into 768-dimensional neural embeddings via Gemini `text-embedding-004` and stored in `public.memory_embeddings` indexed with **IVFFlat / HNSW vector indexes** and comprehensive JSONB provenance metadata.
- **Hybrid Retrieval & RRF Ranking:** Search queries execute a **Hybrid Search** marrying pgvector cosine distance similarity (`<=>`) with native PostgreSQL Full-Text Search (FTS Trigram matching via `pg_trgm`) to capture both semantic concepts and exact acronym/brand matches. Candidate pools are fused using **Reciprocal Rank Fusion (RRF)**, discarding any semantic vector match below an explicit **0.55 similarity threshold**.
- **Grounding & Security Invariant:** Retrieved context blocks are physically encapsulated within `<RETRIEVED_CONTEXT>` XML boundary delimiters accompanied by explicit system instructions forbidding the LLM from executing commands or prompt mutations embedded within historical note text (Prompt Injection Defense). Every factual assertion returned in chat streams must embed verifiable citation IDs linking directly back to canonical database records.

---

## 10. Integration Architecture

For detailed OAuth cryptographic token handling, GCal sync rules, and scope limitations, see [docs/architecture/export_and_backup_flow.md](file:///e:/second%20brain/docs/architecture/export_and_backup_flow.md) and [ADR-009](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-009-google-oauth-token-storage).

### Google OAuth & Calendar Sync Mechanics
- **Minimum Scoped Authorization:** Google cloud connections request strictly the narrowest permissions necessary: `auth/calendar.events` (for specific task schedule syncing) and `auth/drive.file` or appdata (restricted purely to files created by Taj's Second Brain). Global full-drive administrative permissions are rejected by architectural rule.
- **At-Rest Token Encryption:** All Google OAuth access and refresh tokens are encrypted immediately prior to database insertion using **AES-256-GCM authenticated symmetric cryptography** (`TOKEN_ENCRYPTION_KEY` hardware environment secret). Raw tokens never touch unencrypted storage or log outputs.
- **Calendar Synchronization Integrity:** When tasks bearing due dates and high priorities are created in PostgreSQL, an asynchronous worker registers corresponding events in Google Calendar and records the return `gcal_event_id` onto the task row to prevent duplication upon future updates or completion state changes.

---

## 11. Model Context Protocol (MCP) Architecture

For external client JSON-RPC connection topology, tool access security rules, and full tool specifications, see [docs/architecture/mcp_architecture.md](file:///e:/second%20brain/docs/architecture/mcp_architecture.md) and [ADR-010](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-010-mcp-service-access-strategy).

### MCP Server Integration Fundamentals
- **Server Topography & Authorization:** A standalone Python MCP Server (`apps/mcp-server/`) communicates over Stdio / SSE to connect Taj's historical memory base directly to external AI desktop applications (Claude Desktop, ChatGPT, Claude Code, Gemini CLI). All connections demand an explicit authentication credential (`X-MCP-API-KEY`) validated against encrypted DB settings.
- **Internal Service Access Rule:** To prevent schema corruption and security bypasses, **the MCP server never executes raw untyped SQL queries directly against database tables.** Instead, it invokes the shared Python Domain Service and Repository classes (`backend/app/services`), guaranteeing uniform Row Level Security scoping and data validation.
- **Default Read-Only Safety Policy:** All MCP tools operate in strict **Read-Only Mode** by default (`search_people`, `search_memory`, `get_projects`, `get_tasks`, `get_calendar`, `get_relationship_history`). Any tool capable of drafting content or altering records (`generate_linkedin_post`, `generate_case_study`, `generate_weekly_review`) outputs staged draft formulations requiring explicit human confirmation inside the Next.js Founder Dashboard before committing production mutations.

---

## 12. Observability & Audit Logging Architecture

To ensure operational visibility and rapid debugging without exposing sensitive founder secrets, system observability is structured around strict logging filtering rules:
- **Structured JSON Logs:** All backend FastAPI services and background workers output structured logs utilizing standard JSON formatting (e.g., via Python structlog or loguru) containing timestamp, severity level, module path, and correlated request IDs.
- **End-to-End Request Correlation:** Every incoming HTTP request or MCP tool call generates or propagates an immutable `X-Request-ID` header. This identifier attaches to all downstream SQL transactions, external Google API requests, LLM invocations, and SSE streams, enabling seamless distributed tracing across logs.
- **Comprehensive Audit Logging (`public.audit_logs`):** A permanent database audit table captures critical security and system events: authentication failures, OAuth integration attachments/revocations, manual data exports, MCP tool access executions, AI usage token billing volumes, background sync job status changes, and attempted security policy violations.
- **Strict Sensitive Data Exclusion Rule:** Under zero operational circumstances shall system logs or database audit records capture plaintext user passwords, raw OAuth access/refresh tokens, API secret keys, full private document attachment text, or complete unredacted conversational LLM prompts containing proprietary startup secrets.

---

## 13. Testing & Quality Assurance Architecture

To enforce absolute reliability across multi-agent parallel engineering workflows, development must satisfy a comprehensive 12-tier testing pyramid:

| Test Tier & Category | Target Execution Tooling | Core Architectural Verification Mandate |
|---|---|---|
| **1. Unit Testing** | `pytest` (Python) / `Vitest` (TypeScript) | Validate isolated utility calculations, Pydantic schema hydration, Zod rule assertions, and helper math. |
| **2. Component Testing** | React Testing Library / `Jest` | Verify terminal UI component rendering, accessible form interactions, and error toast behaviors. |
| **3. API Endpoint Testing** | `pytest` + FastAPI `TestClient` | Assert HTTP protocol negotiation, correct JSON error response formatting, and route status codes. |
| **4. Repository Testing** | `pytest-asyncio` + `asyncpg` | Execute async database sessions against rollback test schemas to verify SQLAlchemy ORM logic. |
| **5. Database Schema Tests** | `pgTAP` / `pg_prove` | Assert table primary keys, foreign key constraints, default timestamps, and pg_trgm indexes exist. |
| **6. RLS Security Tests** | `pgTAP` + Simulated Auth Claims | **Critical Gate:** Verify that executing queries under simulated `user_A` credentials physically cannot read or modify records belonging to `user_B`. |
| **7. Integration Testing** | Docker Sandbox Test Suites | Test cross-layer interactions: API ingestion -> PostgREST persistence -> Async background task dispatch. |
| **8. Browser Automation E2E** | Playwright / Cypress | Automated browser traversal of core user workflows: authentication, CRM card creation, interactive task assignment, and terminal responsive layout shifts. |
| **9. AI Retrieval Evaluation** | Custom RAG Assertion Framework | Test pgvector cosine similarity accuracy, ensure retrieval precision above 0.55 threshold, and assert accurate source citation link generation. |
| **10. MCP Tool Testing** | Python MCP Test Client | Assert that calling MCP tools over simulated JSON-RPC returns scoped JSON objects and blocks unauthorized write mutations without API access keys. |
| **11. Security Audit Testing** | Bandit / Safety / OWASP ZAP | Automated scanning of Python/Node dependencies, JWT signature forgery resilience, and SQL injection defense across dynamic query endpoints. |
| **12. Backup & Restore Tests** | Automated Sync & Rehydration Worker | Assert that compressed `.zip` markdown backups generated by workers can be successfully unzipped and re-ingested from scratch to reconstruct database state with zero data loss. |

---

## 14. Deployment & Hosting Architecture

### Deployment Infrastructure Decisions
- **Frontend Web Hosting (Vercel):** The Next.js App Router workspace deploys natively to **Vercel**, leveraging Edge network CDNs for static assets, Server-Side Rendering (SSR) in managed serverless Node environments, and reverse-proxy domain routing directly to backend APIs.
- **Backend API & MCP Hosting (Render / Railway):** Following architectural evaluation, **Render (Recommended Primary)** or **Railway (Recommended Alternative)** running continuous Docker container clusters is designated as the mandatory hosting home for the Python FastAPI application service and standalone MCP server.
  - **Evaluation Justification:** Deploying complex Python machine-learning web services (using SQLAlchemy, asyncpg, Pydantic v2, and heavy cryptographic/RAG dependencies) onto Vercel Serverless Functions introduces unacceptable limitations: severe cold-start startup delays (3-8 seconds), strict execution timeout limits that kill background document chunking workers, and structural incompatibility with long-running Server-Sent Events (SSE) streaming sockets during extensive LLM reasoning tasks. Containerized Linux services on Render/Railway eliminate cold starts, provide stable background asyncio event loops, and sustain reliable SSE connections.

### Production Environment Deployment Variables
Every production service container must initialize with verified, decoupled environment configurations:

```ini
# --- COMMON & SERVER DATABASE CONFIGURATION ---
ENVIRONMENT="production"
LOG_LEVEL="info"
API_PORT="8000"
SUPABASE_URL="https://[project-id].supabase.co"
SUPABASE_DB_URL="postgresql://postgres:[db-password]@[project-id].pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true"
SUPABASE_JWT_SECRET="[secure-project-jwt-signing-secret]"
SUPABASE_SERVICE_ROLE_KEY="[server-only-service-bypass-key-never-share]"

# --- AI PROVIDER & INTEGRATION SECRETS (SERVER ONLY) ---
AI_PRIMARY_PROVIDER="gemini"
AI_FALLBACK_PROVIDER="openai"
GEMINI_API_KEY="AIzaSy-[gemini-pro-and-embedding-key]"
OPENAI_API_KEY="sk-[optional-openai-fallback-key]"
EMBEDDING_MODEL="text-embedding-004"
EMBEDDING_DIMENSIONS="768"

# --- EXTERNAL INTEGRATION & CRYPTOGRAPHIC KEYS ---
GOOGLE_CLIENT_ID="[app-id].apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="[google-oauth-client-secret]"
GOOGLE_REDIRECT_URI="https://api.tajssecondbrain.ai/api/v1/integrations/google/callback"
TOKEN_ENCRYPTION_KEY="[32-byte-base64-url-encoded-aes-gcm-master-secret]"

# --- FRONTEND CLIENT BUILD CONFIGURATION (WEB .ENV.LOCAL) ---
NEXT_PUBLIC_APP_URL="https://app.tajssecondbrain.ai"
NEXT_PUBLIC_API_BASE_URL="https://api.tajssecondbrain.ai/api/v1"
NEXT_PUBLIC_SUPABASE_URL="https://[project-id].supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="[browser-safe-anonymous-key-protected-by-rls]"
```

### CORS, Health Checks & Operational Readiness
- **CORS Architecture:** FastAPI production configuration restricts HTTP Cross-Origin Resource Sharing explicitly to trusted application domains (`https://app.tajssecondbrain.ai`, `https://mcp.tajssecondbrain.ai`, and designated localhost development ports `http://localhost:3000`, `http://localhost:3001`), blocking unverified domains from issuing credentialed requests.
- **Health Checks & Monitoring:** Deployments maintain high availability via automated monitoring of `GET /api/v1/health`. This unauthenticated check executes sub-second validation of PostgreSQL connection pool availability, pgvector extension functionality, and primary LLM endpoint reachability, responding with explicit uptime metrics (`{"status": "ok", "db_pool": "healthy", "ai_provider": "online"}`).
- **Deployment Pipeline Orchestration:** CI/CD deployment pipelines operate via GitHub Actions / Cloud DevOps integrations. Code pushes trigger sequential validation gates: ESLint and TypeScript compilation -> Python Ruff formatting and MyPy type checking -> Pytest unit/repository execution -> Docker image build and E2E Playwright verification. Only upon achieving 100% quality gate success does the orchestrator trigger atomic container deployments to Render/Railway clusters and Vercel edge networks.
