from fastapi import APIRouter, BackgroundTasks, status, UploadFile, File
from app.db.config import SessionDep
from app.face_data.schemas import FaceDataOut
from app.face_data.services import upload_user_selfie, get_face_data_by_user
from typing import List

router = APIRouter()

@router.post("/upload-selfie/{user_id}", response_model=FaceDataOut, status_code=status.HTTP_201_CREATED)
async def upload_selfie(
    user_id: str, 
    session: SessionDep, 
    image: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()  # Add this dependency
):
    # Pass background_tasks to your service function
    return await upload_user_selfie(session, user_id, image, background_tasks)

@router.get("/user/{user_id}", response_model=List[FaceDataOut])
async def read_user_face_records(user_id: str, session: SessionDep):
    return await get_face_data_by_user(session, user_id)
