"""
Unit and Integration Tests for Achievement Portfolio
Module Owner: Agent 9
Verifies evidence verification status logic and prevention of unverified numeric claims.
"""

from app.services.achievements.achievement_service import AchievementService


def test_verification_status_evaluator():
    service = AchievementService(repo=None)

    # 1. Self-reported: qualitative claim with zero evidence attachments
    assert (
        service.evaluate_verification_status("Refactored background tasks", []) == "self_reported"
    )

    # 2. Needs evidence: strong numerical traction claim (e.g. 10x growth, $50k revenue) without supporting records
    assert (
        service.evaluate_verification_status("Achieved 10x user growth in one week", [])
        == "needs_evidence"
    )
    assert (
        service.evaluate_verification_status("Generated $500,000 ARR in 2 months", [])
        == "needs_evidence"
    )

    # 3. Supported: internal decision or memory links attached
    supported_ev = [{"source_id": "mem-1", "source_type": "memory"}]
    assert (
        service.evaluate_verification_status("Architected system database schema", supported_ev)
        == "supported"
    )

    # 4. Verified: attached directly to an immutable KPI entry record or external verified URL
    verified_ev_kpi = [{"source_id": "kpi-88", "source_type": "kpi_entry"}]
    assert (
        service.evaluate_verification_status(
            "Reached 25 meaningful founder connections", verified_ev_kpi
        )
        == "verified"
    )

    verified_ev_url = [
        {
            "source_id": "url-1",
            "source_type": "external_url",
            "external_url": "https://github.com/taj/second-brain/pull/44",
        }
    ]
    assert (
        service.evaluate_verification_status(
            "Optimized database search query speed by 40%", verified_ev_url
        )
        == "verified"
    )
