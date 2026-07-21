from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    event_id: str
    name: str
    email: EmailStr
    phone: str

class UserOut(BaseModel):
    user_id: str
    event_id: str
    name: str
    email: EmailStr
    phone: str
    
    model_config = {
        "from_attributes": True
    }
