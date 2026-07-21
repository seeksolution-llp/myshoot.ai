import jwt
from datetime import datetime, timedelta, timezone
from app.utils import SECRET_KEY, ALGORITHM
from fastapi import HTTPException
from app.studios.models import Studio
from app.studios.schemas import StudioCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils import SecurityHelper
from app.auth.schemas import ChangePasswordIn, StudioUpdateIn, ResetPasswordIn

async def create_studio(session: AsyncSession, data: StudioCreate):
    stmt = select(Studio).where(Studio.email == data.email)
    result = await session.scalars(stmt)
    if result.first():
        raise HTTPException(status_code=400, detail="Email already exist")
        
    hashed_password = SecurityHelper.hash_password(data.password)
    
    studio = Studio(
        name=data.name,
        email=data.email,
        password=hashed_password,
        plan_type=data.plan_type
    )
    session.add(studio)
    await session.commit()
    await session.refresh(studio)
    return studio

async def get_all_studios(session: AsyncSession):
    studios = await session.scalars(select(Studio))
    return studios.all()

async def get_studio_by_id(session: AsyncSession, studio_id: str):
    stmt = select(Studio).where(Studio.studio_id == studio_id)
    result = await session.scalars(stmt)
    studio = result.first()
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
    return studio

async def get_studio_by_email(session: AsyncSession, email: str):
    stmt = select(Studio).where(Studio.email == email)
    result = await session.scalars(stmt)
    return result.first()


async def update_studio_profile(session: AsyncSession, studio_id: str, data: StudioUpdateIn):
    stmt = select(Studio).where(Studio.studio_id == studio_id)
    studio = (await session.scalars(stmt)).first()
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
        
    if studio.email != data.email:
        email_check = select(Studio).where(Studio.email == data.email)
        if (await session.scalars(email_check)).first():
            raise HTTPException(status_code=400, detail="Email already in use")
            
    studio.name = data.name
    studio.email = data.email
    studio.plan_type = data.plan_type
    await session.commit()
    await session.refresh(studio)
    return studio

async def change_studio_password(session: AsyncSession, studio_id: str, data: ChangePasswordIn):
    stmt = select(Studio).where(Studio.studio_id == studio_id)
    studio = (await session.scalars(stmt)).first()
    if not studio or not SecurityHelper.verify_password(data.old_password, studio.password):
        raise HTTPException(status_code=400, detail="Invalid old password")
        
    studio.password = SecurityHelper.hash_password(data.new_password)
    await session.commit()
    return {"message": "Password changed successfully"}

async def process_studio_forgot_password(session: AsyncSession, email: str):
    stmt = select(Studio).where(Studio.email == email)
    studio = (await session.scalars(stmt)).first()
    if not studio:
        return {"message": "If the email exists, a reset link has been generated"}
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    reset_payload = {"sub": studio.studio_id, "purpose": "password_reset", "exp": expire}
    jwt_reset_token = jwt.encode(reset_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"[MAILER ENGINE] Studio JWT Reset Token: {jwt_reset_token}")
    return {"message": "If the email exists, a reset link has been generated", "test_token_preview": jwt_reset_token}

async def process_studio_reset_password(session: AsyncSession, data: ResetPasswordIn):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token context")
        studio_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="The reset link has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    stmt = select(Studio).where(Studio.studio_id == studio_id)
    studio = (await session.scalars(stmt)).first()
    if not studio:
        raise HTTPException(status_code=404, detail="Studio account not found")
        
    studio.password = SecurityHelper.hash_password(data.new_password)
    await session.commit()
    return {"message": "Password has been reset successfully"}