import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, String, ForeignKey, Text
from app.db.config import Base

# Fix 1: Isolates imports inside TYPE_CHECKING to break the runtime cycle
if TYPE_CHECKING:
    from app.event.models import Event
    from app.match_result.models import MatchResult


def generate_uuid():
    return str(uuid.uuid4())


class Media(Base):
    __tablename__ = "media"

    media_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_at: Mapped[str] = mapped_column(String(50), nullable=False)

# AI Metadata Fields
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    caption: Mapped[str] = mapped_column(Text, nullable=True)
    clip_embedding: Mapped[str] = mapped_column(Text, nullable=True)
    # Relationships (Fix 2: Added explicit string targets "Event" and "MatchResult")
    event: Mapped["Event"] = relationship("Event", back_populates="media")
    match_results: Mapped[List["MatchResult"]] = relationship("MatchResult", back_populates="media", cascade="all, delete-orphan")
