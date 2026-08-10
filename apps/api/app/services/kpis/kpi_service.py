"""
Life KPI System Service
Module Owner: Agent 9
Implements deterministic non-vanity progress formulas and historical trend calculations.
"""

from typing import Any, Dict, List, Optional


class KPIService:
    def __init__(self, repo: Any):
        self.repo = repo

    def calculate_progress(self, current_val: float, target_val: float, direction: str) -> float:
        """
        Deterministic progress calculation rule respecting KPI directionality.
        """
        if direction == "milestone":
            return 100.0 if current_val >= target_val and target_val > 0 else 0.0

        if target_val == 0:
            return 100.0 if current_val == 0 else 0.0

        if direction == "higher_is_better":
            # Retain actual percentage even above 100% for overperformance analysis
            return round((current_val / target_val) * 100.0, 2)
        elif direction == "lower_is_better":
            # If target is lower is better, dropping below target is success
            if current_val == 0:
                return 100.0
            progress = round((target_val / current_val) * 100.0, 2)
            return max(0.0, progress)
        return round((current_val / target_val) * 100.0, 2)

    def calculate_trend(
        self, entries: List[Dict[str, Any]], direction: str = "higher_is_better"
    ) -> str:
        """
        Deterministic historical trend evaluation without AI guesswork.
        Requires at least 2 historical entries to assert a trend.
        """
        if not entries or len(entries) < 2:
            return "insufficient_data"

        # Entries are sorted descending by date
        latest_val = entries[0]["recorded_value"]
        prev_val = entries[1]["recorded_value"]

        if prev_val == 0:
            variance = 100.0 if latest_val > 0 else 0.0
        else:
            variance = ((latest_val - prev_val) / abs(prev_val)) * 100.0

        if abs(variance) < 5.0:
            return "stable"

        if direction == "higher_is_better":
            return "increasing" if variance > 0 else "decreasing"
        elif direction == "lower_is_better":
            # For bug counts or churn, a numerical decrease represents an increasing positive trend
            return "increasing" if variance < 0 else "decreasing"

        return "increasing" if variance > 0 else "decreasing"

    async def get_kpi_with_analytics(self, user_id: str, kpi_id: str) -> Optional[Dict[str, Any]]:
        kpi = await self.repo.get_kpi(user_id, kpi_id)
        if not kpi:
            return None

        entries = await self.repo.list_entries(user_id, kpi_id, limit=20)
        direction = kpi.get("direction", "higher_is_better")

        kpi["latest_entries"] = entries
        kpi["calculated_progress"] = self.calculate_progress(
            kpi.get("current_value", 0.0), kpi.get("target_value", 0.0), direction
        )
        kpi["calculated_trend"] = self.calculate_trend(entries, direction)
        return kpi

    async def list_kpis_with_analytics(
        self, user_id: str, category: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        kpis = await self.repo.list_kpis(user_id, category, limit, offset)
        enhanced = []
        for kpi in kpis:
            entries = await self.repo.list_entries(user_id, kpi["id"], limit=5)
            direction = kpi.get("direction", "higher_is_better")
            kpi["latest_entries"] = entries
            kpi["calculated_progress"] = self.calculate_progress(
                kpi.get("current_value", 0.0), kpi.get("target_value", 0.0), direction
            )
            kpi["calculated_trend"] = self.calculate_trend(entries, direction)
            enhanced.append(kpi)
        return enhanced

    async def record_entry(
        self, user_id: str, kpi_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Records time-series KPI check-in and updates definition current_value without altering past records.
        """
        kpi = await self.repo.get_kpi(user_id, kpi_id)
        if not kpi:
            raise ValueError("KPI not found or unauthorized.")
        return await self.repo.create_entry(user_id, kpi_id, payload)
