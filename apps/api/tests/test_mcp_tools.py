import uuid

import pytest
import pytest_asyncio

from app.mcp.tools import MCPDomainTools
from app.models.entities import Profile, Project, Task


@pytest_asyncio.fixture
async def setup_mcp_test_env(prepare_database, test_user_id: str):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        profile = Profile(id=test_user_id, email="taj@founder.local", settings={})
        session.add(profile)
        await session.flush()

        proj = Project(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            name="AI Expansion Engine",
            status="in_progress",
        )
        task = Task(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            title="Implement RLS safety checks",
            status="pending",
            priority="high",
        )
        session.add(proj)
        session.add(task)
        await session.commit()
        return {"user_id": test_user_id, "proj_id": proj.id, "task_id": task.id}


@pytest.mark.asyncio
async def test_all_mcp_domain_tools(setup_mcp_test_env):
    from tests.conftest import TestingSessionLocal

    user_id = setup_mcp_test_env["user_id"]

    async with TestingSessionLocal() as session:
        tools = MCPDomainTools(db=session, user_id=user_id)

        # 1. Exploratory Read Tools
        people = await tools.search_people(query="Taj")
        assert isinstance(people, list)

        memories = await tools.search_memory(query="AI")
        assert isinstance(memories, list)

        projects = await tools.get_projects(status="in_progress")
        assert isinstance(projects, list)
        assert len(projects) >= 1
        assert "source_grounding" in projects[0]
        assert projects[0]["source_grounding"]["citation_uri"].startswith("mcp://projects/")

        tasks = await tools.get_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1

        cal = await tools.get_calendar()
        assert isinstance(cal, list)

        rel = await tools.get_relationship_history(person_id=str(uuid.uuid4()))
        assert isinstance(rel, list)

        # 2. Generative Content Drafting Tools
        li_draft = await tools.generate_linkedin_post(topic="AI Expansion Engine")
        assert li_draft["status"] == "draft"
        assert "Draft Mode" in li_draft["notice"] or "human review" in li_draft["notice"]

        cs_draft = await tools.generate_case_study(project_name="AI Expansion Engine")
        assert cs_draft["status"] == "evidence_outline"
        assert cs_draft["project_name"] == "AI Expansion Engine"

        rev_draft = await tools.generate_weekly_review()
        assert rev_draft["status"] == "generated"
