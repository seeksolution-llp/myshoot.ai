import os
import shutil
import json
import cv2
from datetime import datetime, timezone
from fastapi import BackgroundTasks, HTTPException, UploadFile
from app.face_data.models import FaceData
from app.media.models import Media
from app.media.services import process_face_matching_async
from app.user.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from insightface.app import FaceAnalysis

# Initialize Model globally
face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_size=(640, 640))

async def upload_user_selfie(session: AsyncSession, user_id: str, image: UploadFile, background_tasks: BackgroundTasks):
    # 1. Existing user verification and upload logic
    user = (await session.scalars(select(User).where(User.user_id == user_id))).first()
    if not user: 
        raise HTTPException(status_code=404, detail="User target context profile not found")
        
    upload_dir = "static/uploads/selfies"
    os.makedirs(upload_dir, exist_ok=True)
    path = f"{upload_dir}/{user_id}_{image.filename}"
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    img = cv2.imread(path)
    faces = face_app.get(img)
    
    if not faces:
        os.remove(path)
        raise HTTPException(status_code=400, detail="No face detected. Please upload a clear photo.")
    if len(faces) > 1:
        os.remove(path)
        raise HTTPException(status_code=400, detail="Multiple faces detected. Upload a photo with only one face.")
        
    embedding_json = json.dumps(faces[0].embedding.flatten().tolist())
    
    face_record = FaceData(
        user_id=user_id,
        face_embedding=embedding_json,
        uploaded_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )
    
    session.add(face_record)
    await session.commit()
    await session.refresh(face_record)

    # --- NEW: TRIGGER MATCHING AGAINST EXISTING EVENT MEDIA ---
    # Fetch all media for the event associated with this user
    media_stmt = select(Media).where(Media.event_id == user.event_id).where(Media.type == "image")
    existing_media = (await session.scalars(media_stmt)).all()

    if existing_media:
        # Prepare the payload in the format your matching engine expects
        payload = [{"media_id": m.media_id, "url": m.url} for m in existing_media]
        
        # Add to background tasks so it doesn't block the user's response
        background_tasks.add_task(process_face_matching_async, user.event_id, payload)
    
    return face_record

async def get_face_data_by_user(session: AsyncSession, user_id: str):
    stmt = select(FaceData).where(FaceData.user_id == user_id)
    records = await session.scalars(stmt)
    return records.all()