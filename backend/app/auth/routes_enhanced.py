#!/usr/bin/env python3
"""
Enhanced authentication routes with security improvements
"""

from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from .models import User, APIKey, SubscriptionTier
from .security_enhanced import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    create_refresh_token,
    verify_token,
    password_validator,
    api_key_manager,
    SECURITY_HEADERS
)
from .rate_limiter import (
    check_login_rate_limit,
    check_register_rate_limit,
    ip_limiter
)
from .dependencies import get_current_user

# Pydantic models
from pydantic import BaseModel, Field, EmailStr, validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v, values):
        username = values.get('username')
        result = password_validator.validate_password(v, username)
        if not result['is_valid']:
            raise ValueError('; '.join(result['feedback']))
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordStrengthCheck(BaseModel):
    password: str
    username: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    allowed_ips: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

class APIKeyResponse(BaseModel):
    key: str  # Only returned on creation
    key_prefix: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Add security headers to all responses
@router.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(check_register_rate_limit)
):
    """
    Register a new user with enhanced security
    """
    # Check IP block list
    client_ip = request.client.host if request.client else "unknown"
    if not ip_limiter.check_ip(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP address blocked due to suspicious activity"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(
            User.username == user_data.username.lower(),
            User.email == user_data.email.lower()
        )
    ).first()
    
    if existing_user:
        # Don't reveal which field is duplicate (security)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try different credentials."
        )
    
    # Create new user with secure password
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username.lower(),
        email=user_data.email.lower(),
        hashed_password=hashed_password,
        is_active=True,
        email_verified=False,  # Require email verification
        subscription_tier=SubscriptionTier.FREE,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(check_login_rate_limit)
):
    """
    Login with enhanced security and rate limiting
    """
    # Check IP block list
    client_ip = request.client.host if request.client else "unknown"
    if not ip_limiter.check_ip(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP address blocked due to suspicious activity"
        )
    
    # Find user (case insensitive)
    user = db.query(User).filter(
        User.username == form_data.username.lower()
    ).first()
    
    # Generic error message for security
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    if not user:
        # Report suspicious activity if too many failed attempts
        ip_limiter.report_suspicious_activity(client_ip, "invalid_username")
        raise invalid_credentials_error
    
    # Check password
    if not verify_password(form_data.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.account_locked_until = datetime.utcnow() + timedelta(hours=1)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to multiple failed login attempts. Try again later."
            )
        
        db.commit()
        ip_limiter.report_suspicious_activity(client_ip, "invalid_password")
        raise invalid_credentials_error
    
    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked. Try again later."
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800
    )

@router.post("/check-password-strength")
async def check_password_strength(data: PasswordStrengthCheck):
    """
    Check password strength without creating account
    """
    result = password_validator.validate_password(data.password, data.username)
    
    return {
        "is_valid": result["is_valid"],
        "strength_score": result["strength_score"],
        "entropy_bits": result["entropy_bits"],
        "feedback": result["feedback"]
    }

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key with secure storage
    """
    # Check user's API key limit based on subscription
    existing_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).count()
    
    key_limits = {
        SubscriptionTier.FREE: 1,
        SubscriptionTier.PRO: 5,
        SubscriptionTier.ENTERPRISE: 50
    }
    
    limit = key_limits.get(current_user.subscription_tier, 1)
    if existing_keys >= limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key limit reached for {current_user.subscription_tier} tier"
        )
    
    # Generate secure API key
    plain_key, key_hash = api_key_manager.generate_api_key()
    key_prefix = api_key_manager.extract_key_prefix(plain_key)
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        user_id=current_user.id,
        expires_at=expires_at,
        allowed_ips=json.dumps(key_data.allowed_ips) if key_data.allowed_ips else None,
        permissions=json.dumps(key_data.permissions) if key_data.permissions else None,
        rate_limit=60 if current_user.subscription_tier == SubscriptionTier.FREE else 300
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Return the plain key only on creation
    return APIKeyResponse(
        key=plain_key,
        key_prefix=key_prefix,
        name=api_key.name,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at
    )

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's API keys (without showing the actual keys)
    """
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    
    # Never return the actual keys, only metadata
    return [
        APIKeyResponse(
            key="",  # Never expose stored keys
            key_prefix=key.key_prefix,
            name=key.name,
            created_at=key.created_at,
            expires_at=key.expires_at
        )
        for key in keys
    ]

@router.delete("/api-keys/{key_prefix}")
async def revoke_api_key(
    key_prefix: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key
    """
    api_key = db.query(APIKey).filter(
        APIKey.key_prefix == key_prefix,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = False
    db.commit()
    
    return {"message": "API key revoked successfully"}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user (placeholder for token blacklisting)
    """
    # In production, blacklist the token in Redis
    # For now, just return success
    return {"message": "Logged out successfully"}

if __name__ == "__main__":
    # Test password validation
    test_cases = [
        ("weak123", "testuser"),
        ("TestUser123!", "testuser"),
        ("Str0ng!P@ssw0rd", "testuser"),
        ("MySecureP@ss2024!", None)
    ]
    
    for password, username in test_cases:
        result = password_validator.validate_password(password, username)
        print(f"\nPassword: {password}")
        print(f"Valid: {result['is_valid']}")
        print(f"Strength: {result['strength_score']}%")
        print(f"Feedback: {result['feedback']}")