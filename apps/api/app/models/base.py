import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import CHAR, DATE, INTEGER, JSON, TEXT, TypeDecorator


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


class PGEnum(TypeDecorator):
    """Use an enum owned by migrations on PostgreSQL and text in SQLite tests."""

    impl = TEXT
    cache_ok = True

    def __init__(self, name: str, aliases: dict[str, str] | None = None):
        super().__init__()
        self.name = name
        self.aliases = tuple(sorted((aliases or {}).items()))
        self._alias_map = dict(self.aliases)
        self._reverse_aliases = {value: key for key, value in self.aliases}

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            # PG_ENUM MUST be given the enum's values. Without them SQLAlchemy's
            # result processor has an empty lookup table and every READ of this
            # column raises LookupError, even though writes succeed.
            from app.models.enums import ENUM_VALUES

            values = ENUM_VALUES.get(self.name)
            if not values:
                raise KeyError(
                    f"Unknown enum {self.name!r}. Add it to app/models/enums.py "
                    "so it matches the canonical migrations."
                )
            return dialect.type_descriptor(
                PG_ENUM(*values, name=self.name, create_type=False)
            )
        return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value, dialect):
        return self._alias_map.get(value, value)

    def process_result_value(self, value, dialect):
        return self._reverse_aliases.get(value, value)


class DateOnly(TypeDecorator):
    """Canonical PostgreSQL DATE that accepts API datetimes at the boundary."""

    impl = DATE
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DATE())

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            return value.date()
        return value


class PriorityInteger(TypeDecorator):
    """Keep the public priority labels while storing canonical integer priorities."""

    impl = INTEGER
    cache_ok = True
    _DEFAULT_TO_INT = {"low": 1, "medium": 3, "high": 4, "urgent": 5}

    def __init__(self, mapping: dict[str, int] | None = None):
        super().__init__()
        self._to_int = tuple(sorted((mapping or self._DEFAULT_TO_INT).items()))
        self._to_int_map = dict(self._to_int)
        self._to_label = {value: key for key, value in self._to_int}

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            return self._to_int_map.get(value.lower(), value)
        return value

    def process_result_value(self, value, dialect):
        return self._to_label.get(value, value)


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
