import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey
from app.db.config import Base

# TYPE_CHECKING is True only for your IDE/linter, but False at runtime.
# This keeps your autocompletion working perfectly without causing import loops.
if TYPE_CHECKING:
    from app.user.models import User
    from app.media.models import Media
    from app.studios.models import Studio


def generate_uuid():
    return str(uuid.uuid4())

class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    studio_id: Mapped[str] = mapped_column(String(36), ForeignKey("studios.studio_id", ondelete="CASCADE"), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_date: Mapped[str] = mapped_column(String(50), nullable=False)
    event_time: Mapped[str] = mapped_column(String(50), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    qr_code: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships (Using string syntax for the targets avoids import errors)
    studio: Mapped["Studio"] = relationship("Studio", back_populates="events")
    users: Mapped[List["User"]] = relationship("User", back_populates="event", cascade="all, delete-orphan")
    media: Mapped[List["Media"]] = relationship("Media", back_populates="event", cascade="all, delete-orphan")
