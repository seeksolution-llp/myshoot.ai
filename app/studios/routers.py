from fastapi import Response, APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import ChangePasswordIn, ForgotPasswordIn, ResetPasswordIn, StudioUpdateIn
from app.auth.services import create_refresh_token
from app.db.config import SessionDep
from app.admin.schemas import TokenOut
from app.studios.models import Studio
from sqlalchemy import select
from app.studios.schemas import StudioCreate, StudioOut
from app.studios.services import change_studio_password, create_studio, get_all_studios, get_studio_by_id, get_studio_by_email, process_studio_forgot_password, process_studio_reset_password, update_studio_profile
from app.utils import SecurityHelper
from app.dependencies import get_current_studio_id, get_current_user_id
from typing import List
from app.studios.services import get_studio_by_id

router = APIRouter()

@router.post("/register", response_model=StudioOut, status_code=status.HTTP_201_CREATED)
async def register_studio(data: StudioCreate, session: SessionDep):
    return await create_studio(session, data)

@router.post("/login", response_model=TokenOut)
async def login_studio(
    response: Response,
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1. Look up the studio by email
    stmt = select(Studio).where(Studio.email == form_data.username)
    result = await session.scalars(stmt)
    studio = result.first()
    
    # 2. Verify existence and password
    if not studio or not SecurityHelper.verify_password(form_data.password, studio.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect studio email or password"
        )
    
    # 3. Encode the STUDIO_ID into the token
    access_token = SecurityHelper.create_access_token(data={"sub": studio.studio_id, "role": "studio"})
    refresh_token = await create_refresh_token(session, studio.studio_id, "studio") # Import from app.auth.services
    response.set_cookie(
        key="studio_access_token",
        value=access_token, 
        httponly=True,       # Hides it from browser scripts completely
        secure=False,        # Set to True later once you host it on HTTPS
        samesite="lax",      # Anti-CSRF protection
        max_age=1800         # Lasts 30 minutes
    )

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
}

@router.post("/logout")
async def logout_studio(response: Response, current_studio_id: str = Depends(get_current_studio_id)):
    """
    LOGOUT OPERATION: Instructs the browser to remove the secure 
    studio cookie mapping via HTTP headers immediately.
    """
    response.delete_cookie(key="studio_access_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Studio session terminated successfully"}

@router.put("/profile", response_model=StudioOut)
async def update_profile(data: StudioUpdateIn, session: SessionDep, current_studio_id: str = Depends(get_current_studio_id)):
    return await update_studio_profile(session, current_studio_id, data)

@router.post("/change-password")
async def change_password(data: ChangePasswordIn, session: SessionDep, current_studio_id: str = Depends(get_current_studio_id)):
    return await change_studio_password(session, current_studio_id, data)

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordIn, session: SessionDep):
    return await process_studio_forgot_password(session, data.email)

@router.post("/reset-password")
async def reset_password(data: ResetPasswordIn, session: SessionDep):
    return await process_studio_reset_password(session, data)

@router.get("/", response_model=List[StudioOut])
async def read_all_studios(session: SessionDep):
    return await get_all_studios(session)

@router.get("/me", response_model=StudioOut)
async def get_my_studio_profile(
    session: SessionDep,
    current_studio_id: str = Depends(get_current_studio_id) # <-- CHANGE THIS PARAMETER
):
    # Change any function calls inside to look up using current_studio_id
    return await get_studio_by_id(session, current_studio_id)
