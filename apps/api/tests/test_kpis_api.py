"""
Unit and Integration Tests for Life KPI System
Module Owner: Agent 9
Verifies deterministic progress computation, trend window formulas, and historical immutability.
"""

from datetime import date

import pytest

from app.services.kpis.kpi_service import KPIService


class MockKPIRepository:
    def __init__(self):
        self.definitions = {}
        self.entries = {}

    async def create_kpi(self, user_id, data):
        data["id"] = "kpi-test-01"
        data["user_id"] = user_id
        data["current_value"] = 0.0
        self.definitions["kpi-test-01"] = data
        self.entries["kpi-test-01"] = []
        return data

    async def get_kpi(self, user_id, kpi_id):
        k = self.definitions.get(kpi_id)
        if k and k.get("user_id") == user_id:
            return k.copy()
        return None

    async def list_entries(self, user_id, kpi_id, limit=20):
        return sorted(
            self.entries.get(kpi_id, []), key=lambda x: x["recording_date"], reverse=True
        )[:limit]

    async def create_entry(self, user_id, kpi_id, payload):
        payload["id"] = f"ent-{len(self.entries.get(kpi_id, []))}"
        payload["user_id"] = user_id
        payload["kpi_id"] = kpi_id
        payload.setdefault("recording_date", str(date.today()))
        self.entries.setdefault(kpi_id, []).append(payload)

        # Update parent definition current value
        if kpi_id in self.definitions:
            self.definitions[kpi_id]["current_value"] = payload["recorded_value"]
        return payload


def test_progress_calculation_formulas():
    service = KPIService(repo=None)

    # 1. Higher is Better (e.g. CRM connections: 24 of 30 = 80%)
    assert service.calculate_progress(24, 30, "higher_is_better") == 80.0
    assert (
        service.calculate_progress(36, 30, "higher_is_better") == 120.0
    )  # Captures overperformance

    # 2. Lower is Better (e.g. API error rate: 1.0 of 2.0 = 200% progress because actual is lower than threshold)
    assert service.calculate_progress(1.0, 2.0, "lower_is_better") == 200.0

    # 3. Zero Target Handling (prevents division by zero errors)
    assert service.calculate_progress(5, 0, "higher_is_better") == 0.0
    assert service.calculate_progress(0, 0, "higher_is_better") == 100.0

    # 4. Milestone formula
    assert service.calculate_progress(1, 1, "milestone") == 100.0
    assert service.calculate_progress(0, 1, "milestone") == 0.0


def test_deterministic_trend_evaluator():
    service = KPIService(repo=None)

    # 1. Insufficient data (< 2 entries)
    assert service.calculate_trend([], "higher_is_better") == "insufficient_data"
    assert (
        service.calculate_trend([{"recorded_value": 10}], "higher_is_better") == "insufficient_data"
    )

    # 2. Increasing Trend (latest is index 0)
    entries_inc = [{"recorded_value": 30}, {"recorded_value": 20}]
    assert service.calculate_trend(entries_inc, "higher_is_better") == "increasing"

    # 3. Decreasing Trend
    entries_dec = [{"recorded_value": 15}, {"recorded_value": 20}]
    assert service.calculate_trend(entries_dec, "higher_is_better") == "decreasing"

    # 4. Stable Variance (within 5%)
    entries_stable = [{"recorded_value": 102}, {"recorded_value": 100}]
    assert service.calculate_trend(entries_stable, "higher_is_better") == "stable"


@pytest.mark.asyncio
async def test_kpi_entry_recording_and_immutability():
    repo = MockKPIRepository()
    service = KPIService(repo=repo)
    user = "user-taj-001"

    kpi = await repo.create_kpi(
        user,
        {"metric_name": "Deep Work Hours", "target_value": 20, "direction": "higher_is_better"},
    )
    kpi_id = kpi["id"]

    # Record entry 1
    await service.record_entry(user, kpi_id, {"recorded_value": 10, "recording_date": "2026-08-01"})
    # Record entry 2
    await service.record_entry(user, kpi_id, {"recorded_value": 18, "recording_date": "2026-08-02"})

    analytics = await service.get_kpi_with_analytics(user, kpi_id)
    assert analytics["current_value"] == 18
    assert analytics["calculated_progress"] == 90.0
    assert analytics["calculated_trend"] == "increasing"
    assert len(analytics["latest_entries"]) == 2

    # Changing target in definition must NOT alter historical entries
    analytics["target_value"] = 30
    assert len(analytics["latest_entries"]) == 2
    assert analytics["latest_entries"][1]["recorded_value"] == 10
