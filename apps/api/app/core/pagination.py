from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Number of items per page"
    )
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    sort_by: Optional[str] = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


@dataclass
class PaginatedResult(Generic[T]):
    """
    Internal pagination result container for repository and domain service layers.
    Decoupled from Pydantic schema generation so SQLAlchemy ORM models can be
    safely contained without triggering PydanticSchemaGenerationError.
    """

    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def create(cls, items: List[T], total: int, limit: int, offset: int) -> "PaginatedResult[T]":
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "total": self.total,
            "limit": self.limit,
            "offset": self.offset,
            "has_more": self.has_more,
        }

    def dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Pydantic response schema for FastAPI public HTTP endpoint serialization.
    Used exclusively with Pydantic DTO models (e.g. MemoryResponse, IdeaResponse).
    """

    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(cls, items: List[T], total: int, limit: int, offset: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )


def validate_sort_field(sort_by: str, allowlist: List[str]) -> str:
    """Validate requested sort column against table allowlists to prevent arbitrary SQL injection or errors."""
    if sort_by not in allowlist:
        return allowlist[0] if allowlist else "created_at"
    return sort_by
