"""
G5.5 network relationship-intelligence tests (unit category).

These prove the *data model and the query surface*: a person can hold roles at several
organizations, affiliations carry history, commitments are first-class and directional, and
every relationship question in the gate is answerable from stored rows.

They run against the isolated SQLite fixture, so cross-user isolation is proven here at the
repository/service layer (owner-scoped predicates). PostgreSQL RLS denial and the 0022 backfill
are proven only by apps/api/tests/integration/test_network_intelligence_postgres.py, which is
skipped until POSTGRES_TEST_DATABASE_URL is set.
"""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "supabase" / "migrations"


def _iso(offset_days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()


async def _create_person(client, headers, name: str, role: str | None = None) -> str:
    payload = {"name": name}
    if role:
        payload["role"] = role
    res = await client.post("/api/v1/people", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def _create_organization(client, headers, name: str, industry: str | None = None) -> str:
    payload = {"name": name}
    if industry:
        payload["industry"] = industry
    res = await client.post("/api/v1/organizations", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def _create_role(client, headers, person_id: str, organization_id: str, **kwargs) -> dict:
    payload = {"organization_id": organization_id, **kwargs}
    res = await client.post(
        f"/api/v1/people/{person_id}/organizations", json=payload, headers=headers
    )
    assert res.status_code == 201, res.text
    return res.json()


async def _create_commitment(client, headers, **kwargs) -> dict:
    res = await client.post("/api/v1/commitments", json=kwargs, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


# ---------------------------------------------------------------------------
# Multi-organization affiliation
# ---------------------------------------------------------------------------


async def test_person_can_belong_to_two_organizations_with_distinct_roles(
    async_client, auth_headers
):
    """The limitation this gate exists to fix: people.organization_id allowed only one."""
    person_id = await _create_person(async_client, auth_headers, "Nadia Rahman")
    acme_id = await _create_organization(async_client, auth_headers, "Acme Labs", "startup")
    beacon_id = await _create_organization(async_client, auth_headers, "Beacon Capital", "vc")

    await _create_role(
        async_client, auth_headers, person_id, acme_id, role="Founder", is_primary=True
    )
    await _create_role(async_client, auth_headers, person_id, beacon_id, role="Advisor")

    res = await async_client.get(
        f"/api/v1/people/{person_id}/organizations", headers=auth_headers
    )
    assert res.status_code == 200, res.text
    roles = res.json()
    assert len(roles) == 2
    assert {r["organization_id"] for r in roles} == {acme_id, beacon_id}
    assert {r["role"] for r in roles} == {"Founder", "Advisor"}
    # is_primary is a stored fact, not a derived ranking.
    assert [r["role"] for r in roles][0] == "Founder"
    assert roles[0]["is_primary"] is True


async def test_founder_and_advisor_roles_are_distinguishable_at_an_organization(
    async_client, auth_headers
):
    org_id = await _create_organization(async_client, auth_headers, "Orbit Systems", "startup")
    founder_id = await _create_person(async_client, auth_headers, "Imran Chowdhury")
    advisor_id = await _create_person(async_client, auth_headers, "Sara Kabir")

    await _create_role(async_client, auth_headers, founder_id, org_id, role="Co-Founder")
    await _create_role(async_client, auth_headers, advisor_id, org_id, role="Advisor")

    res = await async_client.get(f"/api/v1/organizations/{org_id}/people", headers=auth_headers)
    assert res.status_code == 200, res.text
    by_name = {row["name"]: row for row in res.json()}
    assert by_name["Imran Chowdhury"]["role"] == "Co-Founder"
    assert by_name["Sara Kabir"]["role"] == "Advisor"

    summary = await async_client.get(
        f"/api/v1/organizations/{org_id}/summary", headers=auth_headers
    )
    assert summary.status_code == 200, summary.text
    # "Co-Founder" counts as a founder; "Advisor" does not.
    assert summary.json()["founders_known"] == 1
    assert summary.json()["connected_people_count"] == 2


async def test_ended_role_is_retained_as_history_and_filterable(async_client, auth_headers):
    person_id = await _create_person(async_client, auth_headers, "Rafiq Alam")
    past_id = await _create_organization(async_client, auth_headers, "Previous Ventures")
    current_id = await _create_organization(async_client, auth_headers, "Current Ventures")

    historical = await _create_role(
        async_client,
        auth_headers,
        person_id,
        past_id,
        role="Head of Product",
        started_at=_iso(-900),
        ended_at=_iso(-400),
    )
    await _create_role(async_client, auth_headers, person_id, current_id, role="Founder")

    assert historical["ended_at"] is not None

    everything = await async_client.get(
        f"/api/v1/people/{person_id}/organizations?include_ended=true", headers=auth_headers
    )
    assert len(everything.json()) == 2

    current_only = await async_client.get(
        f"/api/v1/people/{person_id}/organizations?include_ended=false", headers=auth_headers
    )
    assert [r["organization_id"] for r in current_only.json()] == [current_id]

    # The historical row still exists; it was ended, not deleted.
    still_there = await async_client.get(
        f"/api/v1/organizations/{past_id}/people?include_ended=true", headers=auth_headers
    )
    assert [r["person_id"] for r in still_there.json()] == [person_id]
    assert still_there.json()[0]["is_current"] is False


async def test_role_cannot_reference_another_users_organization(
    async_client, auth_headers, other_auth_headers
):
    person_id = await _create_person(async_client, auth_headers, "Owner Contact")
    foreign_org_id = await _create_organization(async_client, other_auth_headers, "Foreign Org")

    res = await async_client.post(
        f"/api/v1/people/{person_id}/organizations",
        json={"organization_id": foreign_org_id, "role": "Founder"},
        headers=auth_headers,
    )
    assert res.status_code == 404, res.text


# ---------------------------------------------------------------------------
# Commitments
# ---------------------------------------------------------------------------


async def test_open_overdue_and_completed_commitments_are_separable(async_client, auth_headers):
    them_id = await _create_person(async_client, auth_headers, "Counterparty")

    open_future = await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=them_id,
        direction="owed_to_me",
        description="Send the term sheet",
        due_at=_iso(7),
    )
    overdue = await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=them_id,
        direction="owed_to_me",
        description="Intro to the lead investor",
        due_at=_iso(-5),
    )
    owed_by_me = await _create_commitment(
        async_client,
        auth_headers,
        to_person_id=them_id,
        direction="owed_by_me",
        description="Share the metrics deck",
        due_at=_iso(-2),
    )
    completed = await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=them_id,
        direction="owed_to_me",
        description="Already delivered",
        due_at=_iso(-30),
        status="completed",
        completed_at=_iso(-29),
    )

    all_open = await async_client.get(
        "/api/v1/commitments?commitment_status=open", headers=auth_headers
    )
    assert {c["id"] for c in all_open.json()} == {
        open_future["id"],
        overdue["id"],
        owed_by_me["id"],
    }

    overdue_res = await async_client.get(
        "/api/v1/commitments?overdue_only=true", headers=auth_headers
    )
    assert {c["id"] for c in overdue_res.json()} == {overdue["id"], owed_by_me["id"]}
    assert completed["id"] not in {c["id"] for c in overdue_res.json()}

    promised_to_me = await async_client.get(
        "/api/v1/commitments?direction=owed_to_me&commitment_status=open", headers=auth_headers
    )
    assert {c["description"] for c in promised_to_me.json()} == {
        "Send the term sheet",
        "Intro to the lead investor",
    }

    i_owe = await async_client.get(
        "/api/v1/commitments?direction=owed_by_me&commitment_status=open", headers=auth_headers
    )
    assert [c["description"] for c in i_owe.json()] == ["Share the metrics deck"]


async def test_completing_a_commitment_clears_it_from_the_overdue_ledger(
    async_client, auth_headers
):
    commitment = await _create_commitment(
        async_client,
        auth_headers,
        direction="owed_by_me",
        description="Reply to the partnership email",
        due_at=_iso(-1),
    )
    before = await async_client.get("/api/v1/commitments?overdue_only=true", headers=auth_headers)
    assert commitment["id"] in {c["id"] for c in before.json()}

    done = await async_client.post(
        f"/api/v1/commitments/{commitment['id']}/complete", headers=auth_headers
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "completed"
    assert done.json()["completed_at"] is not None

    after = await async_client.get("/api/v1/commitments?overdue_only=true", headers=auth_headers)
    assert commitment["id"] not in {c["id"] for c in after.json()}


async def test_organization_summary_counts_commitments_reached_through_its_people(
    async_client, auth_headers
):
    org_id = await _create_organization(async_client, auth_headers, "Summit Robotics", "startup")
    person_id = await _create_person(async_client, auth_headers, "Tanvir Hossain")
    await _create_role(async_client, auth_headers, person_id, org_id, role="Founder")

    await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=person_id,
        direction="owed_to_me",
        description="Pilot results",
        due_at=_iso(-3),
    )
    await _create_commitment(
        async_client,
        auth_headers,
        to_person_id=person_id,
        direction="owed_by_me",
        description="Warm intro",
        due_at=_iso(10),
    )
    await _create_commitment(
        async_client,
        auth_headers,
        to_person_id=person_id,
        direction="owed_by_me",
        description="Closed out",
        status="completed",
    )

    res = await async_client.get(f"/api/v1/organizations/{org_id}/summary", headers=auth_headers)
    body = res.json()
    assert body["connected_people_count"] == 1
    assert body["founders_known"] == 1
    assert body["open_commitments"] == 2
    assert body["overdue_commitments"] == 1
    # No unexplained relationship score is returned.
    assert not [key for key in body if "score" in key.lower()]


# ---------------------------------------------------------------------------
# Interaction-derived questions
# ---------------------------------------------------------------------------


async def test_last_interaction_and_topic_surface_on_the_organization_view(
    async_client, auth_headers
):
    org_id = await _create_organization(async_client, auth_headers, "Northwind AI", "startup")
    person_id = await _create_person(async_client, auth_headers, "Priya Das")
    await _create_role(async_client, auth_headers, person_id, org_id, role="Founder")

    for title, summary, when in (
        ("First coffee", "Discussed the seed round", _iso(-40)),
        ("Follow-up call", "Discussed the pilot scope", _iso(-3)),
    ):
        res = await async_client.post(
            "/api/v1/interactions",
            json={
                "person_id": person_id,
                "interaction_type": "meeting",
                "title": title,
                "summary": summary,
                "date": when,
            },
            headers=auth_headers,
        )
        assert res.status_code == 201, res.text

    people = await async_client.get(
        f"/api/v1/organizations/{org_id}/people", headers=auth_headers
    )
    row = people.json()[0]
    assert row["last_interaction_title"] == "Follow-up call"
    assert row["last_interaction_summary"] == "Discussed the pilot scope"

    summary_res = await async_client.get(
        f"/api/v1/organizations/{org_id}/summary", headers=auth_headers
    )
    assert summary_res.json()["last_interaction_at"] is not None


async def test_founders_not_spoken_to_in_thirty_days(async_client, auth_headers):
    org_id = await _create_organization(async_client, auth_headers, "Lantern Health", "startup")
    stale_id = await _create_person(async_client, auth_headers, "Stale Founder")
    recent_id = await _create_person(async_client, auth_headers, "Recent Founder")
    advisor_id = await _create_person(async_client, auth_headers, "Quiet Advisor")

    await _create_role(async_client, auth_headers, stale_id, org_id, role="Founder")
    await _create_role(async_client, auth_headers, recent_id, org_id, role="Founder")
    await _create_role(async_client, auth_headers, advisor_id, org_id, role="Advisor")

    for person_id, when in ((stale_id, _iso(-90)), (recent_id, _iso(-2))):
        await async_client.post(
            "/api/v1/interactions",
            json={"person_id": person_id, "title": "Sync", "date": when},
            headers=auth_headers,
        )

    res = await async_client.get(
        "/api/v1/network/stale-contacts?days=30&founders_only=true", headers=auth_headers
    )
    assert res.status_code == 200, res.text
    names = {row["name"] for row in res.json()}
    assert names == {"Stale Founder"}
    assert res.json()[0]["days_since_last_interaction"] >= 30

    # Widening the filter picks up the never-contacted advisor, with a null timestamp
    # rather than an invented one.
    everyone = await async_client.get(
        "/api/v1/network/stale-contacts?days=30", headers=auth_headers
    )
    quiet = next(row for row in everyone.json() if row["name"] == "Quiet Advisor")
    assert quiet["last_interaction_at"] is None
    assert quiet["days_since_last_interaction"] is None


async def test_network_overview_counts_organizations_by_recorded_industry(
    async_client, auth_headers
):
    person_id = await _create_person(async_client, auth_headers, "Connector")
    for name, industry in (
        ("Startup One", "startup"),
        ("Startup Two", "startup"),
        ("Big Bank", "finance"),
    ):
        org_id = await _create_organization(async_client, auth_headers, name, industry)
        await _create_role(async_client, auth_headers, person_id, org_id, role="Contact")

    # An organization with nobody connected is not "in my network".
    await _create_organization(async_client, auth_headers, "Unconnected Co", "startup")

    overview = await async_client.get("/api/v1/network/overview", headers=auth_headers)
    body = overview.json()
    assert body["organizations_count"] == 3
    assert body["organizations_by_industry"] == {"finance": 1, "startup": 2}

    startups = await async_client.get(
        "/api/v1/network/overview?industry=startup", headers=auth_headers
    )
    assert startups.json()["organizations_count"] == 2


async def test_venture_network_lists_people_with_recorded_evidence(async_client, auth_headers):
    venture_res = await async_client.post(
        "/api/v1/ventures", json={"name": "Mangosteen"}, headers=auth_headers
    )
    assert venture_res.status_code == 201, venture_res.text
    venture_id = venture_res.json()["id"]

    involved_id = await _create_person(async_client, auth_headers, "Involved Person")
    unrelated_id = await _create_person(async_client, auth_headers, "Unrelated Person")

    await async_client.post(
        "/api/v1/interactions",
        json={"person_id": involved_id, "venture_id": venture_id, "title": "Venture sync"},
        headers=auth_headers,
    )
    await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=involved_id,
        venture_id=venture_id,
        direction="owed_to_me",
        description="Intro to a design partner",
    )
    await async_client.post(
        "/api/v1/interactions",
        json={"person_id": unrelated_id, "title": "Unrelated chat"},
        headers=auth_headers,
    )

    res = await async_client.get(
        f"/api/v1/network/ventures/{venture_id}/people", headers=auth_headers
    )
    assert res.status_code == 200, res.text
    assert [row["name"] for row in res.json()] == ["Involved Person"]
    assert res.json()[0]["interaction_count"] == 1
    assert res.json()[0]["commitment_count"] == 1


