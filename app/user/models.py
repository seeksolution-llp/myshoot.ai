import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from app.db.config import Base
from datetime import datetime, timezone

# Fix 1: Stops Python from executing these imports at runtime to break the loop
if TYPE_CHECKING:
    from app.event.models import Event
    from app.media.models import FaceData


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships (Target classes passed as explicit string literals)
    event: Mapped["Event"] = relationship("Event", back_populates="users")
    face_data: Mapped[List["FaceData"]] = relationship("FaceData", back_populates="user", cascade="all, delete-orphan")
   