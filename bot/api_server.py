"""FastAPI server for UPC World Bot - handles Telegram authentication and JWT tokens."""
import hmac
import hashlib
import json
import time
import asyncio
from typing import Optional
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import jwt

from bot.config import settings
from bot.database.session import db_manager
from bot.database.repositories.user_repository import UserRepository
from bot.utils.logger import logger


# ========== SETUP ==========
app = FastAPI(
    title="UPC World API",
    description="Backend API for Under People Club Bot",
    version="1.0.0"
)

# Configure CORS - Allow requests from website and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.website_url,
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ========== AUTH CODE STORAGE ==========
# In production, use Redis instead of in-memory storage
# Format: {code: user_id, expires_at: timestamp}
auth_codes: dict = {}

def cleanup_expired_codes():
    """Remove expired auth codes (older than 15 minutes)."""
    current_time = time.time()
    expired = [code for code, data in auth_codes.items() 
               if current_time - data.get("created_at", 0) > 900]  # 15 minutes
    for code in expired:
        del auth_codes[code]
    if expired:
        logger.info("auth_codes_cleanup", removed_count=len(expired))


# ========== MODELS ==========
class TelegramAuthData(BaseModel):
    """Telegram Widget Authentication Data."""
    id: int = Field(..., description="User Telegram ID")
    first_name: str = Field(..., description="User first name")
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int = Field(..., description="Unix timestamp of auth")
    hash: str = Field(..., description="Telegram hash for verification")


class AuthCodeRequest(BaseModel):
    """Request to exchange auth code for token."""
    code: str = Field(..., description="One-time auth code")


class AuthCodeResponse(BaseModel):
    """Response with authorization code."""
    code: str
    url: str


