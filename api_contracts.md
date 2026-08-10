# Master API Contracts & MCP Specification - Taj's Second Brain

Version: 2.0 (Comprehensive Implementation-Ready Technical Contracts)  
Author: Agent 1 — Architecture and Contracts Agent  
Approved by: Agent 0 — Lead Orchestrator  
Base URL: `https://api.tajssecondbrain.ai/api/v1` (Local: `http://localhost:8000/api/v1`)  
Authentication Header: `Authorization: Bearer <supabase_jwt_access_token>`  
Content-Type: `application/json` (REST) | `text/event-stream` (SSE AI Streaming)

---

## 1. Global Architectural API Conventions

### Standard Success Response Policy (Consistent Wrapped Approach)
To ensure long-term interface extensibility and predictable client hydration across React App Router components and SWR hooks, all RESTful JSON endpoints strictly return a **Wrapped Resource Payload**.
- **Single Entity Resource Response:**
  ```json
  {
    "data": { "id": "8a32d1e0-5c6a-4c9f-9a1c-2e3b4a5d6e7f", "name": "Justor AI", "status": "active" },
    "meta": { "timestamp": "2026-08-02T16:00:00Z", "request_id": "req_88a91b2c" }
  }
  ```
- **Paginated Collection Resource Response (List Endpoints):**
  ```json
  {
    "data": [
      { "id": "task-uuid-1", "title": "Review pitch deck", "status": "todo" },
      { "id": "task-uuid-2", "title": "Call mentor", "status": "todo" }
    ],
    "pagination": {
      "limit": 20,
      "next_cursor": "eyJidWRfaWQiOiAicHItMTEyIiwiZGF0ZSI6ICMyMDI2LTA4LTAyVDEwOjAwOjAwWiJ9",
      "has_more": true
    },
    "meta": { "timestamp": "2026-08-02T16:00:00Z", "request_id": "req_88a91b2c" }
  }
  ```

