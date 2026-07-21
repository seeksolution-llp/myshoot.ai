from fastapi import APIRouter, status, Depends
from app.db.config import SessionDep
from app.event.schemas import EventCreate, EventOut
from app.event.services import create_event, get_studio_events, get_event_by_id
from app.dependencies import get_current_studio_id 
from typing import List

router = APIRouter()

@router.post("/register", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def register_event(
    data: EventCreate, 
    session: SessionDep,
    current_studio_id: str = Depends(get_current_studio_id) 
):
    """Studio operational method: createEvent() and generateQR()"""
    return await create_event(session, data, current_studio_id)

@router.get("/my-events", response_model=List[EventOut])
async def read_my_studio_events(
    session: SessionDep, 
    current_studio_id: str = Depends(get_current_studio_id)
):
    """Allows a logged-in studio to view all its unique events."""
    return await get_studio_events(session, current_studio_id)

@router.get("/{event_id}", response_model=EventOut)
async def read_event_details(event_id: str, session: SessionDep):
    """Fetch individual event properties (accessible publicly for user scanning)"""
    return await get_event_by_id(session, event_id)
