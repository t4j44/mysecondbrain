"""
G5 MCP write-exposure and finalize_work_session tests (unit category).

What these prove:
  * Every implemented write tool is registered on both the official MCP server and the
    REST invoke manifest, each behind a granular write scope.
  * A read-only credential is refused with 403 before any database work happens.
  * finalize_work_session extracts before it writes, writes once, and replays without
    creating duplicates.
  * Provenance is attached to the session and to every record it creates.

What they do NOT prove (see docs/production-recovery/G5_MCP_FINALIZE_GATE.md):
  * The database-level idempotency constraint — SQLite has no partial unique index on a
    JSON expression; that lives in supabase/migrations/20260828000021 and is verified by
    tests/integration/test_mcp_finalize_postgres.py.
  * Extraction accuracy — no live Gemini key is available, so extraction runs in
    deterministic mode and quality is UNVALIDATED.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.mcp import server as mcp_server_module
from app.mcp.extraction import MODE_DETERMINISTIC, extract_session_intelligence
from app.mcp.router import MCP_ALL_TOOLS, MCP_TOOLS_MANIFEST, MCP_WRITE_TOOLS_MANIFEST
from app.mcp.security import (
    FINALIZE_REQUIRED_SCOPES,
    WRITE_SCOPES,
    MCPScopeError,
    verify_scope,
)
from app.mcp.tools import MCPDomainTools
from app.models.entities import Decision, Interaction, Memory, Profile, Project, Task

EXPECTED_WRITE_TOOLS = {
    "create_task",
    "update_task",
    "complete_task",
    "create_person",
    "update_person",
    "create_project",
    "update_project",
    "save_memory",
    "save_decision",
    "save_work_session",
    "finalize_work_session",
}

READ_ONLY_SCOPES = [
    "mcp:people:read",
    "mcp:memory:read",
    "mcp:projects:read",
    "mcp:tasks:read",
    "mcp:content:draft",
]

SESSION_TRANSCRIPT = """
# Objective
Ship the MCP write surface behind granular scopes.

# Decisions
- Extract with the model before opening the transaction.
- Enforce idempotency with a partial unique index rather than application checks alone.

# Tasks
- Write the postgres-gated finalize idempotency suite
- Update the status docs that still claim writes are hidden

# Findings
- Holding a transaction open across inference pins a pooled connection.

# People
- Taj Uddin

# Artifacts
- supabase/migrations/20260828000021_mcp_work_session_finalization.sql

