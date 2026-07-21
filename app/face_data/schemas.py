from pydantic import BaseModel

class FaceDataCreate(BaseModel):
    user_id: str
    face_embedding: str  # Can accept a JSON-string array representation
    uploaded_at: str

class FaceDataOut(BaseModel):
    face_id: str
    user_id: str
    face_embedding: str
    uploaded_at: str
    
    """User functional transaction step: uploadSelfie()"""
    model_config = {
        "from_attributes": True
    }
