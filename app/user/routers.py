from fastapi import APIRouter, status
from app.db.config import SessionDep
from app.user.schemas import UserCreate, UserOut
from app.user.services import register_user_to_event, get_all_users, get_users_by_event, get_user_by_id
from typing import List

router = APIRouter()

@router.post("/scan-and-register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def scan_qr_and_register(data: UserCreate, session: SessionDep):
    """User operational method: scanQR() and context registration"""
    return await register_user_to_event(session, data)

@router.get("/", response_model=List[UserOut])
async def read_all_users(session: SessionDep):
    return await get_all_users(session)

@router.get("/event/{event_id}", response_model=List[UserOut])
async def read_users_by_event(event_id: str, session: SessionDep):
    return await get_users_by_event(session, event_id)

@router.get("/{user_id}", response_model=UserOut)
async def read_user_profile(user_id: str, session: SessionDep):
    return await get_user_by_id(session, user_id)
