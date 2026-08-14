import importlib
import typing
from dataclasses import is_dataclass
from datetime import datetime, timezone

from app.core.pagination import PaginatedResponse, PaginatedResult
from app.repositories.base import BaseRepository
from app.schemas.founder import VentureResponse
from app.services.founder import (
    KPIService,
    ProjectService,
    ReviewService,
    TaskService,
    VentureService,
)
from app.services.integrations import (
    AuditService,
    ExportService,
    IntegrationManagementService,
)
from app.services.knowledge import (
    AchievementService,
    ContentService,
    DecisionService,
    DocumentService,
    IdeaService,
    MemoryService,
    PortfolioService,
)
from app.services.network import (
    InteractionService,
    MeetingService,
    OrganizationService,
    PersonService,
)


def test_production_app_import_and_openapi_generation() -> None:
    """Regression test ensuring production FastAPI application imports cleanly and generates OpenAPI schema without PydanticSchemaGenerationError."""
    main_module = importlib.import_module("app.main")
    app = main_module.app
    assert app is not None

    # Generate OpenAPI schema - triggers complete Pydantic core schema generation for all routes & models
    openapi_schema = app.openapi()
    assert isinstance(openapi_schema, dict)
    assert "paths" in openapi_schema
    assert "components" in openapi_schema


def test_all_repository_and_service_type_hints_evaluate_cleanly() -> None:
    """Verify that type annotations on all repositories and domain services evaluate cleanly without raising typing/Pydantic errors."""
    services = [
        BaseRepository,
        VentureService,
        ProjectService,
        TaskService,
        KPIService,
        ReviewService,
        IntegrationManagementService,
        ExportService,
        AuditService,
        MemoryService,
        IdeaService,
        DecisionService,
        DocumentService,
        AchievementService,
        PortfolioService,
        ContentService,
        PersonService,
        OrganizationService,
        InteractionService,
        MeetingService,
    ]

    for svc_class in services:
        for attr_name, attr_val in svc_class.__dict__.items():
            if callable(attr_val) and not attr_name.startswith("__"):
                hints = typing.get_type_hints(attr_val)
                assert isinstance(hints, dict), f"Failed to get type hints for {svc_class.__name__}.{attr_name}"


def test_paginated_result_contract_and_methods() -> None:
    """Verify PaginatedResult fulfills the internal pagination contract and provides dict-compatible access."""
    dummy_items = [{"id": "item_1", "name": "first"}, {"id": "item_2", "name": "second"}]
    res = PaginatedResult.create(items=dummy_items, total=5, limit=2, offset=0)

    assert is_dataclass(res)
    assert res.items == dummy_items
    assert res.total == 5
    assert res.limit == 2
    assert res.offset == 0
    assert res.has_more is True

    # Dict-like access
    assert res["items"] == dummy_items
    assert res.get("total") == 5
    assert res.get("non_existent", "default") == "default"

    # Serialization methods
    dumped = res.model_dump()
    assert dumped == {
        "items": dummy_items,
        "total": 5,
        "limit": 2,
        "offset": 0,
        "has_more": True,
    }
    assert res.dict() == dumped


def test_paginated_result_has_more_boundary_calculation() -> None:
    """Verify has_more flag computation under various limit/offset combinations."""
    # Last page exactly matching total
    res1 = PaginatedResult.create(items=[1, 2], total=4, limit=2, offset=2)
    assert res1.has_more is False

    # Empty result
    res2 = PaginatedResult.create(items=[], total=0, limit=20, offset=0)
    assert res2.has_more is False

    # More items remaining
    res3 = PaginatedResult.create(items=[1], total=10, limit=1, offset=0)
    assert res3.has_more is True


def test_paginated_response_pydantic_serialization_from_orm_dto() -> None:
    """Verify PaginatedResponse[DTO] serializes PaginatedResult containing DTO-compatible objects."""
    now = datetime.now(timezone.utc)

    class MockVenture:
        def __init__(self, id: str, name: str, slug: str, user_id: str):
            self.id = id
            self.name = name
            self.slug = slug
            self.user_id = user_id
            self.vision = "Test Vision"
            self.mission = None
            self.description = None
            self.status = "active"
            self.priority = "high"
            self.start_date = None
            self.target_date = None
            self.metadata_payload = {}
            self.created_at = now
            self.updated_at = now
            self.archived_at = None

    mock_venture = MockVenture("v_100", "AI Stealth", "ai-stealth", "usr_999")
    paginated_result = PaginatedResult.create(items=[mock_venture], total=1, limit=20, offset=0)

    # Validate against Pydantic schema
    response_dto = PaginatedResponse[VentureResponse].model_validate(paginated_result)
    assert response_dto.total == 1
    assert response_dto.limit == 20
    assert response_dto.offset == 0
    assert response_dto.has_more is False
    assert len(response_dto.items) == 1
    assert response_dto.items[0].id == "v_100"
    assert response_dto.items[0].name == "AI Stealth"
    assert response_dto.items[0].slug == "ai-stealth"
