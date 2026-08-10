"""
Achievement Portfolio & Verification Service
Module Owner: Agent 9
Enforces evidence-based claim verification without granting automatic AI approvals.
"""

import re
from typing import Any, Dict, List, Optional


class AchievementService:
    def __init__(self, repo: Any):
        self.repo = repo

    def evaluate_verification_status(
        self, impact: str, evidence_items: List[Dict[str, Any]]
    ) -> str:
        """
        Determines verification status from linked Second Brain sources.
        - self_reported: Zero evidence items attached.
        - supported: Attached to internal meetings, decisions, or projects.
        - verified: Attached to explicit quantitative KPI check-in records or verified external URLs.
        - needs_evidence: Contains strong numerical claims in text without sufficient supporting links.
        """
        has_numbers = bool(
            re.search(
                r"\d+([%xX$MK]|\s*(users|clients|arr|revenue|hours|reduction))",
                impact,
                re.IGNORECASE,
            )
        )

        if not evidence_items:
            return "needs_evidence" if has_numbers else "self_reported"

        has_kpi_proof = any(
            ev.get("source_type") == "kpi_entry" or bool(ev.get("external_url"))
            for ev in evidence_items
        )
        if has_kpi_proof:
            return "verified"

        return "supported"

    async def get_achievement(self, user_id: str, achievement_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_by_id(user_id, achievement_id)

    async def list_achievements(
        self, user_id: str, venture_id: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        return await self.repo.list_achievements(user_id, venture_id, limit, offset)

    async def create_achievement(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        evidence_items = data.get("evidence_items", [])
        impact = data.get("impact", "")

        # Automatically assign verification status if not explicitly overriden by auditor
        if "verification_status" not in data or data["verification_status"] == "self_reported":
            data["verification_status"] = self.evaluate_verification_status(impact, evidence_items)

        return await self.repo.create_achievement(user_id, data)

    async def update_achievement(
        self, user_id: str, achievement_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if "impact" in updates or "evidence_items" in updates:
            existing = await self.get_achievement(user_id, achievement_id)
            if existing:
                impact = updates.get("impact", existing.get("impact", ""))
                evidence = updates.get("evidence_items", existing.get("evidence_items", []))
                updates["verification_status"] = self.evaluate_verification_status(impact, evidence)

        return await self.repo.update_achievement(user_id, achievement_id, updates)

    async def delete_achievement(self, user_id: str, achievement_id: str) -> bool:
        return await self.repo.delete_achievement(user_id, achievement_id)
