"""
Application schema contract derived from supabase/migrations (canonical authority).

SQLAlchemy models map to this contract; Base.metadata is never a deployment source.
Used by startup verification and schema-drift tests.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Mapping, Sequence, Set

# Tables the running application must find after migrations are applied.
# Includes RAG tables required before G4 and core daily-driver domains.
APPLICATION_REQUIRED_TABLES: FrozenSet[str] = frozenset(
    {
        "profiles",
        "ventures",
        "projects",
        "tasks",
        "organizations",
        "people",
        "person_organization_roles",
        "commitments",
        "relationships",
        "interactions",
        "meetings",
        "meeting_participants",
        "interaction_participants",
        "memories",
        "memory_embeddings",
        "ideas",
        "decisions",
        "documents",
        "document_chunks",
        "embeddings",
        "embedding_jobs",
        "kpis",
        "kpi_definitions",
        "kpi_entries",
        "achievements",
        "portfolio_case_studies",
        "content_items",
        "content_versions",
        "weekly_reviews",
        "integrations",
        "integration_tokens",
        "sync_jobs",
        "export_jobs",
        "export_items",
        "audit_logs",
        "jobs",
        "exports",
        "work_sessions",
        "evidence_items",
        "portfolio_evidence",
        "entity_edges",
    }
)

# Critical columns (name → expected PostgreSQL udt/type family hints).
# Type hints are matched loosely against information_schema / pg_catalog.
APPLICATION_REQUIRED_COLUMNS: Mapping[str, Mapping[str, str]] = {
    "documents": {
        "id": "uuid",
        "user_id": "uuid",
        "title": "text",
        "original_filename": "text",
        "sanitized_filename": "text",
        "mime_type": "text",
        "file_size": "bigint|int8|integer|int4",
        "storage_bucket": "text",
        "storage_path": "text",
        "checksum": "text",
        "processing_status": "USER-DEFINED|text",
        "processing_error": "text",
        "extracted_text_status": "text",
        "embedding_status": "text",
        "extension": "text",
        "extracted_text": "text",
        "chunking_state": "text",
        "error_state": "text",
        "archived_at": "timestamp|timestamptz",
        "deleted_at": "timestamp|timestamptz",
        "created_at": "timestamp|timestamptz",
        "updated_at": "timestamp|timestamptz",
    },
    "document_chunks": {
        "id": "uuid",
        "user_id": "uuid",
        "document_id": "uuid",
        "chunk_index": "integer|int4",
        "chunk_text": "text",
        "embedding_status": "text",
        "created_at": "timestamp|timestamptz",
    },
    "embeddings": {
        "id": "uuid",
        "user_id": "uuid",
        "source_record_type": "text",
        "source_record_id": "uuid",
        "document_chunk_id": "uuid",
        "embedding": "USER-DEFINED|vector",
        "provider": "text",
        "model": "text",
        "dimensions": "integer|int4",
        "created_at": "timestamp|timestamptz",
        "updated_at": "timestamp|timestamptz",
    },
    "embedding_jobs": {
        "id": "uuid",
        "user_id": "uuid",
        "source_record_type": "text",
        "source_record_id": "uuid",
        "document_chunk_id": "uuid",
        "status": "text",
        "retry_count": "integer|int4",
        "created_at": "timestamp|timestamptz",
        "updated_at": "timestamp|timestamptz",
    },
    "memory_embeddings": {
        "id": "uuid",
        "user_id": "uuid",
        "entity_type": "text",
        "entity_id": "uuid",
        "content": "text",
        "embedding": "USER-DEFINED|vector",
        "created_at": "timestamp|timestamptz",
    },
    "ventures": {
        "id": "uuid",
        "user_id": "uuid",
        "name": "text|character varying|varchar",
        "created_at": "timestamp|timestamptz",
    },
    "projects": {
        "id": "uuid",
        "user_id": "uuid",
        "name": "text|character varying|varchar",
        "member_links": "jsonb|json",
        "created_at": "timestamp|timestamptz",
    },
    "tasks": {
        "id": "uuid",
        "user_id": "uuid",
        "title": "text|character varying|varchar",
        "tags": "ARRAY|text[]",
        "created_at": "timestamp|timestamptz",
    },
    "people": {
        "id": "uuid",
        "user_id": "uuid",
        "name": "text|character varying|varchar",
        "created_at": "timestamp|timestamptz",
    },
    "person_organization_roles": {
        "id": "uuid",
        "user_id": "uuid",
        "person_id": "uuid",
        "organization_id": "uuid",
        "role": "text",
        "relationship_type": "text",
        "is_primary": "boolean|bool",
        "started_at": "timestamp|timestamptz",
        "ended_at": "timestamp|timestamptz",
        "source": "text",
        "confidence": "numeric|double precision|float",
        "deleted_at": "timestamp|timestamptz",
        "created_at": "timestamp|timestamptz",
        "updated_at": "timestamp|timestamptz",
    },
    "commitments": {
        "id": "uuid",
        "user_id": "uuid",
        "from_person_id": "uuid",
        "to_person_id": "uuid",
        "organization_id": "uuid",
        "venture_id": "uuid",
        "project_id": "uuid",
        "interaction_id": "uuid",
        "meeting_id": "uuid",
        "direction": "text",
        "description": "text",
        "status": "text",
        "due_at": "timestamp|timestamptz",
        "completed_at": "timestamp|timestamptz",
        "source": "text",
        "deleted_at": "timestamp|timestamptz",
        "created_at": "timestamp|timestamptz",
        "updated_at": "timestamp|timestamptz",
    },
    "jobs": {
        "id": "uuid",
        "user_id": "uuid",
        "job_type": "text",
        "status": "text",
        "retry_count": "integer|int4",
        "result_payload": "jsonb|json",
        "created_at": "timestamp|timestamptz",
    },
    "exports": {
        "id": "uuid",
        "user_id": "uuid",
        "export_type": "text",
        "status": "text",
        "created_at": "timestamp|timestamptz",
    },
    "content_items": {
        "source_records": "jsonb|json",
    },
    "decisions": {
        "supporting_people": "jsonb|json",
        "supporting_documents": "jsonb|json",
    },
    "memories": {
        "related_people": "ARRAY|uuid[]",
        "related_projects": "ARRAY|uuid[]",
        "related_ventures": "ARRAY|uuid[]",
        "tags": "ARRAY|text[]",
        "linked_venture_id": "uuid",
        "linked_person_id": "uuid",
    },
    "portfolio_case_studies": {
        "achievement_id": "uuid",
    },
}

# Foreign keys the application relies on for RAG and relationship-graph integrity.
APPLICATION_REQUIRED_FOREIGN_KEYS: Sequence[Mapping[str, str]] = (
    {
        "table": "person_organization_roles",
        "column": "person_id",
        "ref_table": "people",
        "ref_column": "id",
    },
    {
        "table": "person_organization_roles",
        "column": "organization_id",
        "ref_table": "organizations",
        "ref_column": "id",
    },
    {
        "table": "commitments",
        "column": "interaction_id",
        "ref_table": "interactions",
        "ref_column": "id",
    },
    {
        "table": "document_chunks",
        "column": "document_id",
        "ref_table": "documents",
        "ref_column": "id",
    },
    {
        "table": "embeddings",
        "column": "document_chunk_id",
        "ref_table": "document_chunks",
        "ref_column": "id",
    },
    {
        "table": "embedding_jobs",
        "column": "document_chunk_id",
        "ref_table": "document_chunks",
        "ref_column": "id",
    },
)

# ORM table names that intentionally do NOT exist in migrations (legacy / test-only).
# Empty: migrations 0018/0019 closed the last gaps (documents columns, jobs, exports).
ORM_OBSOLETE_TABLES: FrozenSet[str] = frozenset()

# pgvector dimensions required for Gemini text-embedding-004.
EMBEDDING_VECTOR_DIMENSIONS: int = 768

# Ordered migration filenames under supabase/migrations (bootstrap contract).
MIGRATION_FILES: List[str] = [
    "20260811000001_enable_extensions.sql",
    "20260811000002_create_enums.sql",
    "20260811000003_create_profiles_and_triggers.sql",
    "20260811000004_create_founder_execution_tables.sql",
    "20260811000005_create_crm_tables.sql",
    "20260811000006_create_memory_tables.sql",
    "20260811000007_create_idea_and_decision_tables.sql",
    "20260811000008_create_documents_and_vectors.sql",
    "20260811000009_create_kpis_and_portfolio_tables.sql",
    "20260811000010_create_ai_and_content_tables.sql",
    "20260811000011_create_integrations_and_jobs_tables.sql",
    "20260811000012_create_audit_logs.sql",
    "20260811000013_create_validation_functions.sql",
    "20260811000014_create_indexes.sql",
    "20260811000015_enable_rls_and_policies.sql",
    "20260811000016_create_search_functions.sql",
    "20260811000017_create_evidence_and_portfolio_graph_tables.sql",
    "20260827000018_align_documents_with_application_contract.sql",
    "20260827000019_create_jobs_and_exports_tables.sql",
    "20260828000020_harden_rls_authorization_boundary.sql",
    "20260828000021_mcp_work_session_finalization.sql",
    "20260828000021b_mcp_work_session_finalization_objects.sql",
    "20260828000022_network_relationship_intelligence.sql",
    "20260828000023_align_canonical_columns_with_application_contract.sql",
]

# Tables that intentionally hold no user-facing RLS policies (verified by the G2 suite).
RLS_POLICY_EXEMPT_TABLES: FrozenSet[str] = frozenset({"integration_tokens"})


def type_matches(actual: str, expected_pattern: str) -> bool:
    """Return True if actual DB type matches one of the pipe-separated expected families."""
    actual_norm = (actual or "").lower().replace(" ", "")
    for part in expected_pattern.lower().split("|"):
        part_norm = part.replace(" ", "")
        if part_norm == "array" and actual_norm.endswith("[]"):
            return True
        if part_norm == "user-defined" and actual_norm not in {
            "uuid",
            "text",
            "varchar",
            "charactervarying",
            "bigint",
            "int8",
            "integer",
            "int4",
            "boolean",
            "bool",
            "date",
            "timestamp",
            "timestamptz",
            "jsonb",
            "json",
            "numeric",
            "doubleprecision",
            "float",
            "float8",
        } and not actual_norm.endswith("[]"):
            return True
        if part_norm and part_norm in actual_norm:
            return True
    return False


def missing_tables(present: Set[str], required: Set[str] | None = None) -> List[str]:
    req = required if required is not None else set(APPLICATION_REQUIRED_TABLES)
    return sorted(req - present)


def orm_mapped_tablenames(metadata_tables: Dict[str, object]) -> Set[str]:
    return set(metadata_tables.keys())
