import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text
from app.db.config import Base

# Fix 1: Isolates imports from the python runtime engine to break the cycle completely
if TYPE_CHECKING:
    from app.user.models import User
    from app.match_result.models import MatchResult


def generate_uuid():
    return str(uuid.uuid4())


class FaceData(Base):
    __tablename__ = "face_data"

    face_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    face_embedding: Mapped[str] = mapped_column(Text, nullable=False)  # Text representation of data array
    uploaded_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships (Target classes passed explicitly as string literals)
    user: Mapped["User"] = relationship("User", back_populates="face_data")
    
    # MatchResult uses "face" as the related attribute on its side.
    match_results: Mapped[List["MatchResult"]] = relationship("MatchResult", back_populates="face", cascade="all, delete-orphan")
