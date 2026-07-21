from pydantic import BaseModel, EmailStr

class StudioCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    plan_type: str

class StudioOut(BaseModel):
    studio_id: str
    name: str
    email: EmailStr
    plan_type: str
    storage_used: int
    
    model_config = {
        "from_attributes": True
    }
