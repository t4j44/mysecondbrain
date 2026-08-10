"""
Taj's Second Brain - Model Context Protocol (MCP) Server

Exposes Taj's personal knowledge, CRM, tasks, ventures, and AI tools
to external AI assistants (ChatGPT, Claude, Gemini, Claude Code).
"""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Taj's Second Brain MCP Server")


@mcp.tool()
def search_people(query: str, relationship_type: Optional[str] = None) -> str:
    """
    Search Taj's network CRM contacts by name, company, role, or relationship type.
    """
    results = [
        {
            "name": "Yousuf Imran",
            "role": "Founder / Mentor",
            "company": "Mangosteen Studio",
            "relationship": "mentor",
            "last_interaction": "Founder Meetup Dhaka (2026-08-01)",
            "insights": ["Startup execution", "Founder mindset"],
            "next_action": "Share Justor AI update",
        },
        {
            "name": "Amina Rahman",
            "role": "VP of Product",
            "company": "TechVentures Asia",
            "relationship": "investor",
            "last_interaction": "Pitch Deck Review (2026-07-20)",
            "insights": ["Requires monthly KPI updates"],
            "next_action": "Send Q3 KPI deck",
        },
    ]
    if query:
        q = query.lower()
        results = [r for r in results if q in r["name"].lower() or q in r["company"].lower()]
    return json.dumps(results, indent=2)


@mcp.tool()
def search_memory(query: str, top_k: int = 5) -> str:
    """
    Semantic vector RAG search across Taj's personal memories, meeting notes, decisions, and documents.
    """
    memories = [
        {
            "title": "Founder Meetup Dhaka Notes",
            "snippet": "Discussed startup execution velocity with Yousuf Imran. Focus on fast MVP validation.",
            "similarity": 0.92,
            "category": "CRM & Meeting",
        },
        {
            "title": "Justor AI Legal Agent Architecture",
            "snippet": "Designed multi-agent workflow using Gemini 3.5 Flash for contract clause analysis.",
            "similarity": 0.88,
            "category": "Venture Strategy",
        },
    ]
    return json.dumps(memories[:top_k], indent=2)


@mcp.tool()
def get_projects(venture_slug: Optional[str] = None) -> str:
    """
    Retrieve active projects under Taj's ventures (Justor AI, Zqtion, IEXF, CMOOS).
    """
    projects = [
        {
            "name": "Justor AI MVP Launch",
            "venture": "Justor AI",
            "status": "in_progress",
            "target_date": "2026-08-30",
        },
        {
            "name": "Zqtion Workflow Automation",
            "venture": "Zqtion",
            "status": "planning",
            "target_date": "2026-09-15",
        },
        {
            "name": "IEXF Partner Onboarding",
            "venture": "IEXF",
            "status": "in_progress",
            "target_date": "2026-08-20",
        },
        {
            "name": "CMOOS Brand Architecture",
            "venture": "CMOOS",
            "status": "completed",
            "target_date": "2026-07-15",
        },
    ]
    if venture_slug:
        projects = [p for p in projects if p["venture"].lower() == venture_slug.lower()]
    return json.dumps(projects, indent=2)


@mcp.tool()
def get_tasks(status: Optional[str] = "todo") -> str:
    """
    Retrieve tasks from Taj's Linear/Notion-inspired task management system.
    """
    tasks = [
        {
            "title": "Complete product roadmap",
            "priority": "high",
            "due_date": "2026-08-05",
            "venture": "Justor AI",
        },
        {
            "title": "Follow up investor Yousuf Imran",
            "priority": "medium",
            "due_date": "2026-08-06",
            "venture": "Justor AI",
        },
        {
            "title": "Review user feedback on legal contract parser",
            "priority": "urgent",
            "due_date": "2026-08-05",
            "venture": "Justor AI",
        },
    ]
    return json.dumps(tasks, indent=2)


@mcp.tool()
def generate_linkedin_post(topic: str) -> str:
    """
    Generate an authentic LinkedIn founder post using Taj's past experiences and writing style.
    """
    return f"""🚀 Building in public: Reflections on {topic}

As a founder building AI-native products like Justor AI, I've realized that execution speed isn't just about writing code—it's about learning velocity.

Here are 3 key takeaways from my journey:
1️⃣ Focus on user retention early.
2️⃣ Make AI an intuitive interface layer, not a gimmick.
3. Keep personal knowledge connected to execution.

What's your biggest bottleneck this week? Let's discuss below 👇

#FounderJourney #AIProductManagement #BuildingInPublic #JustorAI"""


if __name__ == "__main__":
    mcp.run()
