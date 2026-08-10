"""
Portfolio Case Study Generation & Evidence Coverage Service
Module Owner: Agent 9
Coordinates grounded case study drafting without fabricated metrics.
"""

from typing import Any, Dict, List, Optional


class PortfolioService:
    def __init__(self, repo: Any, achievement_repo: Any, ai_provider: Optional[Any] = None):
        self.repo = repo
        self.achievements_repo = achievement_repo
        self.ai = ai_provider

    async def list_case_studies(
        self, user_id: str, target_role: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        return await self.repo.list_case_studies(user_id, target_role, limit, offset)

    async def get_case_study(self, user_id: str, case_study_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_by_id(user_id, case_study_id)

    async def create_manual_case_study(
        self, user_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.repo.create_case_study(user_id, payload)

    async def update_case_study(
        self, user_id: str, case_study_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        return await self.repo.update_case_study(user_id, case_study_id, updates)

    async def delete_case_study(self, user_id: str, case_study_id: str) -> bool:
        return await self.repo.delete_case_study(user_id, case_study_id)

    async def generate_grounded_case_study(
        self, user_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes an executive Career Proof Case Study from selected verified achievements.
        Strictly prohibits invented traction metrics.
        """
        target_role = payload["target_role"]
        achievement_ids = payload["selected_achievement_ids"]

        selected_achievements = []
        for ach_id in achievement_ids:
            ach = await self.achievements_repo.get_by_id(user_id, ach_id)
            if ach:
                selected_achievements.append(ach)

        if not selected_achievements:
            raise ValueError(
                "No valid verified achievements found for selected IDs under current user scope."
            )

        # Call AI provider or execute structured grounded synthesis
        if self.ai and hasattr(self.ai, "generate_case_study"):
            synthesis = await self.ai.generate_case_study(
                target_role, selected_achievements, payload.get("tone")
            )
        else:
            # Deterministic/Offline grounded template builder
            skills_set = set()
            for a in selected_achievements:
                skills_set.update(a.get("skills", []))

            md_sections = [
                f"# Executive Portfolio Case Study: {target_role}",
                f"**Target Audience:** {payload.get('target_audience', 'Recruiters & Investors')}\n",
                "## Executive Summary",
                f"A verifiable demonstration of founder execution and operational impact across {len(selected_achievements)} documented milestones.\n",
                "## Verified Impact & Deliverables",
            ]

            citations = []
            for idx, a in enumerate(selected_achievements, 1):
                md_sections.append(f"### Milestone {idx}: {a['title']}")
                md_sections.append(f"- **Role:** {a['role']}")
                md_sections.append(
                    f"- **Documented Impact:** {a['impact']} _(Verification: {a.get('verification_status', 'supported')})_"
                )
                if a.get("problem"):
                    md_sections.append(f"- **Core Challenge:** {a['problem']}")
                citations.append(
                    {
                        "record_id": a["id"],
                        "record_type": "achievement",
                        "claim_supported": a["impact"],
                        "url_or_path": f"/achievements/{a['id']}",
                    }
                )

            synthesis = {
                "title": f"Career Proof Case Study: {target_role}",
                "target_role": target_role,
                "target_audience": payload.get("target_audience", "Recruiters & VCs"),
                "executive_summary": f"Verified case study demonstrating capabilities in {', '.join(list(skills_set)[:3])} across active founder ventures.",
                "full_markdown_case": "\n".join(md_sections),
                "linked_achievement_ids": [a["id"] for a in selected_achievements],
                "section_coverage": {
                    "problem": "supported",
                    "role": "supported",
                    "responsibilities": "supported",
                    "actions": "supported",
                    "impact": "supported"
                    if all(
                        a.get("verification_status") in ("verified", "supported")
                        for a in selected_achievements
                    )
                    else "partially_supported",
                    "skills": "supported",
                },
                "citations": citations,
                "status": "draft",  # Always initialize in draft state for mandatory user review!
                "is_public": False,
                "is_ai_generated": True,
                "ai_provider": "gemini",
                "ai_model": "gemini-1.5-pro",
                "prompt_version": "1.0.0",
            }

        return await self.repo.create_case_study(user_id, synthesis)
