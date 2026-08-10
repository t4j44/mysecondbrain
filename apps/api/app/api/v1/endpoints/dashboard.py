from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DashboardSummaryResponse(BaseModel):
    current_mission: str
    today_focus: List[str]
    active_projects_count: int
    open_tasks_count: int
    kpi_overview: Dict[str, Any]
    recent_memories: List[Dict[str, Any]]
    ai_insight: str


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary():
    """
    Get aggregated summary data for Taj's Founder Dashboard command center.
    """
    return DashboardSummaryResponse(
        current_mission="Justor AI - Legal AI Accessibility Platform",
        today_focus=[
            "Complete product roadmap for Justor AI MVP",
            "Follow up with Yousuf Imran regarding founder mentorship",
            "Review pitch deck feedback from seed investors",
            "Finalize pgvector hybrid memory search implementation",
        ],
        active_projects_count=4,
        open_tasks_count=12,
        kpi_overview={
            "projects_completed": 8,
            "users_acquired": 1500,
            "meaningful_connections": 42,
            "revenue_milestone": "$12.5k ARR",
        },
        recent_memories=[
            {
                "id": "mem-1",
                "title": "Founder Meetup Dhaka Notes",
                "summary": "Met Yousuf Imran from Mangosteen Studio. Key takeaway: focus relentlessly on customer retention.",
                "date": "2026-08-01",
            },
            {
                "id": "mem-2",
                "title": "Justor AI Legal Agent Architecture",
                "summary": "Designed multi-agent workflow using Gemini 3.5 Flash for contract clause analysis.",
                "date": "2026-07-28",
            },
        ],
        ai_insight="Your biggest bottleneck this week is execution speed on Justor AI user testing. Focus 80% of today on customer validation.",
    )
