"""Regression: every list endpoint must serialize, not 500.

`PaginatedResult.model_dump()` used to hand raw SQLAlchemy instances to the JSON
encoder. Endpoints declare `response_model=dict`, so FastAPI could not shape them
and every list endpoint answered 500 with
`PydanticSerializationError: Unable to serialize unknown type`.

Single-item endpoints were unaffected because they declare a real response_model,
which is exactly why the existing suite stayed green while the Ventures, Projects,
Tasks and People pages were all broken.
"""

import json

from app.core.pagination import PaginatedResult
from app.models.entities import Venture


def _venture(**kw):
    defaults = dict(
        id="11111111-1111-4111-8111-111111111111",
        user_id="22222222-2222-4222-8222-222222222222",
        name="Justor AI",
        slug="justor-ai",
        status="active",
    )
    defaults.update(kw)
    return Venture(**defaults)


def test_paginated_result_of_orm_objects_is_json_serializable():
    page = PaginatedResult.create(items=[_venture()], total=1, limit=20, offset=0)
    dumped = page.model_dump()
    json.dumps(dumped)  # would raise TypeError before the fix


def test_serialized_items_are_plain_dicts_with_the_mapped_field_names():
    page = PaginatedResult.create(items=[_venture()], total=1, limit=20, offset=0)
    item = page.model_dump()["items"][0]
    assert isinstance(item, dict)
    assert item["name"] == "Justor AI"
    assert item["slug"] == "justor-ai"
    assert item["status"] == "active"


def test_soft_delete_column_is_not_exposed_in_list_payloads():
    page = PaginatedResult.create(items=[_venture()], total=1, limit=20, offset=0)
    assert "deleted_at" not in page.model_dump()["items"][0]


def test_pagination_envelope_is_preserved():
    page = PaginatedResult.create(items=[_venture(), _venture()], total=5, limit=2, offset=0)
    dumped = page.model_dump()
    assert dumped["total"] == 5
    assert dumped["limit"] == 2
    assert dumped["offset"] == 0
    assert dumped["has_more"] is True
    assert len(dumped["items"]) == 2


def test_non_orm_items_pass_through_untouched():
    page = PaginatedResult.create(items=[{"a": 1}, "x", 3], total=3, limit=20, offset=0)
    assert page.model_dump()["items"] == [{"a": 1}, "x", 3]
