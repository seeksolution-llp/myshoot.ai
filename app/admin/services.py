import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.admin.models import Admin
from app.studios.models import Studio
from app.event.models import Event
from app.media.models import Media
from app.admin.schemas import AdminCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.utils import SecurityHelper, SECRET_KEY, ALGORITHM

async def create_admin(session: AsyncSession, data: AdminCreate):
    stmt = select(Admin).where(Admin.email == data.email)
    result = await session.scalars(stmt)
    if result.first():
        raise HTTPException(status_code=400, detail="Email already exist")
        
    hashed_password = SecurityHelper.hash_password(data.password)
    
    admin = Admin(
        name=data.name,
        email=data.email,
        password=hashed_password
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin

async def get_all_admins(session: AsyncSession):
    admins = await session.scalars(select(Admin))
    return admins.all()

async def get_admin_by_id(session: AsyncSession, admin_id: str):
    stmt = select(Admin).where(Admin.admin_id == admin_id)
    result = await session.scalars(stmt)
    admin = result.first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

async def get_admin_by_email(session: AsyncSession, email: str):
    stmt = select(Admin).where(Admin.email == email)
    result = await session.scalars(stmt)
    return result.first()

async def admin_view_studios(session: AsyncSession):
    """Maps to viewStudios() in the Class Diagram"""
    studios = await session.scalars(select(Studio))
    return studios.all()

async def admin_view_analytics(session: AsyncSession):
    """Maps directly to viewAnalytics() in your core design spec blueprint."""
    studios_count = await session.scalar(select(func.count(Studio.studio_id))) or 0
    events_count = await session.scalar(select(func.count(Event.event_id))) or 0
    media_count = await session.scalar(select(func.count(Media.media_id))) or 0
    
    # Safely fall back to 0 if the query evaluates to None
    storage_sum = await session.scalar(select(func.sum(Studio.storage_used))) or 0
    
    return {
        "total_studios": studios_count,
        "total_events": events_count,
        "total_media": media_count,
        "total_storage_used_bytes": int(storage_sum)
    }


from app.auth.schemas import ChangePasswordIn, AdminUpdateIn, ResetPasswordIn

async def update_admin_profile(session: AsyncSession, admin_id: str, data: AdminUpdateIn):
    stmt = select(Admin).where(Admin.admin_id == admin_id)
    admin = (await session.scalars(stmt)).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if admin.email != data.email:
        email_check = select(Admin).where(Admin.email == data.email)
        if (await session.scalars(email_check)).first():
            raise HTTPException(status_code=400, detail="Email already in use")
            
    admin.name = data.name
    admin.email = data.email
    await session.commit()
    await session.refresh(admin)
    return admin

async def change_admin_password(session: AsyncSession, admin_id: str, data: ChangePasswordIn):
    stmt = select(Admin).where(Admin.admin_id == admin_id)
    admin = (await session.scalars(stmt)).first()
    if not admin or not SecurityHelper.verify_password(data.old_password, admin.password):
        raise HTTPException(status_code=400, detail="Invalid old password")
        
    admin.password = SecurityHelper.hash_password(data.new_password)
    await session.commit()
    return {"message": "Password changed successfully"}

async def process_admin_forgot_password(session: AsyncSession, email: str):
    stmt = select(Admin).where(Admin.email == email)
    admin = (await session.scalars(stmt)).first()
    if not admin:
        return {"message": "If the email exists, a reset link has been generated"}
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    reset_payload = {"sub": admin.admin_id, "purpose": "password_reset", "exp": expire}
    jwt_reset_token = jwt.encode(reset_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"[MAILER ENGINE] Admin JWT Reset Token: {jwt_reset_token}")
    return {"message": "If the email exists, a reset link has been generated", "test_token_preview": jwt_reset_token}

async def process_admin_reset_password(session: AsyncSession, data: ResetPasswordIn):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token context")
        admin_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="The reset link has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    stmt = select(Admin).where(Admin.admin_id == admin_id)
    admin = (await session.scalars(stmt)).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin account not found")
        
    admin.password = SecurityHelper.hash_password(data.new_password)
    await session.commit()
    return {"message": "Password has been reset successfully"}


async def admin_modify_studio(session: AsyncSession, studio_id: str, data: dict):
    """
    Allows an authenticated administrator to override and update 
    any studio's details (e.g., changing their subscription plan type).
    """
    stmt = select(Studio).where(Studio.studio_id == studio_id)
    result = await session.scalars(stmt)
    studio = result.first()
    
    if not studio:
        raise HTTPException(status_code=404, detail="Studio account not found")
        
    # Dynamically update only the fields provided in the request
    for key, value in data.items():
        if value is not None and hasattr(studio, key):
            setattr(studio, key, value)
            
    await session.commit()
    await session.refresh(studio)
    return studio

async def admin_remove_studio(session: AsyncSession, studio_id: str):
    """
    Completely deletes a studio account from the database.
    Due to ondelete="CASCADE" relationships, this automatically wipes 
    all linked events, media, and match results to prevent orphan data records.
    """
    stmt = select(Studio).where(Studio.studio_id == studio_id)
    result = await session.scalars(stmt)
    studio = result.first()
    
    if not studio:
        raise HTTPException(status_code=404, detail="Studio account not found")
        
    await session.delete(studio)
    await session.commit()
    return {"status": "success", "message": f"Studio '{studio.name}' and all its associated data have been permanently deleted."}