# Open Questions
- Should evidence become rows in evidence_items?
"""


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_every_implemented_write_tool_is_registered():
    manifest_names = {t["name"] for t in MCP_WRITE_TOOLS_MANIFEST}
    assert manifest_names == EXPECTED_WRITE_TOOLS

    for name in EXPECTED_WRITE_TOOLS:
        assert hasattr(MCPDomainTools, name), name
        assert callable(getattr(mcp_server_module, name, None)), name


def test_manifest_and_server_agree_and_have_no_duplicates():
    names = [t["name"] for t in MCP_ALL_TOOLS]
    assert len(names) == len(set(names))
    assert set(names) == {t["name"] for t in MCP_TOOLS_MANIFEST} | EXPECTED_WRITE_TOOLS


def test_write_tools_declare_a_granular_write_scope_and_schema():
    for spec in MCP_WRITE_TOOLS_MANIFEST:
        assert spec["write"] is True, spec["name"]
        assert spec["required_scope"] in WRITE_SCOPES, spec["name"]
        assert spec["input_schema"]["type"] == "object", spec["name"]
        assert spec["input_schema"]["properties"], spec["name"]


def test_finalize_requires_every_domain_write_scope():
    spec = next(t for t in MCP_WRITE_TOOLS_MANIFEST if t["name"] == "finalize_work_session")
    assert set(spec["additional_scopes"]) == set(FINALIZE_REQUIRED_SCOPES)


def test_no_arbitrary_sql_tool_is_exposed():
    for spec in MCP_ALL_TOOLS:
        blob = f"{spec['name']} {spec['description']}".lower()
        assert "sql" not in blob and "query_database" not in blob, spec["name"]


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_read_only_scopes_never_satisfy_a_write_scope():
    for spec in MCP_WRITE_TOOLS_MANIFEST:
        with pytest.raises(MCPScopeError):
            verify_scope(READ_ONLY_SCOPES, str(spec["required_scope"]))
    with pytest.raises(MCPScopeError):
        verify_scope(["mcp:read"], "mcp:tasks:write")


def test_write_group_grant_covers_the_finalize_scope_set():
    for scope in FINALIZE_REQUIRED_SCOPES:
        assert verify_scope(["mcp:write"], scope) is True


def test_writes_go_through_the_committing_rls_context():
    """No write tool may open its own session or skip the commit boundary."""
    source = mcp_server_module.__loader__.get_source(mcp_server_module.__name__)  # type: ignore[union-attr]
    write_block = source.split("# WRITE TOOLS (G5)", 1)[1]
    assert "_domain(" not in write_block.replace("_write_domain(", "")
    assert "AsyncSessionLocal" not in source
    assert "admin_db_session(reason=\"mcp_token_verification\")" in source


@pytest_asyncio.fixture
async def mcp_credentials(async_client: AsyncClient, auth_headers: dict, test_user_id: str):
    """Create one read-only and one full-write MCP credential for the same owner."""
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        if not await session.get(Profile, test_user_id):
            session.add(Profile(id=test_user_id, email="taj@founder.local", settings={}))
            await session.commit()

    async def _create(name: str, scopes: list) -> str:
        response = await async_client.post(
            "/api/v1/mcp/credentials",
            headers=auth_headers,
            json={"client_name": name, "client_type": "stdio", "scopes": scopes},
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]["plaintext_key"]

    return {
        "read_only": await _create("Read Only Client", READ_ONLY_SCOPES),
        "writer": await _create("Writer Client", READ_ONLY_SCOPES + list(WRITE_SCOPES)),
        "user_id": test_user_id,
    }


@pytest.mark.asyncio
async def test_read_only_credential_is_forbidden_from_every_write_tool(
    async_client: AsyncClient, mcp_credentials
):
    for spec in MCP_WRITE_TOOLS_MANIFEST:
        response = await async_client.post(
            "/mcp/tools/invoke",
            headers={"X-MCP-API-KEY": mcp_credentials["read_only"]},
            json={"tool": spec["name"], "arguments": {}},
        )
        assert response.status_code == 403, (spec["name"], response.text)
        assert "scope" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_read_only_credential_write_attempt_persists_nothing(
    async_client: AsyncClient, mcp_credentials
):
    from tests.conftest import TestingSessionLocal

    response = await async_client.post(
        "/mcp/tools/invoke",
        headers={"X-MCP-API-KEY": mcp_credentials["read_only"]},
        json={"tool": "create_task", "arguments": {"title": "unauthorized task"}},
    )
    assert response.status_code == 403

    async with TestingSessionLocal() as session:
        tasks = (await session.execute(Task.__table__.select())).all()
    assert [t for t in tasks if t.title == "unauthorized task"] == []


@pytest.mark.asyncio
async def test_missing_credential_is_unauthorized(async_client: AsyncClient):
    response = await async_client.post(
        "/mcp/tools/invoke", json={"tool": "create_task", "arguments": {"title": "x"}}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Write execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_credential_creates_and_commits_a_task(
    async_client: AsyncClient, mcp_credentials
):
    from tests.conftest import TestingSessionLocal

    response = await async_client.post(
        "/mcp/tools/invoke",
        headers={"X-MCP-API-KEY": mcp_credentials["writer"]},
        json={
            "tool": "create_task",
            "arguments": {"title": "Register MCP write tools", "priority": "high"},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["security_context"]["write"] is True
    task_id = body["result"]["id"]

    async with TestingSessionLocal() as session:
        persisted = await session.get(Task, task_id)
        assert persisted is not None
        assert persisted.user_id == mcp_credentials["user_id"]
        assert persisted.priority == "high"


@pytest.mark.asyncio
async def test_unknown_arguments_are_dropped_not_forwarded(
    async_client: AsyncClient, mcp_credentials
):
    response = await async_client.post(
        "/mcp/tools/invoke",
        headers={"X-MCP-API-KEY": mcp_credentials["writer"]},
        json={
            "tool": "create_task",
            "arguments": {"title": "Scoped task", "user_id": "99999999-9999-4000-a999-999999999999"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["result"]["user_id"] == mcp_credentials["user_id"]


@pytest.mark.asyncio
async def test_missing_required_argument_is_rejected(async_client: AsyncClient, mcp_credentials):
    response = await async_client.post(
        "/mcp/tools/invoke",
        headers={"X-MCP-API-KEY": mcp_credentials["writer"]},
        json={"tool": "update_task", "arguments": {"title": "no id"}},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Extraction (pre-transaction)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extraction_runs_without_a_database_and_reports_its_mode():
    extracted = await extract_session_intelligence(
        summary=SESSION_TRANSCRIPT, session_payload=None, provider="claude_desktop"
    )
    telemetry = extracted["extraction"]
    # No live key is configured in the test environment, so this must be honest about it.
    assert telemetry["mode"] == MODE_DETERMINISTIC
    assert telemetry["quality_validated"] is False
    assert telemetry["error"]

    fields = extracted["fields"]
    assert any("transaction" in d for d in fields["decisions"])
    assert any("postgres-gated" in t for t in fields["tasks"])
    assert "Taj Uddin" in fields["people_mentioned"]
    assert fields["unresolved_questions"]


@pytest.mark.asyncio
async def test_extraction_never_fabricates_from_an_empty_session():
    extracted = await extract_session_intelligence(summary="", session_payload={})
    assert extracted["extraction"]["transcript_chars"] == 0
    assert all(not value for value in extracted["fields"].values())


# ---------------------------------------------------------------------------
# finalize_work_session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def finalize_env(prepare_database, test_user_id: str):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        session.add(Profile(id=test_user_id, email="taj@founder.local", settings={}))
        project = Project(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            name="Second Brain Recovery",
            status="in_progress",
        )
        session.add(project)
        await session.commit()
        return {"user_id": test_user_id, "project_id": project.id}


async def _finalize(user_id: str, **kwargs):
    """Run the tool exactly the way the MCP layer does: extract first, then write."""
    from tests.conftest import TestingSessionLocal

    extracted = await extract_session_intelligence(
        summary=kwargs.get("summary"),
        session_payload=kwargs.get("session_payload"),
        provider=kwargs.get("provider"),
    )
    async with TestingSessionLocal() as session:
        domain = MCPDomainTools(db=session, user_id=user_id)
        result = await domain.finalize_work_session(
            extraction=extracted["extraction"], **extracted["fields"], **kwargs
        )
        await session.commit()
    return result


@pytest.mark.asyncio
async def test_finalize_creates_the_full_record_set_with_provenance(finalize_env):
    from tests.conftest import TestingSessionLocal

    result = await _finalize(
        finalize_env["user_id"],
        provider="claude_desktop",
        session_reference="session-abc-001",
        client_request_id="req-abc-001",
        summary=SESSION_TRANSCRIPT,
        project_hint="Second Brain Recovery",
        title="G5 MCP write exposure",
    )

    assert result["status"] == "finalized"
    assert result["idempotent_replayed"] is False
    assert result["resolved_context"]["project_id"] == finalize_env["project_id"]

    created = result["created_records"]
    assert created["decisions"] and created["tasks"] and created["people"]
    assert created["memories"]

    provenance = result["provenance"]
    assert provenance["session_uri"] == result["session_grounding"]
    assert provenance["provider"] == "claude_desktop"
    assert provenance["client_request_id"] == "req-abc-001"
    assert provenance["extraction"]["mode"] == MODE_DETERMINISTIC

    async with TestingSessionLocal() as session:
        decisions = (await session.execute(Decision.__table__.select())).all()
        assert all(result["session_grounding"] in d.supporting_documents for d in decisions)

        tasks = (await session.execute(Task.__table__.select())).all()
        origins = [t.calendar_sync_metadata.get("origin_session_id") for t in tasks]
        assert set(origins) == {result["session_id"]}

        memories = (await session.execute(Memory.__table__.select())).all()
        assert all(m.meta["origin_session_id"] == result["session_id"] for m in memories)


@pytest.mark.asyncio
async def test_finalize_is_idempotent_on_replay(finalize_env):
    from tests.conftest import TestingSessionLocal

    args = dict(
        provider="claude_desktop",
        session_reference="session-abc-002",
        client_request_id="req-abc-002",
        summary=SESSION_TRANSCRIPT,
        project_hint="Second Brain Recovery",
    )
    first = await _finalize(finalize_env["user_id"], **args)
    second = await _finalize(finalize_env["user_id"], **args)

    assert second["idempotent_replayed"] is True
    assert second["session_id"] == first["session_id"]

    async with TestingSessionLocal() as session:
        sessions = (await session.execute(Interaction.__table__.select())).all()
        assert len([s for s in sessions if s.interaction_type == "work_session"]) == 1
        assert len((await session.execute(Task.__table__.select())).all()) == len(
            first["created_records"]["tasks"]
        )
        assert len((await session.execute(Decision.__table__.select())).all()) == len(
            first["created_records"]["decisions"]
        )


@pytest.mark.asyncio
async def test_finalize_replay_by_session_reference_alone_is_idempotent(finalize_env):
    args = dict(
        provider="claude_desktop",
        session_reference="session-abc-003",
        summary=SESSION_TRANSCRIPT,
    )
    first = await _finalize(finalize_env["user_id"], **args)
    second = await _finalize(finalize_env["user_id"], **args)
    assert second["idempotent_replayed"] is True
    assert second["session_id"] == first["session_id"]


@pytest.mark.asyncio
async def test_finalize_does_not_invent_missing_projects_or_ventures(finalize_env):
    result = await _finalize(
        finalize_env["user_id"],
        session_reference="session-abc-004",
        summary=SESSION_TRANSCRIPT,
        project_hint="A Project That Does Not Exist",
        venture_hint="A Venture That Does Not Exist",
    )
    unresolved = {link["type"] for link in result["resolved_context"]["unresolved_links"]}
    assert unresolved == {"project", "venture"}
    assert result["resolved_context"]["project_id"] is None
    assert result["resolved_context"]["venture_id"] is None


@pytest.mark.asyncio
async def test_finalize_stores_every_intelligence_bucket(finalize_env):
    result = await _finalize(
        finalize_env["user_id"],
        session_reference="session-abc-005",
        summary=SESSION_TRANSCRIPT,
        session_payload={
            "commitments": ["Report G5 verdicts honestly"],
            "organizations_mentioned": ["Justor AI"],
            "evidence": ["apps/api/app/mcp/server.py"],
            "skills_demonstrated": ["transaction design"],
        },
    )
    intel = result["extracted_intelligence"]
    assert intel["commitments"] == ["Report G5 verdicts honestly"]
    assert intel["organizations_mentioned"] == ["Justor AI"]
    assert intel["evidence"] == ["apps/api/app/mcp/server.py"]
    assert intel["skills_demonstrated"] == ["transaction design"]
    assert intel["artifacts"] and intel["unresolved_questions"]


@pytest.mark.asyncio
async def test_finalize_isolates_owners(finalize_env, other_user_id: str):
    """A second owner replaying the same reference gets their own session, never a match."""
    args = dict(session_reference="shared-reference", summary=SESSION_TRANSCRIPT)
    mine = await _finalize(finalize_env["user_id"], **args)
    theirs = await _finalize(other_user_id, **args)
    assert mine["session_id"] != theirs["session_id"]
    assert theirs["idempotent_replayed"] is False


# ---------------------------------------------------------------------------
# Migration contract
# ---------------------------------------------------------------------------


def test_idempotency_is_enforced_in_the_canonical_schema():
    from pathlib import Path

    from app.db.schema_contract import MIGRATION_FILES

    migrations = Path(__file__).resolve().parents[3] / "supabase" / "migrations"
    assert "20260828000021_mcp_work_session_finalization.sql" in MIGRATION_FILES
    assert sorted(p.name for p in migrations.glob("*.sql")) == sorted(MIGRATION_FILES)

    # 0021 adds the enum value alone; a new enum value cannot be USED until the
    # transaction that added it commits, so the objects that reference it live in 0021b.
    enum_source = (migrations / "20260828000021_mcp_work_session_finalization.sql").read_text(
        encoding="utf-8"
    )
    object_source = (
        migrations / "20260828000021b_mcp_work_session_finalization_objects.sql"
    ).read_text(encoding="utf-8")
    assert "ADD VALUE IF NOT EXISTS 'work_session'" in enum_source
    assert (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_interactions_work_session_client_request"
        in object_source
    )
    assert "meta ->> 'client_request_id'" in object_source
    # Enum equality is IMMUTABLE; the text cast is not, and PostgreSQL rejects it
    # in an index predicate.
    assert "WHERE interaction_type = 'work_session'" in object_source
