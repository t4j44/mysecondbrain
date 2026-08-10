"""
Unit and Integration Tests for Idea Vault Module
Module Owner: Agent 9
Verifies data isolation, atomic conversion, and AI strategic evaluation without fabricated metrics.
"""

import pytest

from app.repositories.ideas import IdeaRepository
from app.services.ideas.idea_service import IdeaService


class MockTable:
    def __init__(self, data_store: dict, name: str):
        self.data_store = data_store
        self.name = name
        self._filter_user = None
        self._filter_id = None
        self._null_col = None
        self._updates = None

    def select(self, *args):
        return self

    def eq(self, col, val):
        if col == "user_id":
            self._filter_user = val
        if col == "id":
            self._filter_id = val
        return self

    def is_(self, col, val):
        self._null_col = col
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args):
        return self

    def offset(self, *args):
        return self

    async def execute(self):
        records = self.data_store.get(self.name, [])
        matching = [
            r
            for r in records
            if (not self._filter_user or r.get("user_id") == self._filter_user)
            and (not self._filter_id or r.get("id") == self._filter_id)
            and (not self._null_col or r.get("deleted_at") is None)
        ]
        if self._updates is not None:
            for r in matching:
                r.update(self._updates)

        class Result:
            pass

        res = Result()
        res.data = matching
        return res

    def insert(self, record):
        self.data_store.setdefault(self.name, []).append(record)
        return self

    def update(self, updates):
        self._updates = updates
        return self


class MockDbClient:
    def __init__(self):
        self.data = {"ideas": [], "projects": []}

    def table(self, name: str):
        return MockTable(self.data, name)


@pytest.mark.asyncio
async def test_idea_creation_and_isolation():
    db = MockDbClient()
    repo = IdeaRepository(db)
    service = IdeaService(repo)

    user_a = "user-aaa-111"
    user_b = "user-bbb-222"

    payload = {
        "title": "Test Hypothesis: Autonomous Agents",
        "problem": "Testing isolation boundaries",
        "status": "captured",
    }
    created = await service.create_idea(user_a, payload)

    assert created["user_id"] == user_a
    assert created["title"] == payload["title"]

    # User B should receive zero records due to strict RLS filter
    listed_b = await service.list_ideas(user_b)
    assert len(listed_b) == 0

    listed_a = await service.list_ideas(user_a)
    assert len(listed_a) == 1
    assert listed_a[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_atomic_idea_to_project_conversion():
    db = MockDbClient()
    repo = IdeaRepository(db)
    service = IdeaService(repo)
    user_id = "user-aaa-111"

    created_idea = await service.create_idea(
        user_id, {"title": "Convertible Idea", "solution": "Project Solution"}
    )
    idea_id = created_idea["id"]

    res = await service.convert_to_project(user_id, idea_id, {"name": "Execution Project #1"})

    assert res["idea_status"] == "converted"
    assert "new_project_id" in res
    assert len(db.data["projects"]) == 1
    assert db.data["projects"][0]["name"] == "Execution Project #1"

    # Verify historical idea record was preserved and status updated to converted
    existing_idea = await service.get_idea(user_id, idea_id)
    assert existing_idea is not None
    assert existing_idea["status"] == "converted"


@pytest.mark.asyncio
async def test_ai_feasibility_non_vanity_evaluation():
    db = MockDbClient()
    service = IdeaService(IdeaRepository(db))
    user_id = "user-aaa-111"

    created = await service.create_idea(
        user_id,
        {
            "title": "AI Validator",
            "problem": "Short prob",
            "solution": "Deep scalable automated workflow pipeline architecture with RLS authentication and zero hallucination policies.",
        },
    )

    analysis = await service.analyze_idea_feasibility(user_id, created["id"])
    assert 1 <= analysis["problem_clarity_score"] <= 10
    assert 1 <= analysis["solution_viability_score"] <= 10
    assert "recommended_next_experiment" in analysis
    # Ensure no fabricated financial projections exist in result
    assert "projected_mrr" not in analysis
    assert "estimated_tam_billion_dollars" not in analysis
