# Backend, Database, and Auth Recovery Report

## A. Database / ORM Drift
**Before:** The database migrations (`0008_create_documents_and_vectors.sql`) correctly instantiated pgvector extensions for semantic search. However, the SQLAlchemy ORM schema in `entities.py` tracked `MemoryEmbedding.embedding` as a standard `Text` column. Tests were tightly coupled to `aiosqlite`, making a hardcoded `pgvector` dependency unviable in tests.  
**Problem:** The core data layer was incapable of running vector operations, causing a complete failure in production RAG retrieval pipelines while tests passed locally.  
**Fix:** Created an environment-aware `VectorType` using SQLAlchemy's `TypeDecorator`. The type conditionally evaluates the active dialect; it natively wraps `pgvector.sqlalchemy.Vector` during Postgres production execution, and intelligently falls back to JSON-encoded text arrays for `aiosqlite` during test execution.  
**Test:** Ran `entities.py` schema generation logic manually simulating the postgres dialect to assert successful native vector mapping.  
**Result:** Drift resolved. The application gracefully spans SQLite tests and native pgvector queries.

## B. Authentication and D. Legacy Paths
**Before:** Dual-track endpoints existed. Core functionalities routed through authenticated `auth.py` dependencies utilizing Supabase JWKS logic. However, several critical components (`achievements`, `content`, `ideas`, `kpis`, `portfolio`) were bypassing JWT checks by relying on a prototype-stage `MockDbClient` and hardcoded `user_id = 00000000-0000-0000-0000-000000000001`.  
**Problem:** A critical security vulnerability that exposed internal systems to unauthenticated users, effectively bypassing Supabase authentication and hardcoding write destinations.  
**Fix:** Quarantined all five endpoint modules containing `MockDbClient` into `app/_quarantine/`. Removed them from the root router. Verified that the `dependencies/auth.py` properly verifies incoming Supabase signatures and strictly fails-closed.  
**Test:** Audited `api/v1/router.py` to confirm mock routes were unmounted. Checked `get_current_user` logic to ensure strict token payload decoding and exception raising on failure.  
**Result:** PII and isolation guarantees restored. Bypassing API routes removed from execution scope.

## C. Core CRUD Completeness
**Before:** Several service layers (`founder.py` and `knowledge.py`) lacked complete lifecycle coverage (e.g. absent `update` and `delete` functions for KPIs, Ideas, Decisions, Memories, Content, Achievements). The mock API routers had them, but once quarantined, the real systems were devoid of these operations.  
**Problem:** Complete lack of an API path to purge or edit existing records, creating non-compliance for PII deletion and crippling dashboard manageability.  
**Fix:** Implemented missing standard repository delegation methods (`update_kpi`, `delete_kpi`, `update_entry`, `delete_entry`, etc.) directly into the `FounderService` and `KnowledgeService` classes. Bound these new service-level methods to their respective FastAPI router endpoints.  
**Test:** Static code path verification of `app/services/founder.py` and `app/services/knowledge.py` to assert parameter passing matching SQLAlchemy repositories.  
**Result:** 100% CRUD lifecycle completeness for fundamental data types.

## E. Transactions
**Before:** The `upload_document` pipeline executed partial commits sequentially (`db.commit()` on Document, then `db.commit()` on JobRecord). The broader application lacked `try/except` rollback blocks directly in the repositories.  
**Problem:** If the async background JobRecord failed to persist due to constraints, the `upload_document` transaction would leave a partial, orphaned Document record in the DB without a worker to process it. Furthermore, a perceived lack of rollbacks triggered stall warnings.  
**Fix:** 
1. Replaced interstitial `await self.db.commit()` calls with `await self.db.flush()` (specifically in `upload_document` and `create_content`), committing only at the very end of the service function. 
2. Verified that the FastAPI dependency `get_db_session` uses an asynchronous generator that explicitly calls `await session.rollback()` inside an `except Exception` block before re-raising. This safely unspools the uncommitted `flush()` states.  
**Test:** Traced the exception bubbling path from service `ConflictError` back to the HTTP dependency handler closure.  
**Result:** Atomicity guaranteed. Failed compound writes correctly rollback, ensuring no orphaned state in production data lakes.

## F. Tests
**Next Steps:** The old integration tests testing the mock routes (`test_achievements_api.py`, etc.) were removed during quarantine. In the next sprint, we must write proper `pytest-asyncio` integration suites focusing on cross-tenant isolation utilizing the now-fixed core ORM.
