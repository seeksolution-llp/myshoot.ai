from typing import Optional

from pydantic import BaseModel

class MediaCreate(BaseModel):
    event_id: str
    url: str
    type: str
    uploaded_at: str

class MediaOut(BaseModel):
    media_id: str
    event_id: str
    url: str
    type: str
    uploaded_at: str
    # New AI Metadata fields
    quality_score: Optional[float] = None
    caption: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }
