from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from app.db.config import Base

# This code is ONLY executed by VS Code Pylance, eliminating yellow lines
if TYPE_CHECKING:
    from app.admin.models import Admin
    from app.studios.models import Studio

def generate_uuid():
    return str(uuid.uuid4())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    admin_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("admins.admin_id", ondelete="CASCADE"), nullable=True)
    studio_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("studios.studio_id", ondelete="CASCADE"), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False) 
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    admin: Mapped[Optional["Admin"]] = relationship(back_populates="refresh_tokens")
    studio: Mapped[Optional["Studio"]] = relationship(back_populates="refresh_tokens")
