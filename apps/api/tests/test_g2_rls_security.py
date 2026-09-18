"""
G2 RLS authorization-boundary tests (unit category).

These prove the *architecture*: identity injection is transaction-local and parameter-bound,
endpoints can only obtain an RLS-scoped session, the admin context is not injectable, and the
migration policies use the intended owner form. They do NOT prove that PostgreSQL denies a
cross-tenant read — that requires the postgres integration suite in
tests/integration/test_rls_cross_tenant.py.
"""

import json
import re
from pathlib import Path

import pytest

from app.db.rls import (
    ANON_ROLE,
    CLAIMS_SETTING,
    RLS_ROLE,
    ROLE_SETTING,
    RLSIdentityError,
    build_jwt_claims,
    identity_statements,
)
from app.db.schema_contract import RLS_POLICY_EXEMPT_TABLES

REPO_ROOT = Path(__file__).resolve().parents[3]
API_APP = REPO_ROOT / "apps" / "api" / "app"
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

USER_A = "00000000-0000-4000-a000-000000000001"
USER_B = "99999999-9999-4000-a999-999999999999"


def _python_sources(*subdirs: str) -> list[Path]:
    roots = [API_APP / sub for sub in subdirs] if subdirs else [API_APP]
    return [
        path
        for root in roots
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts and "_quarantine" not in path.parts
    ]


# ---------------------------------------------------------------------------
# Identity injection
# ---------------------------------------------------------------------------


def test_identity_is_transaction_local_only():
    """Every injected setting must use set_config(..., true); plain SET would leak."""
    statements = [sql for sql, _ in identity_statements(USER_A)]
    assert statements, "no identity statements produced"
    for sql in statements:
        assert sql.startswith("SELECT set_config("), sql
        assert sql.rstrip().endswith(", true)"), f"not transaction-local: {sql}"
        assert not re.search(r"^\s*SET\s", sql, re.IGNORECASE)


def test_identity_values_are_bound_parameters():
    """Caller-controlled values are never interpolated into SQL text."""
    for sql, params in identity_statements(USER_A, email="taj@founder.local"):
        assert params, sql
        assert USER_A not in sql
        for value in params.values():
            assert value not in sql


def test_identity_sets_authenticated_role_and_claims():
    statements = dict(
        (sql, params) for sql, params in identity_statements(USER_A, email="taj@founder.local")
    )
    claims_sql = next(sql for sql in statements if CLAIMS_SETTING in sql)
    role_sql = next(sql for sql in statements if f"'{ROLE_SETTING}'" in sql)

    claims = json.loads(statements[claims_sql]["claims"])
    assert claims["sub"] == USER_A
    assert claims["role"] == RLS_ROLE
    assert claims["email"] == "taj@founder.local"
    assert statements[role_sql]["role"] == RLS_ROLE


def test_role_switch_is_restricted_to_rls_roles():
    """A privileged role can never be requested through the identity helper."""
    for role in ("postgres", "service_role", "authenticated; DROP TABLE tasks"):
        with pytest.raises(RLSIdentityError):
            identity_statements(USER_A, role=role)
    assert identity_statements(USER_A, role=ANON_ROLE)


@pytest.mark.parametrize("bad_subject", ["", "not-a-uuid", "1 OR 1=1", None])
def test_non_uuid_subject_fails_closed(bad_subject):
    with pytest.raises(RLSIdentityError):
        identity_statements(bad_subject)
    with pytest.raises(RLSIdentityError):
        build_jwt_claims(bad_subject)


def test_client_claims_cannot_be_smuggled():
    """Only the verified subject, role and email reach the GUC."""
    claims = build_jwt_claims(USER_A, email="taj@founder.local")
    assert set(claims) == {"sub", "role", "aud", "email"}


# ---------------------------------------------------------------------------
# Centralization and admin separation
# ---------------------------------------------------------------------------


def test_set_local_logic_exists_in_exactly_one_module():
    offenders = sorted(
        str(path.relative_to(API_APP)).replace("\\", "/")
        for path in _python_sources()
        if "set_config(" in path.read_text(encoding="utf-8")
    )
    assert offenders == ["db/rls.py"], offenders


def test_endpoints_only_receive_rls_scoped_sessions():
    """No API/MCP module may inject an identity-free session."""
    offenders = []
    for path in _python_sources("api", "mcp", "dependencies", "services"):
        source = path.read_text(encoding="utf-8")
        if "Depends(get_db_session)" in source or "Depends(admin_db_session)" in source:
            offenders.append(str(path.relative_to(API_APP)).replace("\\", "/"))
    assert offenders == [], offenders