async def test_person_relationship_answers_both_ledgers_at_once(async_client, auth_headers):
    org_id = await _create_organization(async_client, auth_headers, "Delta Works", "startup")
    person_id = await _create_person(async_client, auth_headers, "Full Picture")
    await _create_role(async_client, auth_headers, person_id, org_id, role="Founder")

    await async_client.post(
        "/api/v1/interactions",
        json={"person_id": person_id, "title": "Strategy call", "summary": "Discussed hiring"},
        headers=auth_headers,
    )
    await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=person_id,
        direction="owed_to_me",
        description="Candidate referrals",
        due_at=_iso(-4),
    )
    await _create_commitment(
        async_client,
        auth_headers,
        to_person_id=person_id,
        direction="owed_by_me",
        description="Job description draft",
        due_at=_iso(5),
    )

    res = await async_client.get(
        f"/api/v1/network/people/{person_id}/relationship", headers=auth_headers
    )
    body = res.json()
    assert [r["role"] for r in body["roles"]] == ["Founder"]
    assert body["last_interaction_title"] == "Strategy call"
    assert body["last_interaction_summary"] == "Discussed hiring"
    assert [c["description"] for c in body["they_promised_me"]] == ["Candidate referrals"]
    assert [c["description"] for c in body["i_owe_them"]] == ["Job description draft"]
    assert [c["description"] for c in body["overdue_commitments"]] == ["Candidate referrals"]


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------


