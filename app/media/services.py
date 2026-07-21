import os
import shutil
import uuid
import cv2
import json
import numpy as np
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile, BackgroundTasks
from app.media.models import Media
from app.event.models import Event
from app.face_data.models import FaceData
from app.match_result.models import MatchResult
from app.db.config import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.studios.models import Studio
from decouple import config

# --- NEW: IMPORT INSIGHTFACE ---
from insightface.app import FaceAnalysis

# Global AI Model Initialization
face_app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_size=(640, 640))

BACKEND_URL = config("BACKEND_URL")

def get_absolute_file_url(relative_path: str) -> str:
    if not relative_path:
        return ""
    clean_path = relative_path.replace("\\", "/")
    return f"{BACKEND_URL}/{clean_path}"

def check_quality(img_path):
    """Checks image for blur, brightness, and resolution."""
    img = cv2.imread(img_path)
    if img is None: return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharp = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = np.mean(gray)
    h, w = img.shape[:2]
    return sharp >= 80 and 40 <= brightness <= 220 and h >= 200 and w >= 200

def calculate_photo_score(img_path):
    """Calculates a score for photo highlighting."""
    img = cv2.imread(img_path)
    if img is None: return 0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharp = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = np.mean(gray)
    faces = face_app.get(img)
    score = min(sharp/10, 25) + (25 if 80 < brightness < 180 else 0) + (25 if len(faces) > 0 else 0)
    return score

async def process_face_matching_async(event_id: str, new_media_records: list[dict]):
    print(f"DEBUG: Starting background match for {len(new_media_records)} images in event {event_id}")
    async with async_session() as session:
        face_query = select(FaceData).join(FaceData.user).where(FaceData.user.has(event_id=event_id))
        all_event_faces = (await session.scalars(face_query)).all()

        if not all_event_faces:
            print("DEBUG: No face records found for this event.")
            return 

        db_face_vectors = []
        for face in all_event_faces:
            db_emb = np.array(json.loads(face.face_embedding), dtype="float32")
            db_emb = db_emb / np.linalg.norm(db_emb)
            db_face_vectors.append({"face_id": face.face_id, "vector": db_emb})

        for media in new_media_records:
            full_path = os.path.abspath(media["url"])
            event_img = cv2.imread(full_path)
            
            if event_img is None:
                print(f"DEBUG: Could not load image at {full_path}")
                continue
            
            detected_faces = face_app.get(event_img)
            
            for face in detected_faces:
                emb = face.embedding.astype("float32")
                emb = emb / np.linalg.norm(emb)
                
                for db_face in db_face_vectors:
                    score = float(np.dot(emb, db_face["vector"]))
                    
                    if score >= 0.65: 
                        # NEW: Check if this match already exists to prevent duplicate SQL errors
                        existing_match = (await session.execute(
                            select(MatchResult).where(
                                MatchResult.face_id == db_face["face_id"],
                                MatchResult.media_id == media["media_id"]
                            )
                        )).scalar_one_or_none()
                        
                        if not existing_match:
                            print(f"DEBUG: Match found! Score: {score:.4f} for face {db_face['face_id']}")
                            match = MatchResult(
                                face_id=db_face["face_id"], 
                                media_id=media["media_id"], 
                                confidence_score=score
                            )
                            session.add(match)
                        else:
                            print(f"DEBUG: Match already exists for face {db_face['face_id']} in media {media['media_id']}")
        
        await session.commit()
        print("DEBUG: Background matching task committed to database.")
        
async def upload_bulk_event_media(session: AsyncSession, event_id: str, files: list[UploadFile], background_tasks: BackgroundTasks):
    event = (await session.scalars(select(Event).where(Event.event_id == event_id))).first()
    if not event: raise HTTPException(status_code=404, detail="Event not found")
        
    upload_dir = "static/uploads/event_media"
    os.makedirs(upload_dir, exist_ok=True)
    
    saved_records = []
    background_payload = []

    for file in files:
        file_type = "image" if file.content_type.startswith("image/") else "video"
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        saved_path = f"{upload_dir}/{unique_filename}"
        
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if file_type == "image" and not check_quality(saved_path):
            os.remove(saved_path)
            continue

        # --- FIX: Generate timestamp for this specific file ---
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        score = calculate_photo_score(saved_path) if file_type == "image" else 0
        
        # --- FIX: Pass the uploaded_at value here ---
        media_record = Media(
            event_id=event_id, 
            url=saved_path, 
            type=file_type, 
            quality_score=score,
            uploaded_at=timestamp_str 
        )
        session.add(media_record)
        saved_records.append(media_record)

    await session.flush()
    for record in saved_records:
        if record.type == "image":
            background_payload.append({"media_id": record.media_id, "url": record.url})

    await session.commit()
    if background_payload:
        background_tasks.add_task(process_face_matching_async, event_id, background_payload)
    return saved_records

async def get_media_by_event(session: AsyncSession, event_id: str):
    stmt = select(Media).where(Media.event_id == event_id)
    records = await session.scalars(stmt)
    return records.all()