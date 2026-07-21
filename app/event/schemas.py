from pydantic import BaseModel

class EventCreate(BaseModel):
    event_name: str
    event_type: str
    event_date: str
    event_time: str
    owner_name: str

class EventOut(BaseModel):
    event_id: str
    studio_id: str
    event_name: str
    event_type: str
    event_date: str
    event_time: str
    owner_name: str
    qr_code: str
    
    model_config = {
        "from_attributes": True
    }