async def test_relationship_graph_is_invisible_across_users(
    async_client, auth_headers, other_auth_headers
):
    org_id = await _create_organization(async_client, auth_headers, "Private Org", "startup")
    person_id = await _create_person(async_client, auth_headers, "Private Contact")
    role = await _create_role(async_client, auth_headers, person_id, org_id, role="Founder")
    commitment = await _create_commitment(
        async_client,
        auth_headers,
        from_person_id=person_id,
        direction="owed_to_me",
        description="Private promise",
        due_at=_iso(-1),
    )

    assert (
        await async_client.get(
            f"/api/v1/organizations/{org_id}/summary", headers=other_auth_headers
        )
    ).status_code == 404
    assert (
        await async_client.get(
            f"/api/v1/organizations/{org_id}/people", headers=other_auth_headers
        )
    ).status_code == 404
    assert (
        await async_client.get(
            f"/api/v1/people/{person_id}/organizations", headers=other_auth_headers
        )
    ).status_code == 404
    assert (
        await async_client.get(
            f"/api/v1/commitments/{commitment['id']}", headers=other_auth_headers
        )
    ).status_code == 404
    assert (
        await async_client.patch(
            f"/api/v1/network/roles/{role['id']}",
            json={"role": "Hijacked"},
            headers=other_auth_headers,
        )
    ).status_code == 404

    other_overview = await async_client.get(
        "/api/v1/network/overview", headers=other_auth_headers
    )
    assert other_overview.json()["organizations_count"] == 0
    other_ledger = await async_client.get(
        "/api/v1/commitments?overdue_only=true", headers=other_auth_headers
    )
    assert other_ledger.json() == []

    # The owner still sees everything.
    owner_ledger = await async_client.get(
        "/api/v1/commitments?overdue_only=true", headers=auth_headers
    )
    assert [c["description"] for c in owner_ledger.json()] == ["Private promise"]