class AuthResponse(BaseModel):
    """Response after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfileResponse(BaseModel):
    """User profile data."""
    id: int
    username: Optional[str]
    first_name: str
    membership_level: str
    up_coins: float
    daily_streak: int
    total_events_attended: int
    referral_count: int
    referral_earnings: float


# ========== AUTHENTICATION FUNCTIONS ==========
def verify_telegram_data(data: dict, bot_token: str) -> bool:
    """
    Verify Telegram Widget data using cryptographic hash.
    This ensures the data really comes from Telegram.
    """
    # Extract and remove hash from data
    received_hash = data.pop('hash', None)
    if not received_hash:
        logger.warning("telegram_auth_failed", reason="no_hash")
        return False

    # Create data check string (sorted by key)
    data_check_string = []
    for key, value in sorted(data.items()):
        if value is not None:
            data_check_string.append(f"{key}={value}")

    data_check_string_str = "\n".join(data_check_string)
    
    # Calculate hash using BOT_TOKEN as secret
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string_str.encode(),
        hashlib.sha256
    ).hexdigest()

    is_valid = calculated_hash == received_hash
    
    if not is_valid:
        logger.warning(
            "telegram_auth_failed",
            reason="hash_mismatch",
            received=received_hash[:10] + "...",
            calculated=calculated_hash[:10] + "..."
        )
    
    return is_valid


def create_access_token(user_id: int, username: Optional[str] = None) -> str:
    """Create JWT token for authenticated user."""
    payload = {
        "sub": str(user_id),  # subject = user_id
        "username": username,
        "iat": datetime.utcnow(),  # issued at
        "exp": datetime.utcnow() + timedelta(days=7)  # expires in 7 days
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256"
    )
    
    return token


def verify_access_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_auth_code(user_id: int) -> str:
    """Generate one-time auth code."""
    # Cleanup expired codes every 10 minutes
    if len(auth_codes) % 10 == 0:
        cleanup_expired_codes()
    
    code = str(uuid4())
    auth_codes[code] = {
        "user_id": user_id,
        "created_at": time.time(),
        "used": False
    }
    
    logger.info("auth_code_generated", code=code[:8] + "...", user_id=user_id)
    return code


# ========== ENDPOINTS ==========
@app.post("/api/auth/code/exchange", response_model=AuthResponse)
async def exchange_auth_code(request: AuthCodeRequest):
    """
    Exchange one-time auth code for JWT token.
    This is called by the website after user clicks bot login link.
    
    Flow:
    1. User clicks "Войти" in Telegram Bot
    2. Bot generates code and sends deep link with ?code=xxx
    3. User clicks link, returns to website with code in URL
    4. Website calls this endpoint with the code
    5. Website gets JWT token and user data
    6. Website stores token in localStorage and logs user in
    """
    try:
        code = request.code
        
        # Cleanup old codes
        cleanup_expired_codes()
        
        # Find code in storage
        code_data = auth_codes.get(code)
        if not code_data:
            logger.warning("auth_code_not_found", code=code[:8] + "...")
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired auth code"
            )
        
        # Check if code is older than 15 minutes
        age_seconds = time.time() - code_data.get("created_at", 0)
        if age_seconds > 900:  # 15 minutes
            del auth_codes[code]
            logger.warning("auth_code_expired", code=code[:8] + "...", age_seconds=age_seconds)
            raise HTTPException(
                status_code=403,
                detail="Auth code expired (max 15 minutes)"
            )
        
        # Check if already used
        if code_data.get("used"):
            logger.warning("auth_code_reused", code=code[:8] + "...")
            raise HTTPException(
                status_code=403,
                detail="Auth code already used"
            )
        
        user_id = code_data["user_id"]
        
        # Get user from database
        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            
            if not user:
                logger.error("auth_code_user_not_found", user_id=user_id)
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
        
        # Mark code as used and delete it
        auth_codes[code]["used"] = True
        del auth_codes[code]
        
        # Generate JWT token
        access_token = create_access_token(
            user_id=user_id,
            username=user.username
        )
        
        logger.info(
            "auth_code_exchanged",
            user_id=user_id,
            code=code[:8] + "..."
        )
        
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user_id,
                "username": user.username,
                "first_name": user.first_name,
                "role": "member" if user.is_member else "guest"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "auth_code_exchange_exception",
            error=str(e),
            code=request.code[:8] + "..." if request.code else None
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.post("/api/auth/code/generate", response_model=AuthCodeResponse)
async def generate_auth_code_endpoint(user_id: int = Body(..., embed=True)):
    """
    Generate one-time auth code and return redirect URL.
    This is called by the bot when user clicks "Войти на сайт" button.
    
    The returned URL will be used as a deep link that returns the user to the website
    with the auth code in the query string.
    """
    try:
        # Validate user exists
        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            
            if not user:
                logger.warning("auth_code_generate_user_not_found", user_id=user_id)
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
        
        # Generate code
        code = generate_auth_code(user_id)
        
        # Create redirect URL (website will exchange this code for JWT)
        callback_url = f"{settings.website_url}/auth/callback?code={code}"
        
        logger.info(
            "auth_code_generated_for_user",
            user_id=user_id,
            code=code[:8] + "..."
        )
        
        return AuthCodeResponse(
            code=code,
            url=callback_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "auth_code_generate_exception",
            error=str(e),
            user_id=user_id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.post("/api/auth/telegram", response_model=AuthResponse)
async def telegram_login(auth_data: TelegramAuthData):
    """
    Authenticate user via Telegram Widget.
    
    1. Verifies Telegram hash (ensures data is genuine)
    2. Checks if data is not expired (max 24 hours)
    3. Finds or creates user in database
    4. Returns JWT token for subsequent requests
    """
    try:
        logger.info(
            "telegram_auth_attempt",
            user_id=auth_data.id,
            username=auth_data.username
        )
        
        # Step 1: Verify hash
        data_dict = auth_data.dict(exclude_none=True)
        if not verify_telegram_data(data_dict.copy(), settings.bot_token):
            logger.warning(
                "telegram_auth_rejected",
                user_id=auth_data.id,
                reason="invalid_hash"
            )
            raise HTTPException(
                status_code=403,
                detail="Invalid Telegram authentication data"
            )
        
        # Step 2: Check auth data age (must be <= 24 hours)
        current_time = time.time()
        age_seconds = current_time - auth_data.auth_date
        if age_seconds > 86400:  # 24 hours in seconds
            logger.warning(
                "telegram_auth_rejected",
                user_id=auth_data.id,
                reason="expired_data",
                age_hours=age_seconds / 3600
            )
            raise HTTPException(
                status_code=400,
                detail="Authentication data expired (older than 24 hours)"
            )
        
        # Step 3: Find or create user in database
        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(auth_data.id)
            
            if not user:
                # Create new user
                logger.info(
                    "new_user_created",
                    user_id=auth_data.id,
                    username=auth_data.username
                )
                user = await user_repo.create_user(
                    telegram_id=auth_data.id,
                    username=auth_data.username or f"user_{auth_data.id}",
                    first_name=auth_data.first_name,
                    last_name=auth_data.last_name,
                    photo_url=auth_data.photo_url
                )
            else:
                # Update existing user if needed
                if user.username != auth_data.username:
                    user.username = auth_data.username or f"user_{auth_data.id}"
                if user.first_name != auth_data.first_name:
                    user.first_name = auth_data.first_name
                await session.commit()
                logger.info("user_login", user_id=auth_data.id)
        
        # Step 4: Generate JWT token
        access_token = create_access_token(
            user_id=auth_data.id,
            username=auth_data.username
        )
        
        logger.info(
            "user_authenticated",
            user_id=auth_data.id,
            token_issued=True
        )
        
        return AuthResponse(
            access_token=access_token,
            user={
                "id": auth_data.id,
                "username": auth_data.username,
                "first_name": auth_data.first_name,
                "role": "member" if user.is_member else "guest"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "telegram_auth_exception",
            error=str(e),
            user_id=auth_data.id if auth_data else None
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )


@app.get("/api/users/me", response_model=UserProfileResponse)
async def get_user_profile(authorization: str = None):
    """
    Get current user's profile using JWT token.
    
    Authorization header format: "Bearer {token}"
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Missing Authorization header"
            )
        
        # Extract token from "Bearer {token}"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format"
            )
        
        token = parts[1]
        
        # Verify token
        payload = verify_access_token(token)
        user_id = int(payload.get("sub"))
        
        # Get user from database
        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            logger.info("profile_requested", user_id=user_id)
            
            return UserProfileResponse(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                membership_level=user.membership_level or "guest",
                up_coins=float(user.up_coins),
                daily_streak=user.daily_streak,
                total_events_attended=user.total_events_attended,
                referral_count=user.referral_count,
                referral_earnings=float(user.referral_earnings)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "profile_request_exception",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle CORS preflight requests."""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )
