import uuid
from datetime import datetime, timedelta, timezone
from fastapi import BackgroundTasks, HTTPException, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.models import RefreshToken
from app.auth.schemas import ResetPasswordConfirmRequest
from app.utils import SecurityHelper
from decouple import config
from app.studios.models import Studio
from app.admin.models import Admin
from app.utils import send_reset_password_email

# Read it directly from your config/environment instead of importing it
BACKEND_URL = config("BACKEND_URL", default="http://127.0.0.1:8000")


REFRESH_TOKEN_EXPIRE_DAYS = config("REFRESH_TOKEN_EXPIRE_DAYS", cast=int)


async def create_refresh_token(session: AsyncSession, user_id: str, role: str) -> str:
    """Generates a secure token string and hooks it to the proper model relation columns."""
    raw_token_str = str(uuid.uuid4())
    expiry_time = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Base model instantiation parameter maps
    token_kwargs = {
        "role": role,
        "token": raw_token_str,
        "expires_at": expiry_time
    }
    
    # Assign the correct ID column based on runtime role validation
    if role == "admin":
        token_kwargs["admin_id"] = user_id
        # Revoke older existing active sessions for this explicit admin
        stmt = select(RefreshToken).where(RefreshToken.admin_id == user_id, RefreshToken.is_revoked == False)
    elif role == "studio":
        token_kwargs["studio_id"] = user_id
        # Revoke older existing active sessions for this explicit studio
        stmt = select(RefreshToken).where(RefreshToken.studio_id == user_id, RefreshToken.is_revoked == False)
    else:
        raise ValueError("Invalid role provided for token attachment context")
        
    # Revoke old tokens
    existing_tokens = await session.scalars(stmt)
    for old_token in existing_tokens.all():
        old_token.is_revoked = True
        
    db_token = RefreshToken(**token_kwargs)
    session.add(db_token)
    await session.commit()
    return raw_token_str

async def rotate_refresh_token_pipeline(session: AsyncSession, token_str: str):
    """Validates token maps, marks old session entries dead, and issues new token sets."""
    stmt = select(RefreshToken).where(RefreshToken.token == token_str)
    result = await session.scalars(stmt)
    refresh_record = result.first()
    
    if not refresh_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if refresh_record.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    if refresh_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        
    refresh_record.is_revoked = True
    
    # Read the active subject ID depending on who owns the token row parameters
    owner_id = refresh_record.admin_id if refresh_record.role == "admin" else refresh_record.studio_id
    
    new_access_token = SecurityHelper.create_access_token(
        data={"sub": owner_id, "role": refresh_record.role}
    )
    new_refresh_token = await create_refresh_token(session, owner_id, refresh_record.role)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }





SECRET_KEY = config("JWT_SECRET_KEY")
ALGORITHM = config("JWT_ALGORITHM", default="HS256")

async def process_forgot_password_pipeline(
    session: AsyncSession, 
    email: str, 
    background_tasks: BackgroundTasks
):
    """Locates the account identity context and schedules an email delivery item."""
    user_id = None
    role = None
    
    # 1. Search for a matching email profile across your isolated storage models
    studio_stmt = select(Studio).where(Studio.email == email)
    studio_res = await session.scalars(studio_stmt)
    studio = studio_res.first()
    
    if studio:
        user_id = studio.studio_id
        role = "studio"
    else:
        admin_stmt = select(Admin).where(Admin.email == email)
        admin_res = await session.scalars(admin_stmt)
        admin = admin_res.first()
        if admin:
            user_id = admin.admin_id
            role = "admin"
            
    # Standard defensive security guard: Return an identical success text payload 
    # even if the email does not exist to prevent malicious actor enumeration attacks.
    if not user_id:
        return {"message": "If the account exists, a recovery link has been dispatched to your email address."}
        
    # 2. Construct a tight 15-minute single-use verification verification token
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_payload = {"sub": user_id, "role": role, "exp": expire, "purpose": "password_reset"}
    reset_token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # 3. Compile the link route string targeted towards your endpoint receiver system
    reset_link = f"{BACKEND_URL}/auth/reset-password?token={reset_token}"
    
    # 4. Enqueue the SMTP execution out into a background non-blocking execution thread
    background_tasks.add_task(send_reset_password_email, email, reset_link)
    
    return {"message": "If the account exists, a recovery link has been dispatched to your email address."}


async def process_password_reset_confirmation(session: AsyncSession, data: ResetPasswordConfirmRequest):
    """Decodes the verification token and commits the new hashed password to storage."""
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token purpose specification.")
            
        user_id = payload.get("sub")
        role = payload.get("role")
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="The reset link has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid or corrupted security token.")

    # 2. USE YOUR SECURITYHELPER CLASS HERE TO HASH THE PASSWORD SECURELY
    hashed_password = SecurityHelper.hash_password(data.new_password)

    # 3. Locate the entity based on the role
    if role == "studio":
        stmt = select(Studio).where(Studio.studio_id == user_id)
        result = await session.scalars(stmt)
        user = result.first()
    elif role == "admin":
        stmt = select(Admin).where(Admin.admin_id == user_id)
        result = await session.scalars(stmt)
        user = result.first()
    else:
        user = None

    if not user:
        raise HTTPException(status_code=404, detail="Target account profile could not be found.")

    # 4. Bind the new credentials and save to database
    user.password = hashed_password
    await session.commit()

    return {"message": "Password updated successfully. You can now log in with your new credentials."}