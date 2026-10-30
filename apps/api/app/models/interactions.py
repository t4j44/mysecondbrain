"""Canonical Interaction model plus its participant association.

`interactions.participants` never existed in the canonical schema: participation is a
link table, `public.interaction_participants` (migration 0005). The scalar array that
used to be mapped here is what made every real PostgreSQL insert of an interaction fail.
"""

from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, FlexibleUUID
from app.models.entities import Interaction, utc_now
from app.utils.identifiers import generate_uuid


class InteractionParticipant(Base):
    __tablename__ = "interaction_participants"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    interaction_id: Any = Column(
        FlexibleUUID, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Any = Column(
        FlexibleUUID, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


Interaction.participants = relationship(
    InteractionParticipant,
    lazy="selectin",
    cascade="all, delete-orphan",
    passive_deletes=True,
)


__all__ = ["Interaction", "InteractionParticipant"]
