from fastapi import HTTPException, status, Request, Depends  # Added Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Added Bearer schema
import jwt
from sqlalchemy import select
from app.db.config import SessionDep
from app.studios.models import Studio
from decouple import config

SECRET_KEY = config("JWT_SECRET_KEY")
ALGORITHM = config("JWT_ALGORITHM")

# FIX: Define a non-blocking Swagger scheme element configuration definition node
# auto_error=False guarantees missing headers won't auto-reject and crash web browser cookies
swagger_bearer_scheme = HTTPBearer(auto_error=False)


def extract_token_manually(request: Request, swagger_auth: HTTPAuthorizationCredentials | None) -> str:
    """
    Custom extraction helper. Prioritises Swagger/Android headers, 
    then falls back to secure browser cookies.
    """
    # 1. Try to read from incoming Swagger UI / Android header schema instance
    if swagger_auth:
        return swagger_auth.credentials
        
    # 2. Try to read from incoming standard Authorization Header string fallback
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
        
    # 3. Try to read from the Browser Cookie fallback box
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
        
    return None


async def get_current_user_id(
    request: Request,
    swagger_auth: HTTPAuthorizationCredentials = Depends(swagger_bearer_scheme) # <-- INJECT THIS
) -> str:
    """Custom authorization guard for Admins with Swagger UI padlock capability."""
    actual_token = extract_token_manually(request, swagger_auth)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not actual_token:
        print("[AUTH DEBUG] Admin request blocked: No token found in headers or cookies.")
        raise credentials_exception

    try:
        payload = jwt.decode(actual_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")  
        
        if user_id is None or role != "admin":
            print(f"[AUTH DEBUG] Admin token rejected. sub: {user_id}, role: {role}")
            raise credentials_exception
            
        return user_id
    except jwt.PyJWTError as e:
        print(f"[AUTH DEBUG] Admin token decryption failed: {str(e)}")
        raise credentials_exception


# =========================================================================
# FIXED STUDIO AUTHORIZATION LAYER WITH SWAGGER LOCK SUPPORT
# =========================================================================
async def get_current_studio_id(
    request: Request, 
    session: SessionDep,
    swagger_auth: HTTPAuthorizationCredentials = Depends(swagger_bearer_scheme) # <-- INJECT THIS
) -> str:
    """Custom authorization guard for Studio Owners with Swagger UI padlock capability."""
    # Look inside cookies using studio specific namespace identifier tags if header drops empty
    actual_token = extract_token_manually(request, swagger_auth)
    if not actual_token:
        actual_token = request.cookies.get("studio_access_token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate studio credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not actual_token:
        print("[STUDIO AUTH DEBUG] Request blocked: No token found in headers or cookies.")
        raise credentials_exception

    try:
        payload = jwt.decode(actual_token, SECRET_KEY, algorithms=[ALGORITHM])
        studio_id: str = payload.get("sub")
        role: str = payload.get("role")  
        
        if studio_id is None or role != "studio":
            print(f"[STUDIO AUTH DEBUG] Rejected context sub={studio_id}, role={role}")
            raise credentials_exception

    except jwt.PyJWTError as e:
        print(f"[STUDIO AUTH ERROR] Decryption failure message parameters: {str(e)}")
        raise credentials_exception

    # Database Security Check: Ensure this ID actually belongs to a real studio
    stmt = select(Studio).where(Studio.studio_id == studio_id)
    result = await session.scalars(stmt)
    studio = result.first()
    
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot perform studio operations. Please log in as a studio."
        )
        
    return studio_id
