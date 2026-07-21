import os
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select # 1. Added BackgroundTasks import
from app.db.config import SessionDep
from app.media.models import Media
from app.media.schemas import MediaOut
from app.media.services import upload_bulk_event_media, get_media_by_event
from app.dependencies import get_current_studio_id
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File
from app.db.config import SessionDep
from app.dependencies import get_current_studio_id # <-- ENSURE STUDIO DEPENDENCY

router = APIRouter()



@router.post("/upload/{event_id}")
async def studio_upload_media(
    event_id: str, 
    session: SessionDep, 
    background_tasks: BackgroundTasks, 
    files: list[UploadFile] = File(...),
    current_studio_id: str = Depends(get_current_studio_id) # <-- MUST BE STUDIO GUARD
):
    return await upload_bulk_event_media(session, event_id, files, background_tasks)


@router.get("/event/{event_id}", response_model=List[MediaOut])
async def read_event_gallery(event_id: str, session: SessionDep):
    return await get_media_by_event(session, event_id)



@router.get("/download/{media_id}")
async def download_user_matched_image(media_id: str, session: SessionDep):
    stmt = select(Media).where(Media.media_id == media_id)
    result = await session.scalars(stmt)
    media_record = result.first()
    
    if not media_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The requested image could not be found in our database records."
        )
        
    # FIX: Extract the relative path if the DB URL is stored as a full HTTP URL string
    db_url_string = media_record.url
    if "http://" in db_url_string or "https://" in db_url_string:
        # Splits by your port and isolates 'static/uploads/event_media/photo.jpg'
        local_file_path = db_url_string.split(":8000/")[-1]
    else:
        local_file_path = db_url_string
    
    # Check if the file physically exists inside your laptop's local directory path
    if not os.path.exists(local_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"The physical image file is missing from local path: {local_file_path}"
        )
        
    original_filename = os.path.basename(local_file_path)
    
    return FileResponse(
        path=local_file_path, 
        media_type="application/octet-stream", 
        filename=original_filename
    )
