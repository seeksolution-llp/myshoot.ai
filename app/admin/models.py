from __future__ import annotations
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.db.config import Base

if TYPE_CHECKING:
    from app.auth.models import RefreshToken

def generate_uuid():
    return str(uuid.uuid4())

class Admin(Base):
    __tablename__ = "admins"

    admin_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="admin", cascade="all, delete-orphan")
