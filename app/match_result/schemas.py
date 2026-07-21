from pydantic import BaseModel, Field

class MatchResultCreate(BaseModel):
    face_id: str
    media_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class MatchResultOut(BaseModel):
    match_id: str
    face_id: str
    media_id: str
    confidence_score: float
    
    model_config = {
        "from_attributes": True
    }
