"""
Unit and Integration Tests for Career Proof Case Studies
Module Owner: Agent 9
Verifies evidence-grounded case study generation and section coverage reporting.
"""

import pytest

from app.services.portfolio.portfolio_service import PortfolioService


class MockAchievementRepo:
    async def get_by_id(self, user_id, achievement_id):
        if achievement_id == "ach-valid-1" and user_id == "usr-taj":
            return {
                "id": "ach-valid-1",
                "title": "Built RAG pgvector pipeline",
                "role": "AI Product Manager",
                "impact": "Eliminated tool hallucinations",
                "skills": ["RAG", "pgvector", "Python"],
                "verification_status": "verified",
            }
        return None


class MockPortfolioRepo:
    async def create_case_study(self, user_id, data):
        data["id"] = "cs-test-99"
        data["user_id"] = user_id
        return data


@pytest.mark.asyncio
async def test_case_study_generation_without_hallucinations():
    ach_repo = MockAchievementRepo()
    port_repo = MockPortfolioRepo()
    service = PortfolioService(repo=port_repo, achievement_repo=ach_repo)

    user_id = "usr-taj"
    payload = {
        "target_role": "VP of AI",
        "selected_achievement_ids": ["ach-valid-1"],
        "target_audience": "Tech VC Partners",
    }

    res = await service.generate_grounded_case_study(user_id, payload)

    assert res["target_role"] == "VP of AI"
    assert res["status"] == "draft"  # Enforce initial draft status for user verification
    assert len(res["linked_achievement_ids"]) == 1
    assert "section_coverage" in res
    assert res["section_coverage"]["problem"] == "supported"
    assert len(res["citations"]) == 1
    assert res["citations"][0]["claim_supported"] == "Eliminated tool hallucinations"
    # Ensure no fabricated financial metrics or unauthorized past corporate roles exist in output
    assert "Stripe Executive" not in res["full_markdown_case"]
    assert "100 million users" not in res["full_markdown_case"]
