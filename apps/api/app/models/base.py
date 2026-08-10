import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import CHAR, JSON, TEXT, TypeDecorator


class Base(DeclarativeBase):
    id: Any
    user_id: Any
    deleted_at: Any
    archived_at: Any
    status: Any
    created_at: Any
    updated_at: Any


class UUIDString(str):
    """String-compatible UUID value that also compares cleanly with UUID objects."""

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return str(self) == str(other)
        return super().__eq__(other)

    __hash__ = str.__hash__


class FlexibleUUID(TypeDecorator):
    """UUID storage that accepts strings or UUID objects and returns UUID objects.

    Supabase uses native PostgreSQL UUID columns, while the local fallback uses
    SQLite. This adapter keeps both modes consistent without making callers
    special-case the active database.
    """

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(parsed)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return UUIDString(str(value))


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


class SafeArray(TypeDecorator):
    """
    Dialect-agnostic Array column type.
    Uses PostgreSQL native ARRAY in production, and maps to JSON in SQLite tests.
    """

    impl = TEXT
    cache_ok = True

    def __init__(self, item_type):
        super().__init__()
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return value


class MetadataDescriptor:
    """
    SQLAlchemy 2.0 helper descriptor.
    Bypasses naming conflict with standard SQLAlchemy declarative class metadata.
    Returns Base.metadata on class access, and self.meta on instance access.
    """

    def __get__(self, instance, owner):
        if instance is None:
            return Base.metadata
        return instance.meta

    def __set__(self, instance, value):
        instance.meta = value
