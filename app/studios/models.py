from __future__ import annotations
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from app.db.config import Base

if TYPE_CHECKING:
    from app.auth.models import RefreshToken
    from app.event.models import Event

def generate_uuid():
    return str(uuid.uuid4())

class Studio(Base):
    __tablename__ = "studios"

    studio_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    events: Mapped[List["Event"]] = relationship(back_populates="studio", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="studio", cascade="all, delete-orphan")
