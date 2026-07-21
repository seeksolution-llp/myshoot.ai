from pydantic import BaseModel, EmailStr, Field

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str



class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

class AdminUpdateIn(BaseModel):
    name: str
    email: EmailStr

class StudioUpdateIn(BaseModel):
    name: str
    email: EmailStr
    plan_type: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, description="The new secure password string")


