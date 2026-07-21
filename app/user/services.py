from fastapi import HTTPException
from app.user.models import User
from app.event.models import Event
from app.user.schemas import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def register_user_to_event(session: AsyncSession, data: UserCreate):
    # Fix 1: Use session.scalar() directly for a single item lookup
    event_stmt = select(Event).where(Event.event_id == data.event_id)
    event_exists = await session.scalar(event_stmt)
    if not event_exists:
        raise HTTPException(status_code=404, detail="Invalid event QR code context")
        
    # Fix 2: Extract the scalar directly to a variable to prevent iterator exhaustion
    user_stmt = select(User).where(User.email == data.email, User.event_id == data.event_id)
    user_exists = await session.scalar(user_stmt)
    if user_exists:
        raise HTTPException(status_code=400, detail="You are already registered for this event")
    
    user = User(
        event_id=data.event_id,
        name=data.name,
        email=data.email,
        phone=data.phone
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_all_users(session: AsyncSession):
    # Fix 3: Call .all() on the scalar collection output directly
    result = await session.scalars(select(User))
    return result.all()

async def get_users_by_event(session: AsyncSession, event_id: str):
    stmt = select(User).where(User.event_id == event_id)
    result = await session.scalars(stmt)
    return result.all()

async def get_user_by_id(session: AsyncSession, user_id: str):
    # Fix 4: Convert to session.scalar() for simple single-row lookups by ID
    stmt = select(User).where(User.user_id == user_id)
    user = await session.scalar(stmt)
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user
