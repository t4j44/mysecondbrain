# Database Schema & Data Specification - Taj's Second Brain

Version: 2.0 (Comprehensive Logical Database Specification)  
Author: Agent 1 — Architecture and Contracts Agent  
Approved by: Agent 0 — Lead Orchestrator  
Engine: Supabase PostgreSQL 15+  
Required Extensions: `uuid-ossp`, `vector` (`pgvector`), `pg_trgm`, `btree_gin`

---

## 1. Core Ownership & Row Level Security (RLS) Rules

Every database table in Taj's Second Brain must enforce strict Row Level Security (RLS). Under zero circumstances is an application record accessible without cryptographic validation against Supabase Auth sessions.

### The Absolute Universal RLS Default Rule:
```text
The authenticated user may access only records owned by that user (auth.uid() = user_id).
```

### Ownership Inheritance Rules:
1. **Direct User-Owned Tables:** Primary entities (`profiles`, `organizations`, `people`, `ventures`, `projects`, `tasks`, `meetings`, `memories`, `ideas`, `decisions`, `documents`, `achievements`, `kpi_definitions`, `content_items`, `ai_conversations`, `weekly_reviews`, `integrations`, `sync_jobs`, `export_jobs`, `audit_logs`) directly contain a mandatory `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE` column.
2. **Child & Junction Tables:** Dependent tables (`project_members`, `task_comments`, `meeting_participants`, `document_chunks`, `embeddings`, `kpi_entries`, `content_versions`, `ai_messages`, `relationships`, `interactions`, `portfolio_case_studies`) MUST also explicitly embed a `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE` column in addition to foreign keys pointing to parent records. This avoids slow recursive RLS JOIN evaluations during permission verification and guarantees atomic isolation across all query planners.

---

## 2. PostgreSQL Enums vs. Constrained Text Strategy

