# Taj's Second Brain — AI Executive Suite & Founder Terminal

An enterprise-grade, secure, autonomous AI operating engine engineered for executive leadership, RAG-driven knowledge synthesis, venture execution, network intelligence, and career proof documentation. Engineered with a **Retro-Futuristic Founder Terminal** visual architecture and strict data sovereignty principles.

---

## 🏛️ System Architecture & Core Tenets

Taj's Second Brain is structured around four non-negotiable architectural and security principles:

1. **User-Owned & Portable Data**: All recorded knowledge, ideas, decisions, notes, and CRM intelligence must remain completely sovereign and portable. The system includes persistent background workflows to export the entire corpus into portable **Markdown tables and structured front-matter files**.
2. **Strict Row Level Security (RLS)**: Every single query, repository mutation, and interaction enforced via Supabase PostgreSQL policies and local application-layer filtering. A user only ever accesses their authenticated tenant data.
3. **Zero-Secret Zero-Trust Logging & Git**: No API secrets, plaintext MCP tokens, database credentials, or PII ever touch frontend bundles, git commit history, application system logs, or unencrypted storage buckets.
4. **No Client-Side `user_id` Impersonation**: API endpoints reject any hardcoded or client-supplied user identifiers. Identity is extracted dynamically in real-time from cryptographically verified Supabase JWTs or securely salted HMAC MCP credentials.

---

## 📂 Monorepo Structure & Core Application Modules

```text
├── apps/
│   ├── api/               # FastAPI Backend & Domain Application Services
│   │   ├── app/           # Domain Layer (Models, Repositories, Services, Routers)
│   │   ├── tests/         # Comprehensive Test Suite (53 integrated & security tests)
│   │   ├── Dockerfile     # Multi-stage production container build script
│   │   └── requirements.txt
│   ├── mcp-server/        # Model Context Protocol (MCP) sidecar & tooling server
│   └── web/               # Next.js / Vanilla CSS Retro-Futuristic Founder Terminal UI
├── docs/                  # Architecture contracts, schemas, PRDs, and implementation plans
└── docker-compose.yml     # Container orchestration for seamless production deployment
```

---

## 🧠 Backend Domain Capabilities (`apps/api`)

The backend exposes a secure, highly scalable REST and structured JSON API powered by **FastAPI**, **SQLAlchemy 2.0 (AsyncIO)**, and **Supabase**:

* **Founder Dashboard & Operations**: Track executive KPIs, core objectives, operational metrics, and venture priorities.
* **Network Intelligence & CRM**: Maintain deep relationship context, interaction histories, participant logs, and automated meeting follow-up synthesis.
* **Knowledge & Memory Ledger**: Capture meetings, lessons learned, strategic reflections, and decision logic with alternative analysis.
* **AI Content Engine & Authenticity**: Grounded drafting using Gemini/OpenAI RAG pipelines with **zero auto-publishing guarantees**, claim verification against real source records, and pre-generation PII privacy scans.
* **Career Proof Portfolio & Case Studies**: Transform verified milestones and quantifiable impact KPIs directly into verified case studies, executive cover letters, and high-engagement technical communications.
* **Document Processing & PDF Analysis**: Upload proprietary specification sheets and PDFs for multi-stage background chunking, hashing, and vector semantic retrieval.
* **Secure MCP Integration Engine**: Dedicated endpoints and repositories managing Model Context Protocol API keys with constant-time HMAC comparison, prefix querying (`sb_mcp_`), instant revocation, and automated cryptographic rotation.
* **Persistent Job Orchestration**: Database-backed asynchronous queue executing Google Drive sync schedules, file digestion, and complete user Markdown data extraction.

---

## 🚀 Deployment & Local Orchestration

### 1. Containerized Deployment (Recommended)
You can build and run the production backend service using Docker Compose:

```bash
docker-compose up --build -d
```
* The API service will be accessible at `http://localhost:8000`.
* Live liveness and readiness probes available at `/health/live` and `/health/ready`.
* OpenAPI Swagger interactive docs accessible at `/docs`.

### 2. Local Python Environment
To execute natively without Docker:

```bash
cd apps/api
python -m venv .venv
# Activate environment
# Windows:
.venv\Scripts\activate
# Unix/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🧪 Quality Assurance & Test Verification

The codebase maintains strict reliability standards with an automated test suite verifying domain contracts, RLS isolation, JWT rejection modes, pagination serialization, and AI guardrails.

To execute the test suite with detailed code coverage reporting:

```bash
cd apps/api
pytest --cov=app -v
```

### Verified Test Categories:
* **Authentication & Security (`test_auth_security.py`)**: Token expiration handling, invalid signature rejection, security headers, and CORS enforcement.
* **MCP Security & Lifecycle (`test_mcp_auth.py`, `test_mcp_api.py`)**: Salted HMAC verification, instant token revocation, expiration dates, and secure rotation.
* **AI Engine & Privacy Guardrails (`test_content_engine_api.py`, `test_knowledge_ai.py`)**: Claim validation against citations, zero auto-publishing defaults, PII detection, and hybrid vector searching.
* **Domain & CRM (`test_founder_domain.py`, `test_crm_memory.py`, `test_kpis_api.py`)**: Complete CRUD, filtering, and PostgREST-compatible pagination across executive modules.
* **System & Integrations (`test_integrations_export.py`, `test_health.py`)**: Background job handling, Markdown export verification, and database health check probes.

---

## 📜 License & Ownership

Copyright © 2026 Taj's Second Brain. All rights reserved. Built for private executive operation with strict user ownership and data sovereignty.
