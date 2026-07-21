from datetime import datetime, timedelta, timezone
from typing import Optional
from decouple import config
import jwt
from passlib.context import CryptContext
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pathlib import Path


# Configuration
SECRET_KEY = config("JWT_SECRET_KEY")
ALGORITHM = config("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=30)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityHelper:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt



# Load mail infrastructure environmental keys
mail_config = ConnectionConfig(
    MAIL_USERNAME=config("MAIL_USERNAME"),
    MAIL_PASSWORD=config("MAIL_PASSWORD"),
    MAIL_FROM=config("MAIL_FROM"),
    MAIL_PORT=config("MAIL_PORT", cast=int),
    MAIL_SERVER=config("MAIL_SERVER"),
    MAIL_FROM_NAME=config("MAIL_FROM_NAME"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_reset_password_email(email_to: str, reset_link: str):
    """Asynchronously dispatches an elegant HTML recovery link email."""
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #4A90E2; text-align: center;">Reset Your Password</h2>
                <p>Hello,</p>
                <p>We received a request to reset the password for your Face Matching account. Click the secure button below to choose a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #4A90E2; color: white; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block;">Reset Password</a>
                </div>
                <p>If you did not make this request, you can safely ignore this email. This link will remain active for the next 15 minutes.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
                <p style="font-size: 0.8em; color: #777; text-align: center;">This is an automated operational system message. Please do not reply directly.</p>
            </div>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Password Reset Request - Face Matching System",
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message)
