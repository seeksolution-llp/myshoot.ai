from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class AdminOut(BaseModel):
    admin_id: str
    name: str
    email: EmailStr
    
    model_config = {
        "from_attributes": True
    }

class AdminAnalyticsOut(BaseModel):
    total_studios: int
    total_events: int
    total_media: int
    total_storage_used_bytes: int


class AdminStudioUpdateIn(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    plan_type: Optional[str] = None