async def test_unauthenticated_access_is_rejected(async_client):
    for path in (
        "/api/v1/network/overview",
        "/api/v1/commitments",
        "/api/v1/network/stale-contacts",
    ):
        res = await async_client.get(path)
        assert res.status_code in (401, 403), (path, res.status_code)


# ---------------------------------------------------------------------------
# Migration contract (G1 authority preserved)
# ---------------------------------------------------------------------------


def _migration_0022() -> str:
    path = next(MIGRATIONS_DIR.glob("*_network_relationship_intelligence.sql"))
    return path.read_text(encoding="utf-8")


def test_migration_0022_is_registered_in_the_schema_contract():
    from app.db.schema_contract import APPLICATION_REQUIRED_TABLES, MIGRATION_FILES

    on_disk = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert on_disk == sorted(MIGRATION_FILES)
    assert "20260828000022_network_relationship_intelligence.sql" in MIGRATION_FILES
    assert {"person_organization_roles", "commitments"} <= set(APPLICATION_REQUIRED_TABLES)


def test_migration_0022_preserves_the_legacy_fields():
    """Deprecated in place: marked, backfilled, never dropped."""
    source = _migration_0022()
    assert "DROP COLUMN" not in source.upper()
    assert "people.organization_id" in source
    assert "interactions.commitments" in source
    assert "COMMENT ON COLUMN public.people.organization_id" in source
    assert "COMMENT ON COLUMN public.interactions.commitments" in source
    assert "INSERT INTO public.person_organization_roles" in source
    assert "INSERT INTO public.commitments" in source


def test_migration_0022_does_not_guess_commitment_direction():
    """The legacy TEXT[] never recorded who owed whom; the backfill must not invent it."""
    source = _migration_0022()
    backfill = source.split("INSERT INTO public.commitments", 1)[1]
    assert "'unspecified'" in backfill
    assert "'owed_to_me'" not in backfill
    assert "'owed_by_me'" not in backfill


def test_migration_0022_policies_use_the_g2_owner_form():
    source = _migration_0022()
    policies = re.findall(r"CREATE POLICY.*?;", source, re.DOTALL)
    assert len(policies) == 4
    for statement in policies:
        assert "auth.uid() IS NOT NULL AND user_id = auth.uid()" in statement, statement


def test_new_tables_are_mapped_by_the_orm():
    from app.models.entities import Base

    assert {"person_organization_roles", "commitments"} <= set(Base.metadata.tables)


@pytest.mark.parametrize(
    "direction", ["owed_to_me", "owed_by_me", "unspecified"]
)
def test_commitment_direction_vocabulary_matches_the_check_constraint(direction):
    source = _migration_0022()
    assert f"'{direction}'" in source