Following architectural evaluation ([ADR-011](file:///e:/second%20brain/docs/architecture/architecture_decisions.md#adr-011-soft-delete-and-archival-strategy)), **native PostgreSQL `ENUM` types are explicitly rejected for evolving business categorizations** (such as CRM relationship types or content statuses) because adding enum values in production Postgres requires complex exclusive locks and difficult database migrations.
- **Decision:** Use **Constrained Text Fields with explicit SQL `CHECK` constraints** or lookup tables for domain statuses. This guarantees data integrity while preserving schema migration flexibility.

### Standard Evaluated Check Constraints:
- `task_status_check`: `CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled', 'archived'))`
- `task_priority_check`: `CHECK (priority IN ('low', 'medium', 'high', 'urgent'))`
- `project_status_check`: `CHECK (status IN ('planning', 'in_progress', 'completed', 'on_hold', 'archived'))`
- `venture_status_check`: `CHECK (status IN ('active', 'paused', 'exited', 'archived'))`
- `idea_status_check`: `CHECK (status IN ('draft', 'validating', 'executing', 'converted', 'archived'))`
- `relationship_type_check`: `CHECK (relationship_type IN ('mentor', 'investor', 'peer', 'collaborator', 'lead', 'client', 'contact'))`
- `interaction_type_check`: `CHECK (interaction_type IN ('meeting', 'call', 'email', 'chat', 'event', 'note'))`
- `content_status_check`: `CHECK (status IN ('draft', 'review', 'published', 'archived'))`
- `job_status_check`: `CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retried'))`
- `doc_status_check`: `CHECK (status IN ('pending', 'processing', 'completed', 'failed'))`

---

## 3. Universal Deletion Strategy (No Destructive Cascading)

To preserve long-term institutional founder memory and prevent accidental destruction of historical intelligence:
- **Hard Delete Restriction:** Destructive database `DELETE` statements are explicitly banned for primary intellectual property entities (`ventures`, `projects`, `tasks`, `people`, `organizations`, `memories`, `ideas`, `decisions`, `documents`).
- **Soft Delete / Archival Columns:** All primary tables incorporate a mandatory `deleted_at TIMESTAMPTZ NULL` column and an archival status state. Removing an item in the UI transitions `status = 'archived'` or sets `deleted_at = NOW()`.
- **Relationship Detachment (`ON DELETE SET NULL`):** Foreign key links from immutable historical records (e.g., `interactions`, `memories`, `decisions`) pointing to parent containers (`ventures`, `projects`, `people`) must declare `ON DELETE SET NULL` or refer to archived records rather than executing cascading wipes.
- **Audit Retentiveness:** `audit_logs` are strictly append-only and cannot be soft-deleted or hard-deleted by normal application users.

---

## 4. Comprehensive Table Specifications (31+ Required Tables)

### 4.1 Core Profiles & Organizations

#### `profiles`
- **Purpose:** Extends Supabase `auth.users` with founder operational preferences, avatar images, and global system configuration toggles.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE`
  - `email TEXT NOT NULL UNIQUE`
  - `full_name TEXT NULL`
  - `avatar_url TEXT NULL`
  - `bio TEXT NULL`
  - `settings JSONB NOT NULL DEFAULT '{}'::jsonb` (Stores theme preferences and encrypted MCP tokens)
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_profiles_email ON public.profiles(email);`
- **RLS Policy:** `CREATE POLICY "Profiles user isolation" ON public.profiles FOR ALL USING (id = auth.uid());`

#### `organizations`
- **Purpose:** Stores corporate enterprises, venture capital funds, startup incubators, and client firms associated with people in the Founder CRM.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `name TEXT NOT NULL`
  - `domain TEXT NULL`
  - `industry TEXT NULL`
  - `location TEXT NULL`
  - `website_url TEXT NULL`
  - `description TEXT NULL`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Constraints:** `UNIQUE(user_id, name)` (within non-deleted scope)
- **Indexes:** `CREATE INDEX idx_orgs_user_name ON public.organizations(user_id, name) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Organizations user isolation" ON public.organizations FOR ALL USING (user_id = auth.uid());`

---

### 4.2 Founder CRM & Relationship Intelligence

#### `people`
- **Purpose:** Primary directory table for Network Intelligence CRM, recording mentors, investors, peers, and strategic collaborators.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `organization_id UUID NULL REFERENCES public.organizations(id) ON DELETE SET NULL`
  - `name TEXT NOT NULL`
  - `role TEXT NULL`
  - `company TEXT NULL` (Cached representation or unlinked firm name)
  - `industry TEXT NULL`
  - `location TEXT NULL`
  - `email TEXT NULL`
  - `phone TEXT NULL`
  - `linkedin_url TEXT NULL`
  - `relationship_type TEXT NOT NULL DEFAULT 'contact' CHECK (relationship_type IN ('mentor', 'investor', 'peer', 'collaborator', 'lead', 'client', 'contact'))`
  - `last_interaction_at TIMESTAMPTZ NULL`
  - `notes TEXT NULL`
  - `tags TEXT[] NOT NULL DEFAULT '{}'`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** 
  - `CREATE INDEX idx_people_user_name ON public.people(user_id, name) WHERE deleted_at IS NULL;`
  - `CREATE INDEX idx_people_tags ON public.people USING GIN(tags) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "People user isolation" ON public.people FOR ALL USING (user_id = auth.uid());`

#### `relationships` (Junction / Graph Table)
- **Purpose:** Maps multi-directional relationships between different people in the CRM (e.g., Person A introduced Person B, or Person A is co-founder with Person B).
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `source_person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE`
  - `target_person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE`
  - `relationship_nature TEXT NOT NULL` (e.g., 'introduced', 'co-investor', 'former-colleague')
  - `notes TEXT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Constraints:** `CHECK (source_person_id != target_person_id)`, `UNIQUE(user_id, source_person_id, target_person_id, relationship_nature)`
- **Indexes:** `CREATE INDEX idx_relationships_nodes ON public.relationships(source_person_id, target_person_id);`
- **RLS Policy:** `CREATE POLICY "Relationships user isolation" ON public.relationships FOR ALL USING (user_id = auth.uid());`

#### `interactions`
- **Purpose:** Immutable communication journal capturing meetings, advisor calls, coffee chats, and email thread digests.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `person_id UUID NULL REFERENCES public.people(id) ON DELETE SET NULL`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `interaction_type TEXT NOT NULL DEFAULT 'meeting' CHECK (interaction_type IN ('meeting', 'call', 'email', 'chat', 'event', 'note'))`
  - `title TEXT NOT NULL`
  - `summary TEXT NULL`
  - `date TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `key_takeaways TEXT[] NOT NULL DEFAULT '{}'`
  - `next_actions TEXT[] NOT NULL DEFAULT '{}'`
  - `markdown_path TEXT NULL` (Filesystem canonical backup reference)
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_interactions_person_date ON public.interactions(user_id, person_id, date DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Interactions user isolation" ON public.interactions FOR ALL USING (user_id = auth.uid());`

---

### 4.3 Execution Command (Ventures, Projects, Tasks)

#### `ventures`
- **Purpose:** Primary root organization container for Taj’s startup initiatives (Justor AI, Zqtion, IEXF, CMOOS, custom projects).
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `name TEXT NOT NULL`
  - `slug TEXT NOT NULL`
  - `vision TEXT NULL`
  - `mission TEXT NULL`
  - `status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'exited', 'archived'))`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Constraints:** `UNIQUE(user_id, slug)`
- **Indexes:** `CREATE INDEX idx_ventures_user_status ON public.ventures(user_id, status) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Ventures user isolation" ON public.ventures FOR ALL USING (user_id = auth.uid());`

#### `projects`
- **Purpose:** Actionable project execution pipelines residing within or independent of ventures.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `name TEXT NOT NULL`
  - `description TEXT NULL`
  - `status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('planning', 'in_progress', 'completed', 'on_hold', 'archived'))`
  - `target_date DATE NULL`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_projects_venture ON public.projects(user_id, venture_id, status) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Projects user isolation" ON public.projects FOR ALL USING (user_id = auth.uid());`

#### `project_members` (Junction Table)
- **Purpose:** Associates CRM people (collaborators, advisors, co-founders) with specific projects.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE`
  - `person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE`
  - `role_in_project TEXT NULL` (e.g., 'Advisor', 'Lead Engineer', 'UI Designer')
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Constraints:** `UNIQUE(project_id, person_id)`
- **Indexes:** `CREATE INDEX idx_project_members_lookup ON public.project_members(project_id, person_id);`
- **RLS Policy:** `CREATE POLICY "Project members user isolation" ON public.project_members FOR ALL USING (user_id = auth.uid());`

#### `tasks`
- **Purpose:** Linear/Notion-inspired operational execution tasks linked to projects, ventures, or CRM follow-ups.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `project_id UUID NULL REFERENCES public.projects(id) ON DELETE SET NULL`
  - `person_id UUID NULL REFERENCES public.people(id) ON DELETE SET NULL`
  - `title TEXT NOT NULL`
  - `description TEXT NULL`
  - `status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled', 'archived'))`
  - `priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent'))`
  - `due_date TIMESTAMPTZ NULL`
  - `completed_at TIMESTAMPTZ NULL`
  - `gcal_event_id TEXT NULL` (Google Calendar bidirectional sync linkage)
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** 
  - `CREATE INDEX idx_tasks_user_status_priority ON public.tasks(user_id, status, priority) WHERE deleted_at IS NULL;`
  - `CREATE INDEX idx_tasks_due_date ON public.tasks(user_id, due_date) WHERE deleted_at IS NULL AND status != 'done';`
- **RLS Policy:** `CREATE POLICY "Tasks user isolation" ON public.tasks FOR ALL USING (user_id = auth.uid());`

#### `task_comments`
- **Purpose:** Stores chronological progress update logs, notes, and AI execution recommendations attached to tasks.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `task_id UUID NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE`
  - `content TEXT NOT NULL`
  - `author_type TEXT NOT NULL DEFAULT 'user' CHECK (author_type IN ('user', 'ai_assistant', 'system'))`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** `CREATE INDEX idx_task_comments_task ON public.task_comments(task_id, created_at);`
- **RLS Policy:** `CREATE POLICY "Task comments user isolation" ON public.task_comments FOR ALL USING (user_id = auth.uid());`

---

### 4.4 Meetings & Unstructured Memory Archives

#### `meetings`
- **Purpose:** Structured record of official calendar appointments, startup pitches, team reviews, and recorded conferences.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `title TEXT NOT NULL`
  - `meeting_date TIMESTAMPTZ NOT NULL`
  - `duration_minutes INT NULL`
  - `location TEXT NULL`
  - `recording_url TEXT NULL` (Link to Supabase Storage voice blob)
  - `transcript_text TEXT NULL`
  - `ai_summary TEXT NULL`
  - `action_items TEXT[] NOT NULL DEFAULT '{}'`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_meetings_user_date ON public.meetings(user_id, meeting_date DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Meetings user isolation" ON public.meetings FOR ALL USING (user_id = auth.uid());`

#### `meeting_participants` (Junction Table)
- **Purpose:** Links CRM contacts (`people`) as verified attendees to formal meetings.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE`
  - `person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE`
  - `attendance_status TEXT NOT NULL DEFAULT 'attended' CHECK (attendance_status IN ('invited', 'attended', 'absent'))`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Constraints:** `UNIQUE(meeting_id, person_id)`
- **Indexes:** `CREATE INDEX idx_meeting_participants_join ON public.meeting_participants(meeting_id, person_id);`
- **RLS Policy:** `CREATE POLICY "Meeting participants user isolation" ON public.meeting_participants FOR ALL USING (user_id = auth.uid());`

#### `memories`
- **Purpose:** Freeform reflective capture vault for personal insights, lessons learned, executive epiphanies, and voice memos.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `title TEXT NOT NULL`
  - `content TEXT NOT NULL`
  - `category TEXT NULL` (e.g., 'lesson', 'quote', 'observation', 'win', 'failure')
  - `tags TEXT[] NOT NULL DEFAULT '{}'`
  - `linked_venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `linked_person_id UUID NULL REFERENCES public.people(id) ON DELETE SET NULL`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** 
  - `CREATE INDEX idx_memories_user_created ON public.memories(user_id, created_at DESC) WHERE deleted_at IS NULL;`
  - `CREATE INDEX idx_memories_tags ON public.memories USING GIN(tags) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Memories user isolation" ON public.memories FOR ALL USING (user_id = auth.uid());`

---

### 4.5 Strategy & Idea Vault

#### `ideas`
- **Purpose:** Storehouse for early-stage startup ideation, problem-solution formulation, and AI market feasibility scores.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `title TEXT NOT NULL`
  - `problem TEXT NULL`
  - `solution TEXT NULL`
  - `market TEXT NULL`
  - `potential_score INT NULL CHECK (potential_score >= 1 AND potential_score <= 10)`
  - `ai_validation_summary TEXT NULL`
  - `status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'validating', 'executing', 'converted', 'archived'))`
  - `next_steps TEXT NULL`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_ideas_user_status ON public.ideas(user_id, status, potential_score DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Ideas user isolation" ON public.ideas FOR ALL USING (user_id = auth.uid());`

#### `decisions`
- **Purpose:** Executive architecture and startup decision ledger documenting rationales, trade-offs, and historical context.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `project_id UUID NULL REFERENCES public.projects(id) ON DELETE SET NULL`
  - `title TEXT NOT NULL`
  - `context_description TEXT NOT NULL`
  - `chosen_option TEXT NOT NULL`
  - `options_considered TEXT[] NOT NULL DEFAULT '{}'`
  - `expected_consequences TEXT NULL`
  - `decision_date DATE NOT NULL DEFAULT CURRENT_DATE`
  - `tags TEXT[] NOT NULL DEFAULT '{}'`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_decisions_venture_date ON public.decisions(user_id, venture_id, decision_date DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Decisions user isolation" ON public.decisions FOR ALL USING (user_id = auth.uid());`

---

### 4.6 File Processing & pgvector RAG Pipeline

#### `documents`
- **Purpose:** Metadata tracking repository for uploaded PDFs, legal agreements, slide decks, and external attachments residing in Supabase Storage.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `project_id UUID NULL REFERENCES public.projects(id) ON DELETE SET NULL`
  - `file_name TEXT NOT NULL`
  - `storage_path TEXT NOT NULL UNIQUE` (Supabase storage private path)
  - `file_size_bytes BIGINT NOT NULL`
  - `mime_type TEXT NOT NULL`
  - `processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))`
  - `extracted_text TEXT NULL`
  - `error_message TEXT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_documents_user_status ON public.documents(user_id, processing_status) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Documents user isolation" ON public.documents FOR ALL USING (user_id = auth.uid());`

#### `document_chunks`
- **Purpose:** Subdivided 500-token text window spans generated from documents, meeting transcripts, and interaction notes preparing for vectorization.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `document_id UUID NULL REFERENCES public.documents(id) ON DELETE CASCADE`
  - `entity_type TEXT NOT NULL` (e.g., 'document', 'meeting', 'interaction', 'memory', 'idea')
  - `entity_id UUID NOT NULL` (Polymorphic ID of source record)
  - `chunk_index INT NOT NULL`
  - `chunk_text TEXT NOT NULL`
  - `token_count INT NOT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** `CREATE INDEX idx_doc_chunks_entity ON public.document_chunks(entity_type, entity_id);`
- **RLS Policy:** `CREATE POLICY "Document chunks user isolation" ON public.document_chunks FOR ALL USING (user_id = auth.uid());`

#### `embeddings` (`public.memory_embeddings`)
- **Purpose:** Core neural memory search table storing high-dimensional numerical vector embeddings for low-latency RAG hybrid retrieval.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `chunk_id UUID NULL REFERENCES public.document_chunks(id) ON DELETE CASCADE`
  - `entity_type TEXT NOT NULL`
  - `entity_id UUID NOT NULL`
  - `content TEXT NOT NULL` (Replicated text payload for direct citation extraction)
  - `embedding vector(768)` (Configurable dimension; default 768 for Gemini `text-embedding-004`, 1536 for OpenAI)
  - `embedding_provider TEXT NOT NULL DEFAULT 'gemini'`
  - `embedding_model TEXT NOT NULL DEFAULT 'text-embedding-004'`
  - `embedding_version INT NOT NULL DEFAULT 1`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** 
  - `CREATE INDEX idx_embeddings_vector_ivf ON public.memory_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`
  - `CREATE INDEX idx_embeddings_fts ON public.memory_embeddings USING GIN (to_tsvector('english', content));`
  - `CREATE INDEX idx_embeddings_user_entity ON public.memory_embeddings(user_id, entity_type, entity_id);`
- **RLS Policy:** `CREATE POLICY "Memory Embeddings user isolation" ON public.memory_embeddings FOR ALL USING (user_id = auth.uid());`

---

### 4.7 Growth Metrics & Career Proof (KPIs & Portfolio)

#### `kpi_definitions`
- **Purpose:** Defines personal and startup growth target metrics across Founder, Network, and Learning categories.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `category TEXT NOT NULL CHECK (category IN ('founder', 'network', 'learning', 'venture'))`
  - `metric_name TEXT NOT NULL` (e.g., 'Projects Completed', 'Meaningful Connections', 'Books Read')
  - `target_value NUMERIC NOT NULL`
  - `current_value NUMERIC NOT NULL DEFAULT 0`
  - `unit TEXT NOT NULL DEFAULT 'count'`
  - `period TEXT NOT NULL DEFAULT 'weekly' CHECK (period IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly'))`
  - `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_kpi_user_category ON public.kpi_definitions(user_id, category) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "KPI definitions user isolation" ON public.kpi_definitions FOR ALL USING (user_id = auth.uid());`

#### `kpi_entries`
- **Purpose:** Time-series historical log of periodic KPI value check-ins and progress audits.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `kpi_id UUID NOT NULL REFERENCES public.kpi_definitions(id) ON DELETE CASCADE`
  - `recorded_value NUMERIC NOT NULL`
  - `notes TEXT NULL`
  - `recording_date DATE NOT NULL DEFAULT CURRENT_DATE`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Constraints:** `UNIQUE(kpi_id, recording_date)`
- **Indexes:** `CREATE INDEX idx_kpi_entries_timeline ON public.kpi_entries(kpi_id, recording_date DESC);`
- **RLS Policy:** `CREATE POLICY "KPI entries user isolation" ON public.kpi_entries FOR ALL USING (user_id = auth.uid());`

#### `achievements`
- **Purpose:** Milestone registry capturing validated startup victories, technical deliverables, and business outcomes.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `project_id UUID NULL REFERENCES public.projects(id) ON DELETE SET NULL`
  - `title TEXT NOT NULL`
  - `role TEXT NOT NULL` (e.g., 'Founder & AI Product Manager')
  - `problem TEXT NULL`
  - `responsibilities TEXT[] NOT NULL DEFAULT '{}'`
  - `impact TEXT NOT NULL` (Quantifiable user or technical value delivered)
  - `skills TEXT[] NOT NULL DEFAULT '{}'` (e.g., 'AI Workflow Design', 'Product Strategy')
  - `achievement_date DATE NOT NULL DEFAULT CURRENT_DATE`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_achievements_user_date ON public.achievements(user_id, achievement_date DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Achievements user isolation" ON public.achievements FOR ALL USING (user_id = auth.uid());`

#### `portfolio_case_studies`
- **Purpose:** Curated career proof case studies generated by AI or assembled manually from linked achievements for executive portfolio presentation.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `title TEXT NOT NULL`
  - `target_role TEXT NOT NULL` (e.g., 'AI Product Manager', 'Chief Product Officer')
  - `executive_summary TEXT NOT NULL`
  - `full_markdown_case TEXT NOT NULL`
  - `linked_achievement_ids UUID[] NOT NULL DEFAULT '{}'`
  - `is_public BOOL NOT NULL DEFAULT FALSE` (Toggles sharable read-only presentation link)
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_case_studies_user_role ON public.portfolio_case_studies(user_id, target_role) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Case studies user isolation" ON public.portfolio_case_studies FOR ALL USING (user_id = auth.uid());`

---

### 4.8 Content Engine & Reflection

#### `content_items`
- **Purpose:** Master drafting table for AI-generated social media outputs, LinkedIn posts, founder stories, and articles.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `title TEXT NOT NULL`
  - `content_type TEXT NOT NULL DEFAULT 'linkedin_post' CHECK (content_type IN ('linkedin_post', 'founder_story', 'case_study', 'article', 'update'))`
  - `current_body TEXT NOT NULL`
  - `status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived'))`
  - `published_url TEXT NULL`
  - `cited_record_ids UUID[] NOT NULL DEFAULT '{}'` (RAG grounding evidence links)
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_content_user_type_status ON public.content_items(user_id, content_type, status) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Content items user isolation" ON public.content_items FOR ALL USING (user_id = auth.uid());`

#### `content_versions`
- **Purpose:** Immutable audit revision history for content items, allowing instant rollback across iterative editing cycles.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `content_id UUID NOT NULL REFERENCES public.content_items(id) ON DELETE CASCADE`
  - `version_number INT NOT NULL`
  - `body_snapshot TEXT NOT NULL`
  - `change_summary TEXT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Constraints:** `UNIQUE(content_id, version_number)`
- **Indexes:** `CREATE INDEX idx_content_versions_lookup ON public.content_versions(content_id, version_number DESC);`
- **RLS Policy:** `CREATE POLICY "Content versions user isolation" ON public.content_versions FOR ALL USING (user_id = auth.uid());`

#### `weekly_reviews`
- **Purpose:** Structured weekly reflective syntheses generated by AI analyzing completed tasks, relationships nurtured, and KPI milestones.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `week_number INT NOT NULL`
  - `year INT NOT NULL`
  - `title TEXT NOT NULL`
  - `wins_summary TEXT NULL`
  - `bottleneck_analysis TEXT NULL` (e.g., "Execution speed on Justor AI slowed down")
  - `next_week_focus TEXT[] NOT NULL DEFAULT '{}'`
  - `kpi_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Constraints:** `UNIQUE(user_id, year, week_number)`
- **Indexes:** `CREATE INDEX idx_weekly_reviews_timeline ON public.weekly_reviews(user_id, year DESC, week_number DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "Weekly reviews user isolation" ON public.weekly_reviews FOR ALL USING (user_id = auth.uid());`

---

### 4.9 AI Assistant Conversation Memory

#### `ai_conversations`
- **Purpose:** Parent conversation container for live interactive streaming sessions with the AI Founder Coach.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `title TEXT NOT NULL DEFAULT 'New Strategy Session'`
  - `context_venture_id UUID NULL REFERENCES public.ventures(id) ON DELETE SET NULL`
  - `model_used TEXT NOT NULL DEFAULT 'gemini-1.5-pro'`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `deleted_at TIMESTAMPTZ NULL`
- **Indexes:** `CREATE INDEX idx_ai_conversations_user ON public.ai_conversations(user_id, updated_at DESC) WHERE deleted_at IS NULL;`
- **RLS Policy:** `CREATE POLICY "AI conversations user isolation" ON public.ai_conversations FOR ALL USING (user_id = auth.uid());`

#### `ai_messages`
- **Purpose:** Chronological chat transcript logs capturing prompts, streamed responses, and RAG grounding citation packets.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `conversation_id UUID NOT NULL REFERENCES public.ai_conversations(id) ON DELETE CASCADE`
  - `role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool'))`
  - `content TEXT NOT NULL`
  - `citations JSONB NOT NULL DEFAULT '[]'::jsonb` (Array of cited entity UUIDs and titles)
  - `tool_calls JSONB NULL` (Executed MCP tool parameters if applicable)
  - `token_usage_metadata JSONB NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** `CREATE INDEX idx_ai_messages_convo ON public.ai_messages(conversation_id, created_at ASC);`
- **RLS Policy:** `CREATE POLICY "AI messages user isolation" ON public.ai_messages FOR ALL USING (user_id = auth.uid());`

---

### 4.10 System Infrastructure & Observability

#### `integrations`
- **Purpose:** Highly secured repository storing encrypted OAuth credentials and connection configurations for Google Calendar, Google Drive, and MCP clients.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `provider TEXT NOT NULL CHECK (provider IN ('google_calendar', 'google_drive', 'mcp_client'))`
  - `account_email TEXT NULL`
  - `encrypted_access_token BYTEA NULL` (AES-256-GCM field-level encryption)
  - `encrypted_refresh_token BYTEA NULL` (AES-256-GCM field-level encryption)
  - `token_expires_at TIMESTAMPTZ NULL`
  - `status TEXT NOT NULL DEFAULT 'connected' CHECK (status IN ('connected', 'expired', 'revoked', 'error'))`
  - `scopes_granted TEXT[] NOT NULL DEFAULT '{}'`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Constraints:** `UNIQUE(user_id, provider, account_email)`
- **Indexes:** `CREATE INDEX idx_integrations_provider ON public.integrations(user_id, provider, status);`
- **RLS Policy:** `CREATE POLICY "Integrations user isolation" ON public.integrations FOR ALL USING (user_id = auth.uid());`

#### `sync_jobs`
- **Purpose:** Job queue tracker for background tasks: Google Calendar event syncing, Google Drive backup uploads, and document vector ingestion.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `job_type TEXT NOT NULL CHECK (job_type IN ('gdrive_backup', 'gcal_sync', 'doc_ingest', 'vector_reindex'))`
  - `target_entity_id UUID NULL`
  - `status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retried'))`
  - `retry_count INT NOT NULL DEFAULT 0`
  - `max_retries INT NOT NULL DEFAULT 3`
  - `error_details TEXT NULL`
  - `started_at TIMESTAMPTZ NULL`
  - `finished_at TIMESTAMPTZ NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** `CREATE INDEX idx_sync_jobs_queue ON public.sync_jobs(status, job_type, created_at) WHERE status IN ('pending', 'retried');`
- **RLS Policy:** `CREATE POLICY "Sync jobs user isolation" ON public.sync_jobs FOR ALL USING (user_id = auth.uid());`

#### `export_jobs`
- **Purpose:** Manages background execution state for generating comprehensive local Markdown folder archives and ZIP file downloads.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `export_scope TEXT NOT NULL DEFAULT 'full' CHECK (export_scope IN ('full', 'module', 'single_record'))`
  - `target_module TEXT NULL` (e.g., 'People', 'Ventures', 'Meetings')
  - `status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed'))`
  - `download_url TEXT NULL` (Temporary signed URL to generated ZIP backup)
  - `file_size_bytes BIGINT NULL`
  - `error_details TEXT NULL`
  - `started_at TIMESTAMPTZ NULL`
  - `completed_at TIMESTAMPTZ NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** `CREATE INDEX idx_export_jobs_user ON public.export_jobs(user_id, created_at DESC);`
- **RLS Policy:** `CREATE POLICY "Export jobs user isolation" ON public.export_jobs FOR ALL USING (user_id = auth.uid());`

#### `audit_logs`
- **Purpose:** Permanent, append-only security and observability trail tracking authentications, tool modifications, AI billing tokens, and integration accesses.
- **Columns & Schema:**
  - `id UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
  - `user_id UUID NULL REFERENCES auth.users(id) ON DELETE SET NULL` (Nullable to capture unauthenticated failed login attempts)
  - `event_type TEXT NOT NULL` (e.g., 'auth.login_success', 'auth.login_failed', 'mcp.tool_execute', 'export.generated', 'ai.token_usage', 'security.revocation')
  - `source_interface TEXT NOT NULL DEFAULT 'web' CHECK (source_interface IN ('web', 'api', 'mcp_server', 'background_worker', 'cli'))`
  - `target_entity_type TEXT NULL`
  - `target_entity_id UUID NULL`
  - `action_details JSONB NOT NULL DEFAULT '{}'::jsonb` (Stores token consumption counts, duration ms; NEVER records plaintext secrets or full prompts)
  - `ip_address TEXT NULL`
  - `user_agent TEXT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes:** 
  - `CREATE INDEX idx_audit_logs_user_event ON public.audit_logs(user_id, event_type, created_at DESC);`
  - `CREATE INDEX idx_audit_logs_timestamp ON public.audit_logs(created_at DESC);`
- **RLS Policy:** `CREATE POLICY "Audit logs user isolation" ON public.audit_logs FOR SELECT USING (user_id = auth.uid());` (Users can view their logs; NO UPDATE OR DELETE POLICIES PERMITTED).

---

## 5. Authoritative SQL RAG Similarity Function

To support Phase 3 AI RAG hybrid retrieval without cross-user data leaks, migrations must deploy the following audited PL/pgSQL function:

```sql
CREATE OR REPLACE FUNCTION match_memories(
    query_embedding vector(768),
    match_threshold float,
    match_count int,
    p_user_id uuid,
    p_entity_types text[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    entity_type text,
    entity_id uuid,
    content text,
    similarity float,
    metadata jsonb
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        me.id,
        me.entity_type,
        me.entity_id,
        me.content,
        1 - (me.embedding <=> query_embedding) AS similarity,
        me.metadata
    FROM public.memory_embeddings me
    WHERE me.user_id = p_user_id -- EXPLICIT RLS PRE-FILTERING INVARIANT
      AND (p_entity_types IS NULL OR me.entity_type = ANY(p_entity_types))
      AND 1 - (me.embedding <=> query_embedding) > match_threshold
    ORDER BY me.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

## 4. Final Database Implementation & Migrations (Agent 2 Implementation Notes)

The complete production schema spanning all 9 PRD modules and 56 domain tables has been fully implemented via ordered SQL migration files under `supabase/migrations/`.

Key structural enhancements implemented by Agent 2:
- **Enum Specification**: Stable domain state machines implemented in `0002_create_enums.sql` (`venture_status`, `task_priority`, `interaction_type`, etc.).
- **Soft-Delete Architecture**: Standardized `archived_at TIMESTAMPTZ` and stored computed boolean `is_archived` across mutable entities to protect founder history.
- **Vector Search Expansion**: Supporting both v1.0 `memory_embeddings` (IVFFlat index) and multi-modal `embeddings` / `embedding_jobs` (HNSW index) for high-speed incremental RAG retrieval.
- **Junction Relations**: Replaced arbitrary ID arrays with strictly indexed relational junction tables (`memory_people`, `person_venture_links`, `decision_documents`).

For technical specifics, refer to:
- [Migration Guide](file:///e:/second%20brain/docs/database/migration_guide.md)
- [Schema Implementation Notes](file:///e:/second%20brain/docs/database/schema_implementation_notes.md)
- [RLS Policy Reference](file:///e:/second%20brain/docs/database/rls_policy_reference.md)
- Generated TypeScript definitions: `packages/database/generated/types.ts`
- Generated Pydantic ORM models: `packages/database/generated/pydantic_models.py`

