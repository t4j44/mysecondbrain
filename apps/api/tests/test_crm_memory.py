import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.errors import ConflictError, NotFoundError
from app.models.base import Base
from app.repositories.crm import CRMRepository
from app.repositories.interactions import InteractionsRepository
from app.repositories.meetings import MeetingsRepository
from app.repositories.memories import MemoriesRepository
from app.schemas.crm import OrganizationCreate, PersonCreate
from app.schemas.interactions import InteractionCreate
from app.schemas.meetings import MeetingCreate
from app.schemas.memories import MemoryCreate


@pytest_asyncio.fixture(scope="function")
async def test_db():
    # Set up in-memory sqlite for test database isolation
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_crm_organization_crud(test_db):
    user_1 = uuid.uuid4()
    user_2 = uuid.uuid4()

    # 1. Create Organization
    org_schema = OrganizationCreate(
        name="Mangosteen Studio", domain="mangosteen.cc", industry="SaaS", location="Dhaka"
    )
    db_org = await CRMRepository.create_organization(test_db, user_1, org_schema)
    assert db_org.name == "Mangosteen Studio"
    assert db_org.user_id == user_1

    # 2. Prevent duplicate names under same user
    with pytest.raises(ConflictError):
        await CRMRepository.create_organization(test_db, user_1, org_schema)

    # 3. Allow duplicate names across different users
    db_org_2 = await CRMRepository.create_organization(test_db, user_2, org_schema)
    assert db_org_2.user_id == user_2

    # 4. Fetch Organization
    fetched = await CRMRepository.get_organization(test_db, user_1, db_org.id)
    assert fetched.name == "Mangosteen Studio"

    # 5. Prevent cross-user access (Security check)
    with pytest.raises(NotFoundError):
        await CRMRepository.get_organization(test_db, user_2, db_org.id)


@pytest.mark.asyncio
async def test_crm_person_crud(test_db):
    user_id = uuid.uuid4()

    # 1. Create Person
    p_schema = PersonCreate(
        name="Yousuf Imran",
        role="CEO",
        company="Mangosteen Studio",
        relationship_type="mentor",
        tags=["LegalTech", "SaaS"],
    )
    person = await CRMRepository.create_person(test_db, user_id, p_schema)
    assert person.name == "Yousuf Imran"
    assert person.user_id == user_id
    assert "LegalTech" in person.tags

    # 2. List People with filters
    list_all, total = await CRMRepository.list_people(test_db, user_id)
    assert total == 1
    assert list_all[0].name == "Yousuf Imran"

    # Check tag filtering
    list_tagged, _ = await CRMRepository.list_people(test_db, user_id, tag="LegalTech")
    assert len(list_tagged) == 1

    list_missing, _ = await CRMRepository.list_people(test_db, user_id, tag="NonExistent")
    assert len(list_missing) == 0


@pytest.mark.asyncio
async def test_interaction_timeline(test_db):
    user_id = uuid.uuid4()

    # Create contact
    p_schema = PersonCreate(name="Yousuf Imran", relationship_type="mentor")
    person = await CRMRepository.create_person(test_db, user_id, p_schema)

    # Create Interaction
    int_schema = InteractionCreate(
        title="Coffee Chat Dhaka",
        person_id=person.id,
        interaction_type="meeting",
        summary="Discussed product retention model.",
        key_takeaways=["Scoping MVP is critical", "Identify core bottlenecks"],
        next_actions=["Draft product case study"],
    )
    db_int = await InteractionsRepository.create_interaction(test_db, user_id, int_schema)
    assert db_int.title == "Coffee Chat Dhaka"
    assert db_int.person_id == person.id

    # List chronological interactions
    ints, total = await InteractionsRepository.list_interactions(
        test_db, user_id, person_id=person.id
    )
    assert total == 1
    assert ints[0].title == "Coffee Chat Dhaka"


@pytest.mark.asyncio
async def test_meetings_and_participants(test_db):
    user_id = uuid.uuid4()

    # Create contact
    p_schema = PersonCreate(name="Yousuf Imran", relationship_type="mentor")
    person = await CRMRepository.create_person(test_db, user_id, p_schema)

    # Create Meeting
    meet_schema = MeetingCreate(
        title="Justor AI Validation Sync",
        meeting_date=datetime.utcnow(),
        duration_minutes=45,
        location="Google Meet",
        participant_person_ids=[person.id],
        action_items=["Complete legal audit"],
    )
    meeting = await MeetingsRepository.create_meeting(test_db, user_id, meet_schema)
    assert meeting.title == "Justor AI Validation Sync"

    # Check participant linked
    fetched = await MeetingsRepository.get_meeting(test_db, user_id, meeting.id)
    assert len(fetched.participants) == 1
    assert fetched.participants[0].person_id == person.id


@pytest.mark.asyncio
async def test_memories_indexing(test_db):
    user_id = uuid.uuid4()

    # Create Memory
    mem_schema = MemoryCreate(
        title="Scaling bottleneck lesson",
        content="Premature optimization is indeed the root of all evil.",
        category="lesson",
        tags=["optimization", "development"],
    )
    memory = await MemoriesRepository.create_memory(test_db, user_id, mem_schema)
    assert memory.title == "Scaling bottleneck lesson"
    assert "optimization" in memory.tags

    # Fetch memory list
    mems, total = await MemoriesRepository.list_memories(test_db, user_id, tag="optimization")
    assert total == 1
    assert mems[0].title == "Scaling bottleneck lesson"
