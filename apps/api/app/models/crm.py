"""CRM model compatibility exports.

Organization and Person are defined once in ``entities``. Relationship is kept
here because it has no competing canonical definition.
"""

from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.models.base import Base, FlexibleUUID
from app.models.entities import Organization, Person, utc_now
from app.utils.identifiers import generate_uuid


class Relationship(Base):
    __tablename__ = "relationships"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    source_person_id: Any = Column(
        FlexibleUUID, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    target_person_id: Any = Column(
        FlexibleUUID, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    relationship_nature: Any = Column(String(255), nullable=False)
    notes: Any = Column(Text, nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


__all__ = ["Organization", "Person", "Relationship"]
