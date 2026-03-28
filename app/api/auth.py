"""
Authentication endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
import jwt
import bcrypt

from app.config import config
from app.db import UserRepository
from app.services.email import email_service
from app.services.google_oauth import google_oauth_service

auth_router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
user_repo = UserRepository()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_verification: bool = False


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str] = None
    balance: float
    is_verified: bool
    created_at: datetime


class VerifyRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=config.JWT_EXPIRY_MINUTES),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")


def create_verification_token() -> str:
    return secrets.token_urlsafe(32)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials, 
            config.JWT_SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@auth_router.post("/signup")
async def signup(request: SignupRequest):
    existing = user_repo.get_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password_hash = hash_password(request.password)
    verification_token = create_verification_token()
    
    user = user_repo.create(
        email=request.email,
        password_hash=password_hash,
        display_name=request.display_name,
        verification_token=verification_token
    )
    
    email_service.send_verification_email(user.email, verification_token)
    
    token = create_token(user.id)
    
    return {
        "token": token,
        "message": "Account created. Please check your email to verify.",
        "requires_verification": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": None,
            "balance": user.balance,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }


@auth_router.post("/login")
async def login(request: LoginRequest):
    user = user_repo.get_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.id)
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": getattr(user, 'avatar_url', None),
            "balance": user.balance,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }


@auth_router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}


@auth_router.post("/verify")
async def verify_email(request: VerifyRequest):
    user = user_repo.get_by_verification_token(request.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    user_repo.verify_user(user.id)
    
    return {"message": "Email verified successfully"}


@auth_router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest):
    user = user_repo.get_by_email(request.email)
    if not user:
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.is_verified:
        return {"message": "Email is already verified"}
    
    verification_token = create_verification_token()
    
    with user_repo._get_db() if hasattr(user_repo, '_get_db') else None:
        from app.db.connection import get_db
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE users 
                SET verification_token = %s, verification_expires = NOW() + INTERVAL '24 hours'
                WHERE id = %s
                """,
                (verification_token, user.id)
            )
    
    email_service.send_verification_email(user.email, verification_token)
    
    return {"message": "Verification email sent"}


@auth_router.get("/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=getattr(user, 'avatar_url', None),
        balance=user.balance,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@auth_router.get("/session", response_model=UserResponse)
async def get_session(user = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=getattr(user, 'avatar_url', None),
        balance=user.balance,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@auth_router.get("/google")
async def google_login(response: Response):
    state = secrets.token_urlsafe(32)
    
    auth_url = google_oauth_service.get_auth_url(state)
    
    response = RedirectResponse(url=auth_url)
    
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600
    )
    
    return response


@auth_router.get("/google/callback")
async def google_callback(request: Request, code: str, state: str):
    oauth_state = request.cookies.get("oauth_state")
    
    if not oauth_state or oauth_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        tokens = await google_oauth_service.exchange_code(code)
        user_info = await google_oauth_service.get_user_info(tokens["access_token"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")
    
    user = user_repo.get_by_google_id(user_info.google_id)
    
    if not user:
        user = user_repo.get_by_email(user_info.email)
        
        if user:
            user = user_repo.link_google(
                user_id=user.id,
                google_id=user_info.google_id,
                avatar_url=user_info.picture
            )
        else:
            user = user_repo.create_from_google(
                email=user_info.email,
                google_id=user_info.google_id,
                display_name=user_info.name,
                avatar_url=user_info.picture
            )
    
    token = create_token(user.id)
    
    response = RedirectResponse(url=f"{config.FRONTEND_URL}/auth/callback?token={token}")
    
    response.delete_cookie("oauth_state")
    
    return response
