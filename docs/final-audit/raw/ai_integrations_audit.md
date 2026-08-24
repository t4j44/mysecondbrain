# AI Integrations Audit Findings

## SECTION 9 — AI ENGINE
- **Gemini Provider & Models**: The system defaults to Gemini (`GeminiLLMProvider`) utilizing Google's `text-embedding-004` and `gemini-1.5-pro` (evidence in `apps/api/app/ai/provider.py` and `database_schema.md`).
- **OpenAI Dependency**: There is no hard OpenAI dependency. `OpenAILLMProvider` is implemented purely as a fallback via the `BaseLLMProvider` abstraction (`apps/api/app/ai/provider.py`). 
- **Fake/Simulated Behaviors**: In `apps/api/app/ai/provider.py`, if the API key is unconfigured or a "placeholder" (in non-production), it safely returns synthetic text like `[Simulated Gemini Output for...]` to support local development and tests without actual API calls.

## SECTION 10 — RAG A-Z
- **Trace & Vector Persistence**: 
  - **Upload & Storage**: Files are mapped in the `documents` table utilizing Supabase Storage (`supabase/migrations/20260811000008_create_documents_and_vectors.sql`).
  - **Extraction & Chunking**: Document parsing uses a 500-token sliding window with a 100-token overlap, stored in `document_chunks` (detailed in `docs/architecture/ai_retrieval_flow.md`).
  - **Embedding**: Handled via Gemini (`text-embedding-004`).
  - **Vector Persistence**: Embeddings are stored in the `embeddings` and `memory_embeddings` tables using **pgvector** (`extensions.vector(768)`).
  - **Retrieval & Ranking**: Executed using a hybrid approach combining pgvector cosine similarity and PostgreSQL FTS Trigram keyword search via the `hybrid_knowledge_search` SQL function (`supabase/migrations/20260811000016_create_search_functions.sql`).

## SECTION 12 — WORK SESSION INTELLIGENCE
- **Trace**: AI conversation (`ai_conversations`, `ai_messages`) -> `decisions` -> `tasks` -> `achievements` -> `portfolio_case_studies`.
- **Automatic vs Manual**:
  - The system enforces a **Zero Auto-Publishing Rule** (`docs/features/ai-content-engine.md`). Everything generated is set to a `"draft"` status and requires manual review.
  - Before generation, the system forces an explicit **Evidence Preview & Privacy Review**.
  - Portfolio creation in `apps/api/app/services/portfolio/portfolio_service.py` is automatic via `ai.generate_case_study` if available, otherwise it falls back to a deterministic, offline markdown template generator based on evidence.

## SECTION 13 & 14 — NETWORK & GOOGLE A-Z
- **Google Integration Reality**: The Google Drive and Calendar integrations are **simulated**.
  - `apps/api/app/integrations/google_client.py` mocks the OAuth process by generating tokens like `1//0e_simulated_refresh_token_for_{user_id}_{code[:10]}`.
  - `apps/api/app/jobs/handlers/sync_google.py` hardcodes the sync responses, statically returning `{"synced_files_count": 14}` for Drive and `{"events_synchronized": 5}` for Calendar, rather than performing actual API sync operations.

## SECTION 18 & 19 — EVIDENCE/PORTFOLIO & DECISION INTELLIGENCE
- **Decision Intelligence**: Tracked in the `decisions` table to document executive rationale, alternatives, and expected outcomes (`database_schema.md`).
- **Evidence & Portfolio**: Portfolio case studies (`portfolio_case_studies` table) must strictly trace back to verified `achievements`. The `PortfolioService` (`apps/api/app/services/portfolio/portfolio_service.py`) ensures that generated case studies strictly reflect documented milestones and prohibits the insertion of fabricated or unverified traction metrics.
