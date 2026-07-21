import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Float
from app.db.config import Base
from app.face_data.models import FaceData
from app.media.models import Media



def generate_uuid():
    return str(uuid.uuid4())

class MatchResult(Base):
    __tablename__ = "match_results"

    match_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    face_id: Mapped[str] = mapped_column(String(36), ForeignKey("face_data.face_id", ondelete="CASCADE"), nullable=False)
    media_id: Mapped[str] = mapped_column(String(36), ForeignKey("media.media_id", ondelete="CASCADE"), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    face: Mapped["FaceData"] = relationship(back_populates="match_results")
    media: Mapped["Media"] = relationship(back_populates="match_results")