### Standard Error Response Format
Whenever an endpoint rejects processing due to validation failures, authentication lapses, or domain exceptions, it returns the appropriate HTTP status code accompanied by an explicit structured error object:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested relationship record was not found in your workspace.",
    "details": {
      "field": "person_id",
      "reason": "UUID does not exist under current authenticated user scope"
    },
    "request_id": "req_99b02c3d"
  }
}
```

### Common HTTP Error Codes & Meanings
- `400 BAD_REQUEST` / `VALIDATION_ERROR`: Malformed JSON or Pydantic field constraint violation.
- `401 UNAUTHORIZED`: Missing, expired, or cryptographically invalid Supabase Bearer JWT.
- `403 FORBIDDEN`: Attempting to execute an operation denied by current license or read-only MCP scope.
- `404 RESOURCE_NOT_FOUND`: Target entity UUID does not exist or is hidden by Row Level Security.
- `409 CONFLICT` / `DUPLICATE_SLUG`: Attempting to create a venture slug or KPI entry that already exists.
- `422 UNPROCESSABLE_ENTITY`: Syntactically correct payload that fails complex business validation rules.
- `429 RATE_LIMIT_EXCEEDED`: Client exceeded API rate limit buckets (e.g., >60 req/min for MCP or AI chat).
- `500 INTERNAL_SERVER_ERROR`: Unhandled backend worker exception or database connection timeout.

---

## 2. Comprehensive REST API Group Contracts

Every endpoint specified below enforces mandatory **Authentication Requirement: Bearer JWT** and **Authorization Rule: Explicit User Isolation (`auth.uid() == user_id`)** unless explicitly marked public. All endpoints operate under a baseline **Rate Limit of 300 requests/minute per authenticated user** unless stricter throttles are documented.

---

### 2.1 Authentication & Profile
- **`GET /api/v1/me`**
  - **Purpose:** Retrieve the currently authenticated founder profile and application preferences.
  - **Params:** None. | **Request Schema:** None.
  - **Response Schema:** `{ "data": { "id": "uuid", "email": "str", "full_name": "str", "avatar_url": "str", "settings": { "theme": "retro", "timezone": "UTC" } } }`
  - **Idempotency & Pagination:** Idempotent read. No pagination.
- **`PATCH /api/v1/me`**
  - **Purpose:** Update founder profile metadata, bio, or frontend theme preferences.
  - **Request Schema:** `{ "full_name": "Optional[str]", "bio": "Optional[str]", "settings": "Optional[dict]" }`
  - **Response Schema:** `{ "data": { ...updated_profile... } }` | **Error Codes:** 400, 401, 422.
  - **Idempotency:** Idempotent modification.

---

### 2.2 Founder Dashboard Command Center
- **`GET /api/v1/dashboard`**
  - **Purpose:** Aggregates real-time operational state for the daily terminal command center.
  - **Params (Query):** `venture_id` (Optional UUID to filter command dashboard by specific venture).
  - **Response Schema:**
    ```json
    {
      "data": {
        "current_mission_venture": { "id": "uuid", "name": "Justor AI", "slug": "justor-ai" },
        "today_focus_tasks": [ { "id": "uuid", "title": "Complete roadmap", "priority": "urgent" } ],
        "calendar_events_today": [ { "title": "Investor Call", "time": "14:00Z" } ],
        "active_projects_count": 4,
        "kpi_highlights": [ { "metric_name": "Users Acquired", "current_value": 1500, "target_value": 5000 } ],
        "recent_memory_stream": [ { "id": "uuid", "title": "Execution bottleneck insight", "created_at": "timestamp" } ]
      }
    }
    ```
  - **Idempotency & Caching:** Idempotent read; server cache TTL = 30 seconds (`s-maxage=30`).
- **`GET /api/v1/dashboard/insights`**
  - **Purpose:** Fetches daily AI-generated executive recommendations and execution bottleneck diagnoses.
  - **Response Schema:** `{ "data": { "ai_insight": "Your biggest bottleneck this week is execution speed on Justor AI.", "recommended_actions": ["Delegate design tasks", "Follow up with Yousuf Imran"] } }`
  - **Rate Limit:** 60 req/min (Computational LLM read abstraction).

---

### 2.3 Venture Management
- **`GET /api/v1/ventures`**
  - **Purpose:** List all startup ventures owned by the founder (Justor AI, Zqtion, IEXF, CMOOS).
  - **Query Params:** `status` (Default: 'active'), `limit` (Default: 20), `cursor` (Optional string).
  - **Response Schema:** `{ "data": [ { "id": "uuid", "name": "str", "slug": "str", "status": "active" } ], "pagination": { ... } }`
- **`POST /api/v1/ventures`**
  - **Purpose:** Initialize a new startup venture container.
  - **Request Schema:** `{ "name": "str (Required)", "slug": "str (Required, unique)", "vision": "Optional[str]", "mission": "Optional[str]", "status": "Optional[str]" }`
  - **Response Schema:** HTTP 201 Created `{ "data": { "id": "uuid", ... } }` | **Error Codes:** 400, 401, 409 (DUPLICATE_SLUG).
- **`GET /api/v1/ventures/{venture_id}`**
  - **Purpose:** Fetch comprehensive details, linked projects, and key milestones for a single venture.
  - **Path Params:** `venture_id` (UUID). | **Response Schema:** `{ "data": { "id": "uuid", "name": "str", "vision": "str", "project_count": 5, ... } }` | **Error Codes:** 401, 404.
- **`PATCH /api/v1/ventures/{venture_id}`**
  - **Purpose:** Update venture attributes, vision statements, or operational status.
  - **Request Schema:** `{ "name": "Optional[str]", "vision": "Optional[str]", "status": "Optional[str]" }`
  - **Response Schema:** `{ "data": { ...updated_venture... } }`
- **`DELETE /api/v1/ventures/{venture_id}`**
  - **Purpose:** Soft-delete/archive a venture without destroying historical memories or CRM notes.
  - **Response Schema:** `{ "data": { "id": "uuid", "status": "archived", "deleted_at": "2026-08-02T16:00:00Z" } }`
  - **Idempotency:** Idempotent soft-deletion.

---

### 2.4 Project Management
- **`GET /api/v1/projects`** | **Query Params:** `venture_id`, `status` (Default 'in_progress'), `limit`, `cursor`. | **Response:** Paginated list of projects.
- **`POST /api/v1/projects`**
  - **Request Schema:** `{ "venture_id": "Optional[UUID]", "name": "str (Required)", "description": "Optional[str]", "target_date": "Optional[YYYY-MM-DD]" }` | **Response:** HTTP 201 Created `{ "data": { ... } }`.
- **`GET /api/v1/projects/{project_id}`** | **Path Params:** `project_id` (UUID). | **Response:** Single project workspace with linked task summaries.
- **`PATCH /api/v1/projects/{project_id}`** | **Request Schema:** `{ "name": "Optional[str]", "status": "Optional[str]", "target_date": "Optional[date]" }` | **Response:** Updated project object.
- **`DELETE /api/v1/projects/{project_id}`** | **Purpose:** Archive project; sets `status='archived'`. No cascading deletion of tasks.

---

### 2.5 Task Management
- **`GET /api/v1/tasks`** | **Query Params:** `venture_id`, `project_id`, `status` (Default 'todo'), `priority`, `limit`, `cursor`.
- **`POST /api/v1/tasks`**
  - **Request Schema:** `{ "title": "str (Required)", "description": "Optional[str]", "venture_id": "Optional[UUID]", "project_id": "Optional[UUID]", "person_id": "Optional[UUID]", "priority": "str (default 'medium')", "due_date": "Optional[ISO8601]" }`
  - **Response Schema:** HTTP 201 Created. (Note: If `due_date` is present, triggers background Google Calendar sync job).
- **`GET /api/v1/tasks/today`** | **Purpose:** List open tasks where `due_date <= current_day` or priority is 'urgent'.
- **`GET /api/v1/tasks/upcoming`** | **Purpose:** List open tasks scheduled for the next 14 days sorted by chronological due date.
- **`GET /api/v1/tasks/{task_id}`** | **Response Schema:** Task details plus array of chronological `task_comments`.
- **`PATCH /api/v1/tasks/{task_id}`** | **Request Schema:** `{ "title": "Optional[str]", "due_date": "Optional[str]", "priority": "Optional[str]" }`.
- **`PATCH /api/v1/tasks/{task_id}/status`**
  - **Purpose:** Dedicated atomic transition endpoint for interactive terminal drag-and-drop task boards.
  - **Request Schema:** `{ "status": "str (todo | in_progress | done | cancelled)" }` | **Response:** Updated task object.
- **`DELETE /api/v1/tasks/{task_id}`** | **Purpose:** Soft-delete task record (`deleted_at = NOW()`).

---

### 2.6 People & Organizations (Founder CRM)
- **`GET /api/v1/people`** | **Query Params:** `q` (keyword name/company check), `relationship_type`, `tag`, `limit`, `cursor`.
- **`POST /api/v1/people`**
  - **Request Schema:** `{ "name": "str (Required)", "role": "Optional[str]", "company": "Optional[str]", "organization_id": "Optional[UUID]", "relationship_type": "str (default 'contact')", "email": "Optional[str]", "notes": "Optional[str]", "tags": ["str"] }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/people/{person_id}`** | **Response Schema:** CRM Contact profile including recent interactions timeline and linked tasks.
- **`PATCH /api/v1/people/{person_id}`** | **Request Schema:** `{ "role": "Optional[str]", "relationship_type": "Optional[str]", "tags": ["str"] }`.
- **`DELETE /api/v1/people/{person_id}`** | **Purpose:** Archive contact card; sets `deleted_at = NOW()`. Detaches relationship links in historical logs via SET NULL.
- **`GET /api/v1/organizations`** | **Query Params:** `industry`, `limit`, `cursor`. | **Response:** Paginated list of enterprise firms.
- **`POST /api/v1/organizations`** | **Request Schema:** `{ "name": "str (Required)", "domain": "Optional[str]", "website_url": "Optional[str]" }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/organizations/{organization_id}`** | **Response Schema:** Organization details and list of associated CRM people.
- **`PATCH /api/v1/organizations/{organization_id}`** | **Request Schema:** `{ "name": "Optional[str]", "description": "Optional[str]" }`.

---

### 2.7 Interactions & Communication Logs
- **`GET /api/v1/interactions`** | **Query Params:** `person_id`, `venture_id`, `interaction_type`, `limit`, `cursor`.
- **`POST /api/v1/interactions`**
  - **Request Schema:** `{ "title": "str (Required)", "person_id": "Optional[UUID]", "venture_id": "Optional[UUID]", "interaction_type": "str (default 'meeting')", "summary": "Optional[str]", "key_takeaways": ["str"], "next_actions": ["str"] }`
  - **Response:** HTTP 201 Created. (Note: Automatically triggers background pgvector embedding indexing job for RAG retrieval).
- **`GET /api/v1/interactions/{interaction_id}`** | **Response Schema:** Detailed interaction notes, takeaways, and markdown sync paths.
- **`PATCH /api/v1/interactions/{interaction_id}`** | **Request Schema:** `{ "summary": "Optional[str]", "key_takeaways": ["str"] }`.
- **`DELETE /api/v1/interactions/{interaction_id}`** | **Purpose:** Soft-delete interaction log from active query views.

---

### 2.8 Meetings
- **`GET /api/v1/meetings`** | **Query Params:** `venture_id`, `limit`, `cursor`.
- **`POST /api/v1/meetings`** | **Request Schema:** `{ "title": "str", "meeting_date": "ISO8601", "duration_minutes": "Optional[int]", "location": "Optional[str]", "participant_person_ids": ["UUID"] }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/meetings/{meeting_id}`** | **Response Schema:** Meeting metadata, participant roster, recording Blob URLs, and AI transcripts.
- **`PATCH /api/v1/meetings/{meeting_id}`** | **Request Schema:** `{ "transcript_text": "Optional[str]", "ai_summary": "Optional[str]", "action_items": ["str"] }`.
- **`DELETE /api/v1/meetings/{meeting_id}`** | **Purpose:** Soft-delete meeting archive from canonical view.

---

### 2.9 Memories & Reflective Captures
- **`GET /api/v1/memories`** | **Query Params:** `category`, `tag`, `linked_venture_id`, `limit`, `cursor`.
- **`POST /api/v1/memories`**
  - **Request Schema:** `{ "title": "str", "content": "str", "category": "Optional[str]", "tags": ["str"], "linked_venture_id": "Optional[UUID]", "linked_person_id": "Optional[UUID]" }` | **Response:** HTTP 201 Created (Dispatches instant pgvector indexing worker).
- **`GET /api/v1/memories/{memory_id}`** | **Response:** Memory contents with linked entity metadata.
- **`PATCH /api/v1/memories/{memory_id}`** | **Request Schema:** `{ "title": "Optional[str]", "content": "Optional[str]", "tags": ["str"] }`.
- **`DELETE /api/v1/memories/{memory_id}`** | **Purpose:** Soft-delete memory from active dashboard stream.

---

### 2.10 Idea Vault & Strategic Validator
- **`GET /api/v1/ideas`** | **Query Params:** `status`, `venture_id`, `limit`, `cursor`.
- **`POST /api/v1/ideas`** | **Request Schema:** `{ "title": "str", "problem": "Optional[str]", "solution": "Optional[str]", "market": "Optional[str]", "potential_score": "Optional[int (1-10)]" }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/ideas/{idea_id}`** | **Response Schema:** Idea analysis details and previous AI validation reports.
- **`PATCH /api/v1/ideas/{idea_id}`** | **Request Schema:** `{ "problem": "Optional[str]", "potential_score": "Optional[int]", "status": "Optional[str]" }`.
- **`DELETE /api/v1/ideas/{idea_id}`** | **Purpose:** Archive idea (`status = 'archived'`).
- **`POST /api/v1/ideas/{idea_id}/convert-to-project`**
  - **Purpose:** Transforms a validated idea into an actionable execution project.
  - **Request Schema:** `{ "venture_id": "Optional[UUID]", "target_date": "Optional[date]" }`
  - **Response Schema:** HTTP 201 Created `{ "data": { "new_project_id": "uuid", "idea_status": "converted" } }`.
- **`POST /api/v1/ideas/{idea_id}/analyze`**
  - **Purpose:** Invokes Gemini LLM Provider to conduct deep market evaluation and competitor analysis on the stored idea.
  - **Response Schema:** `{ "data": { "similar_products": ["str"], "market_opportunities": "str", "execution_requirements": ["str"], "recommended_next_step": "str" } }` | **Rate Limit:** 30 req/min.

---

### 2.11 Decisions Ledger
- **`GET /api/v1/decisions`** | **Query Params:** `venture_id`, `project_id`, `limit`, `cursor`.
- **`POST /api/v1/decisions`** | **Request Schema:** `{ "title": "str", "context_description": "str", "chosen_option": "str", "options_considered": ["str"], "venture_id": "Optional[UUID]" }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/decisions/{decision_id}`** | **Response:** Decision record with historical context and expected consequence projections.
- **`PATCH /api/v1/decisions/{decision_id}`** | **Request Schema:** `{ "expected_consequences": "Optional[str]", "tags": ["str"] }`.

---

### 2.12 Documents & Attachment Processing
- **`GET /api/v1/documents`** | **Query Params:** `venture_id`, `processing_status`, `limit`, `cursor`.
- **`POST /api/v1/documents`**
  - **Purpose:** Register metadata for a newly uploaded Blob situated in Supabase Storage private buckets and trigger text extraction.
  - **Request Schema:** `{ "file_name": "str", "storage_path": "str", "file_size_bytes": "int", "mime_type": "str", "venture_id": "Optional[UUID]" }` | **Response:** HTTP 202 Accepted `{ "data": { "id": "uuid", "processing_status": "pending", "job_id": "job-uuid" } }`.
- **`GET /api/v1/documents/{document_id}`** | **Response Schema:** Returns document properties plus a short-lived **Cryptographically Signed Private Storage Download URL** (`signed_download_url`).
- **`DELETE /api/v1/documents/{document_id}`** | **Purpose:** Mark file as deleted and queue worker to purge blob from Supabase Storage.
- **`POST /api/v1/documents/{document_id}/process`** | **Purpose:** Manually re-trigger text extraction and pgvector chunk indexing. | **Response:** HTTP 202 Accepted `{ "data": { "job_id": "uuid" } }`.
- **`GET /api/v1/documents/{document_id}/processing-status`** | **Response Schema:** `{ "data": { "document_id": "uuid", "processing_status": "completed", "chunks_indexed": 14, "error_message": null } }`.

---

### 2.13 Search & RAG Hybrid Retrieval
- **`POST /api/v1/search`** (Universal Quick-Search)
  - **Request Schema:** `{ "query": "str (Required)", "limit": "Optional[int (default 10)]" }`
  - **Response Schema:** Merged array of matching Ventures, People, Projects, and Tasks across all operational tables.
- **`POST /api/v1/search/keyword`** | **Request Schema:** `{ "query": "str", "entity_types": ["str"] }` | **Response:** FTS Trigram matched records.
- **`POST /api/v1/search/semantic`** | **Request Schema:** `{ "query": "str", "top_k": "Optional[int (default 5)]", "similarity_threshold": "Optional[float (default 0.55)]" }` | **Response:** Pure pgvector cosine distance ranked memory chunks.
- **`POST /api/v1/search/hybrid`**
  - **Purpose:** Authoritative RAG retrieval engine using Reciprocal Rank Fusion (RRF) combining vector similarity and keyword accuracy.
  - **Request Schema:** `{ "query": "str (Required)", "top_k": 5, "threshold": 0.55, "entity_types": ["Optional[str]"] }`
  - **Response Schema:**
    ```json
    {
      "data": [
        {
          "chunk_id": "uuid",
          "entity_type": "interaction",
          "entity_id": "uuid",
          "title": "Meeting with Yousuf Imran",
          "snippet": "Discussed customer retention metrics for Justor AI...",
          "rrf_score": 0.032,
          "similarity": 0.84,
          "citation_url": "https://app.tajssecondbrain.ai/people/uuid#interaction-uuid"
        }
      ]
    }
    ```
- **`POST /api/v1/search/reindex`** | **Purpose:** Initiate full background database re-embedding cycle after vector model migration. | **Response:** HTTP 202 Accepted `{ "data": { "job_id": "uuid" } }`.
- **`GET /api/v1/search/reindex/{job_id}`** | **Response Schema:** `{ "data": { "job_id": "uuid", "status": "processing", "processed_records": 120, "total_records": 450 } }`.

---

### 2.14 AI Assistant & Streaming Chat
- **`GET /api/v1/ai/conversations`** | **Query Params:** `limit`, `cursor`. | **Response:** List of historical chat sessions with the AI Founder Coach.
- **`POST /api/v1/ai/conversations`** | **Request Schema:** `{ "title": "Optional[str]", "context_venture_id": "Optional[UUID]" }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/ai/conversations/{conversation_id}`** | **Response:** Full transcript of `ai_messages` within the session.
- **`DELETE /api/v1/ai/conversations/{conversation_id}`** | **Purpose:** Soft-delete conversation archive.
- **`POST /api/v1/ai/chat`** (Synchronous Execution)
  - **Request Schema:** `{ "conversation_id": "UUID", "prompt": "str", "model": "Optional[str (default 'gemini-1.5-pro')]" }`
  - **Response Schema:** `{ "data": { "message_id": "uuid", "role": "assistant", "content": "str", "citations": [ { "id": "uuid", "title": "str" } ], "usage": { "prompt_tokens": 45, "completion_tokens": 150 } } }`.
- **`POST /api/v1/ai/chat/stream`** (Authoritative Real-Time Streaming Endpoint)
  - **Protocol & Header:** Server-Sent Events (SSE) | `Content-Type: text/event-stream` | See Section 3 for detailed frame specification.

---

### 2.15 Life KPIs Growth Matrix
- **`GET /api/v1/kpis`** | **Query Params:** `category` (founder | network | learning), `limit`, `cursor`. | **Response:** List of target KPI Definitions with latest calculated progress.
- **`POST /api/v1/kpis`** | **Request Schema:** `{ "category": "str", "metric_name": "str", "target_value": "numeric", "unit": "str (default 'count')", "period": "str (default 'weekly')" }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/kpis/{kpi_id}`** | **Response:** KPI Definition plus historical progress chart coordinates.
- **`PATCH /api/v1/kpis/{kpi_id}`** | **Request Schema:** `{ "target_value": "Optional[numeric]", "metric_name": "Optional[str]" }`.
- **`POST /api/v1/kpis/{kpi_id}/entries`** | **Request Schema:** `{ "recorded_value": "numeric (Required)", "notes": "Optional[str]", "recording_date": "Optional[YYYY-MM-DD]" }` | **Response:** HTTP 201 Created. Updates parent `current_value`.
- **`GET /api/v1/kpis/{kpi_id}/entries`** | **Query Params:** `start_date`, `end_date`. | **Response:** Chronological time-series check-ins.

---

### 2.16 Achievements & Career Proof Portfolio
- **`GET /api/v1/achievements`** | **Query Params:** `venture_id`, `limit`, `cursor`. | **Response:** Paginated milestone achievements.
- **`POST /api/v1/achievements`** | **Request Schema:** `{ "title": "str", "role": "str", "problem": "Optional[str]", "responsibilities": ["str"], "impact": "str", "skills": ["str"], "venture_id": "Optional[UUID]" }` | **Response:** HTTP 201 Created.
- **`GET /api/v1/achievements/{achievement_id}`** | **Response:** Detailed achievement record and demonstrated skill tags.
- **`PATCH /api/v1/achievements/{achievement_id}`** | **Request Schema:** `{ "impact": "Optional[str]", "skills": ["str"] }`.
- **`POST /api/v1/portfolio/generate`**
  - **Purpose:** Commands AI to assemble a comprehensive Career Proof Case Study tailored for targeted roles (e.g., AI Product Manager).
  - **Request Schema:** `{ "target_role": "str (Required)", "selected_achievement_ids": ["UUID (Required)"], "tone": "Optional[str]" }`
  - **Response Schema:** HTTP 201 Created `{ "data": { "case_study_id": "uuid", "title": "str", "executive_summary": "str", "markdown_content": "str" } }`.
- **`GET /api/v1/portfolio/case-studies`** | **Response:** List of generated portfolio case studies.
- **`POST /api/v1/portfolio/case-studies`** | **Purpose:** Save a manually drafted career case study without AI generation.
- **`PATCH /api/v1/portfolio/case-studies/{case_study_id}`** | **Request Schema:** `{ "executive_summary": "Optional[str]", "full_markdown_case": "Optional[str]", "is_public": "Optional[bool]" }`.

---

### 2.17 AI Content Engine Studio
- **`GET /api/v1/content`** | **Query Params:** `content_type` (linkedin_post | founder_story | article), `status`, `limit`, `cursor`.
- **`POST /api/v1/content/generate`**
  - **Purpose:** Generates authentic social content drafts grounded in Taj's stored founder memories and achievements.
  - **Request Schema:** `{ "content_type": "str (Required)", "topic": "str (Required)", "target_audience": "Optional[str]", "tone": "Optional[str (default 'Retro-editorial founder perspective')]" }`
  - **Response Schema:** HTTP 201 Created `{ "data": { "content_id": "uuid", "title": "str", "current_body": "str", "cited_records": [ { "id": "uuid", "title": "str" } ] } }`.
- **`GET /api/v1/content/{content_id}`** | **Response:** Current content draft, cited sources, and status.
- **`PATCH /api/v1/content/{content_id}`** | **Request Schema:** `{ "current_body": "Optional[str]", "status": "Optional[str (draft|review|published)]", "published_url": "Optional[str]" }` (Note: Modifying `current_body` automatically creates an immutable revision row in `content_versions`).
- **`POST /api/v1/content/{content_id}/versions`** | **Purpose:** Manually snapshot current drafting state into version history.
- **`GET /api/v1/content/{content_id}/versions`** | **Response:** Array of historical editing drafts with timestamps and change summaries.
- **`POST /api/v1/content/{content_id}/restore-version`**
  - **Request Schema:** `{ "version_number": "int (Required)" }` | **Response:** Reverts `current_body` to specified historical snapshot.

---

### 2.18 Weekly Strategic Reviews
- **`GET /api/v1/weekly-reviews`** | **Query Params:** `year`, `limit`, `cursor`. | **Response:** Chronological archive of weekly performance reflections.
- **`POST /api/v1/weekly-reviews/generate`**
  - **Purpose:** Trigger automated AI analysis of week's completed tasks, relationship touches, and KPI check-ins to synthesize reflective feedback.
  - **Request Schema:** `{ "year": "Optional[int]", "week_number": "Optional[int]" }` (Defaults to current week).
  - **Response Schema:** HTTP 201 Created `{ "data": { "id": "uuid", "wins_summary": "str", "bottleneck_analysis": "str", "next_week_focus": ["str"] } }`.
- **`GET /api/v1/weekly-reviews/{review_id}`** | **Response Schema:** Detailed weekly evaluation and accompanying KPI statistics snapshot.
- **`PATCH /api/v1/weekly-reviews/{review_id}`** | **Request Schema:** `{ "next_week_focus": ["str"], "wins_summary": "Optional[str]" }`.

---

### 2.19 External Cloud Integrations
- **`GET /api/v1/integrations`** | **Response Schema:** `{ "data": [ { "provider": "google_calendar", "account_email": "str", "status": "connected", "expires_at": "timestamp" } ] }`.
- **`POST /api/v1/integrations/google/connect`** | **Request Schema:** `{ "redirect_url": "Optional[str]" }` | **Response:** `{ "data": { "oauth_authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?..." } }`.
- **`GET /api/v1/integrations/google/callback`** | **Query Params:** `code`, `state`, `error`. | **Response:** HTTP 302 Redirect to `/settings/integrations?status=success` after encrypting access/refresh tokens in DB.
- **`POST /api/v1/integrations/google/disconnect`** | **Request Schema:** `{ "provider": "str (google_calendar | google_drive)" }` | **Response:** Hard-deletes encrypted connection tokens from DB table; returns `{ "data": { "status": "disconnected" } }`.
- **`POST /api/v1/integrations/google/revoke`** | **Purpose:** Disconnects AND transmits HTTP revocation request to Google Authorization servers to destroy token validities remotely.
- **`POST /api/v1/integrations/google-drive/sync`** | **Purpose:** Manually queue asynchronous Cloud Backup upload to Google Drive. | **Response:** HTTP 202 Accepted `{ "data": { "job_id": "uuid" } }`.
- **`POST /api/v1/integrations/google-calendar/sync`** | **Purpose:** Trigger background task to synchronizing pending task due dates with primary Google Calendar. | **Response:** HTTP 202 Accepted `{ "data": { "job_id": "uuid" } }`.
- **`GET /api/v1/integrations/sync-jobs`** | **Query Params:** `job_type`, `status`, `limit`. | **Response:** List of queued and executed background tasks.
- **`GET /api/v1/integrations/sync-jobs/{job_id}`** | **Response Schema:** `{ "data": { "job_id": "uuid", "job_type": "gdrive_backup", "status": "completed", "error_details": null, "finished_at": "timestamp" } }`.

---

### 2.20 Universal Knowledge Export
- **`POST /api/v1/exports/record`** | **Request Schema:** `{ "entity_type": "str (person|venture|meeting)", "entity_id": "UUID" }` | **Response:** Exploded YAML-Frontmatter markdown string for immediate UI download or file saving.
- **`POST /api/v1/exports/module`** | **Request Schema:** `{ "target_module": "str (People|Ventures|Meetings|Ideas)" }` | **Response:** HTTP 202 Accepted `{ "data": { "job_id": "uuid", "export_scope": "module" } }`.
- **`POST /api/v1/exports/full`** | **Purpose:** Initiates background worker to generate complete Obsidian-compatible directory snapshot (`knowledge/Founder_OS/`) and package into compressed `.zip`. | **Response:** HTTP 202 Accepted `{ "data": { "job_id": "uuid", "export_scope": "full" } }`.
- **`GET /api/v1/exports`** | **Response:** List of historical export generation jobs and expiration statuses.
- **`GET /api/v1/exports/{export_id}`** | **Response Schema:** `{ "data": { "id": "uuid", "status": "completed", "file_size_bytes": 45120, "download_url": "https://[storage]/exports/backup_20260802.zip?signature=..." } }`.
- **`GET /api/v1/exports/{export_id}/download`** | **Response:** HTTP 302 Redirect directly to signed secure ZIP Blob download URI.
- **`POST /api/v1/exports/{export_id}/retry`** | **Purpose:** Re-queues a failed export background job; increments retry count.

---

## 3. Authoritative AI Streaming Contract (Vercel Data-Stream Protocol)

To eliminate interface freezes during deep LLM generation, endpoint `POST /api/v1/ai/chat/stream` utilizes **Server-Sent Events (SSE)** structured according to the **Vercel AI SDK Data-Stream specification** ([ADR-012](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-012-ai-streaming-protocol)).

### Transmission Protocol Rules & Event Frames
The FastAPI asynchronous generator (`StreamingResponse`) emits newline-delimited operational text packets:
1. **Start Event (Session Initiation):** Emits conversation confirmation block immediately upon socket attachment:
   ```text
   f:{"conversationId":"conv-8f3a-uuid","model":"gemini-1.5-pro"}\n
   ```
2. **Text Delta Events (Token Chunks):** Streamed real-time generation fragments prefixed by token tag `0:`:
   ```text
   0:"Based on your discussion with Yousuf Imran"\n
   0:", your primary focus should remain on"\n
   0:" narrow MVP scoping and customer retention."\n
   ```
3. **Citation Event (RAG Grounding Proof):** Emits real-time citation links whenever retrieved context is referenced:
   ```text
   e:{"type":"citation","id":"mem-104","entity_type":"interaction","title":"Founder Meetup Dhaka","uri":"/people/uuid#interaction-mem-104"}\n
   ```
4. **Tool Execution Event (MCP & Function Visibility):** Emits status updates if AI invokes memory search tools during reasoning:
   ```text
   9:{"toolCallId":"call_12a","toolName":"search_memory","args":{"query":"Justor AI MVP customer retention"}}\n
   a:{"toolCallId":"call_12a","result":"Retrieved 2 relevant conversation takeaways from Mangosteen Studio notes."}\n
   ```
5. **Usage Event (Token Consumption & Audit Metrics):** Transmits final LLM billing token totals prior to stream closure:
   ```text
   d:{"finishReason":"stop","usage":{"promptTokens":128,"completionTokens":45,"totalTokens":173}}\n
   ```
6. **Error Event (Controlled Exception Abort):** Transmitted immediately if LLM provider fails or session token expires mid-stream:
   ```text
   3:"LLM rate limit saturated on primary provider. Fallback OpenAI provider also unreachable. Please retry in 30 seconds."\n
   ```
7. **Client Cancellation Protocol:** If the founder clicks "Stop Generating" or closes the dashboard tab, the browser terminates the TCP underlying socket connection (`GET / HTTP/1.1 -> FIN/RST`). The FastAPI server catches `asyncio.CancelledError`, immediately aborts generation cycles with Google Gemini cloud servers to preserve token billing, and records partial output transcripts into `public.ai_messages` marked as `status='aborted'`.

---

## 4. MCP Server Tool Contracts Summary

For external desktop AI clients (Claude Desktop, ChatGPT, Gemini CLI), the standalone Python MCP Server (`apps/mcp-server/`) exposes 9 authenticated tool interfaces communicating over JSON-RPC Stdio / SSE via `X-MCP-API-KEY` authorization. For exhaustive tool arguments, return payloads, and read-only security enforcement details, reference [docs/architecture/mcp_architecture.md](file:///e:/second%20brain/docs/architecture/mcp_architecture.md).

1. `search_people`: Query Founder CRM contacts, mentors, and investors by expertise tags or industry.
2. `search_memory`: Execute hybrid pgvector + keyword similarity searches across stored memories, notes, and decisions.
3. `get_projects`: Retrieve active venture project pipelines, completion statuses, and milestone target dates.
4. `get_tasks`: Pull open action items, due dates, and urgent task priorities scheduled for today or upcoming sprints.
5. `get_calendar`: Scan synchronized schedule meetings and task deadlines up to 30 days ahead.
6. `get_relationship_history`: Reconstruct chronological conversation notes and past advice timelines for specific contacts.
7. `generate_linkedin_post`: Draft authentic social updates based on documented startup achievements (Draft Stage only).
8. `generate_case_study`: Compile professional career proof case studies for executive presentations (Draft/Read Stage).
9. `generate_weekly_review`: Assess past week task completion rates, network connections, and learning KPI growth (Read/Draft Stage).