def test_unscoped_session_dependency_no_longer_exists():
    from app.dependencies import database

    assert not hasattr(database, "get_db_session"), (
        "get_db_session is a footgun: an authenticated endpoint could obtain a session with "
        "no RLS claims. Use get_rls_db_session or admin_db_session(reason=...)."
    )
    assert hasattr(database, "get_rls_db_session")
    assert hasattr(database, "admin_db_session")


def test_admin_session_is_not_injectable():
    """admin_db_session must be a context manager, never a FastAPI dependency."""
    from app.dependencies.database import admin_db_session

    assert hasattr(admin_db_session, "__wrapped__")
    with pytest.raises(TypeError):
        admin_db_session()  # type: ignore[call-arg]  # reason is keyword-only and required


def test_privileged_paths_use_the_admin_context_explicitly():
    expected = {
        "jobs/runner.py": "job_claim",
        "mcp/server.py": "mcp_token_verification",
        "mcp/router.py": "mcp_api_key_verification",
        "main.py": "readiness_probe",
    }
    for relative, reason in expected.items():
        source = (API_APP / relative).read_text(encoding="utf-8")
        assert "admin_db_session(reason=" in source, relative
        assert reason in source, (relative, reason)


def test_no_module_bypasses_the_session_factory_for_user_work():
    """Only the canonical dependency module may build sessions from the factory."""
    offenders = sorted(
        str(path.relative_to(API_APP)).replace("\\", "/")
        for path in _python_sources()
        if "AsyncSessionLocal(" in path.read_text(encoding="utf-8")
    )
    assert offenders == ["dependencies/database.py"], offenders


# ---------------------------------------------------------------------------
# Migration policy audit
# ---------------------------------------------------------------------------


def _policy_statements() -> list[str]:
    statements = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        statements.extend(
            re.findall(r"CREATE POLICY.*?;", path.read_text(encoding="utf-8"), re.DOTALL)
        )
    return statements


def test_every_policy_is_owner_scoped():
    for statement in _policy_statements():
        if 'brain_private_anon_guard' in statement:
            assert 'AS RESTRICTIVE' in statement and 'TO anon' in statement
            assert "USING (bucket_id <> 'brain-documents')" in statement
            assert "WITH CHECK (bucket_id <> 'brain-documents')" in statement
        else:
            assert "auth.uid()" in statement, statement


def test_hardening_migration_requires_a_present_identity():
    """The G2 migration must use the explicit auth.uid() IS NOT NULL form."""
    migration = next(MIGRATIONS_DIR.glob("*_harden_rls_authorization_boundary.sql"))
    source = migration.read_text(encoding="utf-8")
    policies = re.findall(r"CREATE POLICY.*?;", source, re.DOTALL)
    assert policies
    for statement in policies:
        assert "auth.uid() IS NOT NULL" in statement, statement


def test_hardening_migration_keeps_rls_enabled_everywhere():
    """RLS must be hardened, never dropped, to make tests easier."""
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
    )
    assert "DISABLE ROW LEVEL SECURITY" not in source.upper()
    assert "NO FORCE ROW LEVEL SECURITY" not in source.upper()


def test_token_vault_has_no_policies_and_no_authenticated_grant():
    migration = next(MIGRATIONS_DIR.glob("*_harden_rls_authorization_boundary.sql"))
    source = migration.read_text(encoding="utf-8")
    assert "integration_tokens" in RLS_POLICY_EXEMPT_TABLES
    assert "REVOKE ALL ON public.integration_tokens FROM authenticated;" in source


def test_audit_log_history_stays_immutable_for_users():
    migration = next(MIGRATIONS_DIR.glob("*_harden_rls_authorization_boundary.sql"))
    source = migration.read_text(encoding="utf-8")
    assert "REVOKE UPDATE, DELETE ON public.audit_logs FROM authenticated;" in source
    audit_policies = [s for s in re.findall(r"CREATE POLICY.*?;", source, re.DOTALL) if "audit_logs" in s]
    assert audit_policies
    for statement in audit_policies:
        assert " FOR SELECT " in statement or " FOR INSERT " in statement, statement


def test_indirect_ownership_is_checked_for_rag_child_tables():
    migration = next(MIGRATIONS_DIR.glob("*_harden_rls_authorization_boundary.sql"))
    source = migration.read_text(encoding="utf-8")
    assert "FROM public.documents d" in source
    assert "FROM public.document_chunks ch" in source


def test_migration_contract_includes_the_hardening_migration():
    from app.db.schema_contract import MIGRATION_FILES

    on_disk = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert on_disk == sorted(MIGRATION_FILES)
    assert any("harden_rls_authorization_boundary" in name for name in MIGRATION_FILES)
