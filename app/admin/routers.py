from fastapi import Response, APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import AdminUpdateIn, ChangePasswordIn, ForgotPasswordIn, ResetPasswordIn
from app.db.config import SessionDep
from app.admin.schemas import AdminCreate, AdminOut, AdminStudioUpdateIn, TokenOut, AdminAnalyticsOut
from app.studios.schemas import StudioOut
from app.admin.services import (
    admin_modify_studio, admin_remove_studio, create_admin, get_all_admins, get_admin_by_id, get_admin_by_email, 
    admin_view_studios, admin_view_analytics, update_admin_profile, change_admin_password, 
    process_admin_forgot_password, process_admin_reset_password
)
from app.utils import SecurityHelper
from app.dependencies import get_current_user_id
from typing import List
from app.auth.services import create_refresh_token

router = APIRouter()

@router.post("/register", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
async def register_admin(data: AdminCreate, session: SessionDep):
    return await create_admin(session, data)

@router.post("/login", response_model=TokenOut)
async def login_admin(
    response: Response,
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    admin = await get_admin_by_email(session, form_data.username)
    if not admin or not SecurityHelper.verify_password(form_data.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = SecurityHelper.create_access_token(data={"sub": admin.admin_id, "role": "admin"})
    refresh_token = await create_refresh_token(session, admin.admin_id, "admin") # Import from app.auth.services

    response.set_cookie(
        key="access_token",
        value=access_token, # The raw token string
        httponly=True,      # Crucial: Hides token from browser JavaScript/XSS scripts
        secure=False,       # Set to True in production once you have an HTTPS/SSL certificate
        samesite="lax",     # Protects against CSRF attacks
        max_age=1800        # Cookie lifetime matching your token expiration (30 mins in seconds)
    )

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout_admin(response: Response, current_admin_id: str = Depends(get_current_user_id)):
    """
    LOGOUT OPERATION: Tells the web browser to purge the cookie 
    while remaining fully compliant with stateless mobile platforms.
    """
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Admin session terminated successfully"}

@router.put("/profile", response_model=AdminOut)
async def update_profile(data: AdminUpdateIn, session: SessionDep, current_admin_id: str = Depends(get_current_user_id)):
    return await update_admin_profile(session, current_admin_id, data)

@router.post("/change-password")
async def change_password(data: ChangePasswordIn, session: SessionDep, current_admin_id: str = Depends(get_current_user_id)):
    return await change_admin_password(session, current_admin_id, data)

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordIn, session: SessionDep):
    return await process_admin_forgot_password(session, data.email)

@router.post("/reset-password")
async def reset_password(data: ResetPasswordIn, session: SessionDep):
    return await process_admin_reset_password(session, data)


@router.get("/", response_model=List[AdminOut])
async def read_all_admins(session: SessionDep):
    return await get_all_admins(session)

@router.get("/me", response_model=AdminOut)
async def get_my_admin_profile(
    session: SessionDep,
    current_admin_id: str = Depends(get_current_user_id)
):
    return await get_admin_by_id(session, current_admin_id)

@router.get("/studios", response_model=List[StudioOut])
async def admin_view_all_registered_studios(
    session: SessionDep,
    current_admin_id: str = Depends(get_current_user_id)
):
    """Admin operational method: viewStudios()"""
    return await admin_view_studios(session)

@router.get("/analytics", response_model=AdminAnalyticsOut)
async def admin_view_system_analytics(
    session: SessionDep,
    current_admin_id: str = Depends(get_current_user_id)
):
    """Admin operational method: viewAnalytics()"""
    return await admin_view_analytics(session)


@router.put("/studios/{studio_id}", response_model=StudioOut)
async def admin_edit_studio(
    studio_id: str,
    data: AdminStudioUpdateIn,
    session: SessionDep,
    current_admin_id: str = Depends(get_current_user_id) # Enforces strict admin check
):
    """Allows an authorized administrator to edit a studio's profile or plan parameters."""
    # Convert Pydantic object to a standard Python dictionary filtering out unset values
    update_data = data.model_dump(exclude_unset=True)
    return await admin_modify_studio(session, studio_id, update_data)


@router.delete("/studios/{studio_id}", status_code=status.HTTP_200_OK)
async def admin_delete_studio(
    studio_id: str,
    session: SessionDep,
    current_admin_id: str = Depends(get_current_user_id) # Enforces strict admin check
):
    """Deletes a studio and cascades down to clean up all storage metadata allocations."""
    return await admin_remove_studio(session, studio_id)