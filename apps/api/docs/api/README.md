# Taj's Second Brain — FastAPI Backend & Domain Architecture Documentation

Welcome to the canonical technical reference for **Taj's Second Brain FastAPI Backend**. This document provides an executive architectural overview, authentication specifications, multi-tenant security guidelines (RLS), local testing workflows, and endpoint routing tables.

---

## 1. Architectural Foundation & Layering
The backend follows a clean architecture model designed for strict ownership, modular extension, and high security:

- **API Layer (`app/api/v1/`)**: Handles HTTP requests, input validation via Pydantic schemas, routing, and HTTP status mapping.
- **Service Layer (`app/services/`)**: Enforces domain business logic, cross-record validation, transactional boundaries, and automated audit logging.
- **Repository Layer (`app/repositories/`)**: Encapsulates all SQLAlchemy persistence operations with mandatory user-id scoping for Row Level Security (RLS).
- **AI Abstraction Layer (`app/ai/`)**: Provides provider-neutral LLM execution (Google Gemini / OpenAI) and hybrid semantic RAG retrieval (`perform_hybrid_search`).
- **Background Job Engine (`app/jobs/`)**: Asynchronous worker pipeline (`JobRunner`) managing document chunking/embeddings, Markdown data export, and Google Drive/Calendar synchronization.

---

## 2. Authentication & RLS Enforcement
- **Authentication**: All domain endpoints require an HTTP Authorization header containing a valid JSON Web Token:
  ```http
  Authorization: Bearer <jwt_token>
  ```
- **Local JWT Validation**: The backend independently validates token signatures using `JWT_SECRET` and extracts `sub` as the active `user_id`.
- **Zero Hardcoded User IDs**: Clients NEVER pass `user_id` in query strings or payloads. The identity is securely injected via the `get_current_user` FastAPI dependency.
- **Row Level Security (RLS)**: Every query automatically appends `.where(Entity.user_id == authenticated_user.id)` within `BaseRepository`, guaranteeing zero horizontal cross-tenant leakage.

---

## 3. Data Portability & Markdown Export (ADR-005)
Taj's Second Brain operates on a **User-Owned Data Model**. At any time, founders can request a full archive export in human-readable Markdown format with YAML frontmatter via:
- **POST `/api/v1/export/markdown`**: Initiates background projection of canonical database records into structured Markdown files, bundled with temporary signed URLs.

---

## 4. Test Suite Execution
To run the automated test suite locally without requiring an external PostgreSQL instance, execute:
```bash
# From inside apps/api/ directory
pytest tests/ -v
```
The test suite utilizes an in-memory asynchronous SQLite harness (`sqlite+aiosqlite:///:memory:`) and tests all routes, RLS isolation, token encryption, and AI fallback generation.

---

## 5. Summary Endpoint Table

| Module | Method & Path | Description |
| :--- | :--- | :--- |
| **System Health** | `GET /health`, `/health/live`, `/health/ready` | Standard liveness and database reachability probes |
| **Founder Profile** | `GET /api/v1/me`, `PATCH /api/v1/me` | Inspect or update current founder profile attributes |
| **Dashboard** | `GET /api/v1/dashboard/summary`, `/insights` | Operational metrics and automated AI guidance |
| **Ventures** | `GET /api/v1/ventures`, `POST /api/v1/ventures` | Strategic venture management with slug deduplication |
| **Projects & Tasks**| `GET/POST /api/v1/projects`, `/api/v1/tasks` | Actionable project milestones and prioritized tasks |
| **Network CRM** | `GET/POST /api/v1/people`, `/organizations`, `/interactions` | Relationship intelligence and meeting logs |
| **Knowledge & RAG** | `POST /api/v1/documents`, `GET /api/v1/memories` | Upload attachments for OCR and vector chunking |
| **AI Intelligence** | `POST /api/v1/ai/search`, `/ai/content-generate` | Grounded semantic search and citation-backed drafting |
| **Executive Career**| `POST /api/v1/ai/cover-letter`, `/ai/linkedin-post` | Automated achievement storytelling and cover letters |
| **Integrations** | `POST /api/v1/sync/gdrive`, `/sync/calendar` | Trigger asynchronous Drive backup and schedule syncs |
| **Portability** | `POST /api/v1/export/markdown`, `GET /api/v1/exports` | Request portable YAML-frontmatter Markdown archives |

---
*Authored by Agent 3 — FastAPI Backend, Domain Architecture, API Security, and Integration Services Engineer.*
