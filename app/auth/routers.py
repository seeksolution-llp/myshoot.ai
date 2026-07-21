from fastapi import APIRouter, BackgroundTasks
from app.db.config import SessionDep
from app.auth.schemas import RefreshTokenRequest, ResetPasswordConfirmRequest, TokenPairOut
from app.auth.services import process_password_reset_confirmation, rotate_refresh_token_pipeline
from app.auth.schemas import ForgotPasswordRequest
from app.auth.services import process_forgot_password_pipeline

router = APIRouter()

@router.post("/refresh", response_model=TokenPairOut)
async def refresh_user_session_tokens(data: RefreshTokenRequest, session: SessionDep):
    """
    Called automatically by Android network interceptors when an access token expires.
    Takes a valid refresh token and returns a fresh active payload pair.
    """
    return await rotate_refresh_token_pipeline(session, data.refresh_token)


@router.post("/forgot-password")
async def forgot_password_endpoint(
    data: ForgotPasswordRequest, 
    session: SessionDep, 
    background_tasks: BackgroundTasks
):
    """
    Accepts password reset triggers submitted by mobile devices, calculates security tokens,
    and handles secure delivery out to the user's personal email inbox in the background.
    """
    return await process_forgot_password_pipeline(session, data.email, background_tasks)


@router.post("/reset-password-confirm")
async def reset_password_confirm_endpoint(
    data: ResetPasswordConfirmRequest,
    session: SessionDep
):
    """
    Consumes the short-lived email verification token along with the user's
    new password choice, validating credentials before committing changes 
    using the SecurityHelper class.
    """
    return await process_password_reset_confirmation(session, data)