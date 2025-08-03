#!/usr/bin/env python3
"""
Enhanced authentication routes with security improvements
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from .models import (
    User, APIKey, UserCreate, UserUpdate, UserInDB, Token, 
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse
)
from .security_enhanced import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    SecureAPIKeyManager, PasswordValidator
)
from .dependencies import get_current_user, get_current_active_user, get_current_superuser
from .rate_limiter import (
    login_rate_limit, register_rate_limit, refresh_rate_limit,
    password_reset_rate_limit, add_rate_limit_headers
)
from .oauth import get_oauth_provider, OAuthStateManager, OAuthUserInfo
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserInDB)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    rate_limit_info = Depends(register_rate_limit)
):
    """Register a new user with enhanced security"""
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength (done in get_password_hash)
    try:
        hashed_password = get_password_hash(user_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create new user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        subscription_tier="free",
        api_calls_limit=100
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Add rate limit headers
    add_rate_limit_headers(response, rate_limit_info)
    
    return db_user

@router.post("/token", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    rate_limit_info = Depends(login_rate_limit)
):
    """Login and get access token with rate limiting"""
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Create access token with enhanced security
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "user_id": user.id,
            "login_ip": request.client.host if request.client else "unknown"
        },
        expires_delta=access_token_expires
    )
    
    # Add rate limit headers
    add_rate_limit_headers(response, rate_limit_info)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # seconds
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    rate_limit_info = Depends(refresh_rate_limit)
):
    """Refresh access token using refresh token"""
    from .security_enhanced import SecureTokenManager
    
    payload = SecureTokenManager.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "user_id": user.id,
            "refresh_ip": request.client.host if request.client else "unknown"
        },
        expires_delta=access_token_expires
    )
    
    # Add rate limit headers
    add_rate_limit_headers(response, rate_limit_info)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60
    }

@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key with enhanced security"""
    # Check if user has API access
    from .dependencies import check_subscription_feature
    if not check_subscription_feature(current_user, "api_access"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access not available in your subscription tier"
        )
    
    # Generate secure API key
    api_key, key_hash = SecureAPIKeyManager.generate_api_key()
    key_prefix = api_key[:12]  # Store prefix for display (osk_xxxxxxxx)
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Validate and serialize allowed IPs and permissions
    allowed_ips_json = None
    if key_data.allowed_ips:
        allowed_ips_json = json.dumps(key_data.allowed_ips)
    
    permissions_json = None
    if key_data.permissions:
        permissions_json = json.dumps(key_data.permissions)
    
    # Create key record
    db_key = APIKey(
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        user_id=current_user.id,
        expires_at=expires_at,
        allowed_ips=allowed_ips_json,
        permissions=permissions_json
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    # Parse JSON fields for response
    response_data = {
        "id": db_key.id,
        "key": api_key,  # Only returned on creation
        "key_prefix": db_key.key_prefix,
        "name": db_key.name,
        "is_active": db_key.is_active,
        "created_at": db_key.created_at,
        "expires_at": db_key.expires_at,
        "rate_limit": db_key.rate_limit,
        "allowed_ips": json.loads(db_key.allowed_ips) if db_key.allowed_ips else None,
        "permissions": json.loads(db_key.permissions) if db_key.permissions else None,
    }
    
    return APIKeyCreateResponse(**response_data)

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's API keys (without showing actual keys)"""
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    
    # Parse JSON fields and prepare response
    response_keys = []
    for key in keys:
        key_data = {
            "id": key.id,
            "key_prefix": key.key_prefix,
            "name": key.name,
            "is_active": key.is_active,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
            "last_used": key.last_used,
            "rate_limit": key.rate_limit,
            "allowed_ips": json.loads(key.allowed_ips) if key.allowed_ips else None,
            "permissions": json.loads(key.permissions) if key.permissions else None,
        }
        response_keys.append(APIKeyResponse(**key_data))
    
    return response_keys

# OAuth routes
@router.get("/oauth/{provider}/url")
async def get_oauth_url(
    provider: str,
    redirect_url: Optional[str] = None
):
    """Get OAuth authorization URL for provider"""
    oauth_provider = get_oauth_provider(provider)
    
    # Generate secure state
    state_token = OAuthStateManager.create_state_token(provider, redirect_url)
    auth_url = await oauth_provider.get_authorization_url(state_token)
    
    return {
        "auth_url": auth_url,
        "state": state_token
    }

@router.post("/oauth/{provider}/callback", response_model=Token)
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback and create/login user"""
    # Validate state
    state_data = OAuthStateManager.validate_state_token(state)
    if state_data["provider"] != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State provider mismatch"
        )
    
    # Get OAuth provider
    oauth_provider = get_oauth_provider(provider)
    
    # Exchange code for token
    access_token = await oauth_provider.exchange_code_for_token(code, state)
    
    # Get user info
    user_info = await oauth_provider.get_user_info(access_token)
    
    # Find or create user
    user = db.query(User).filter(User.email == user_info.email).first()
    
    if not user:
        # Create new user from OAuth info
        user = User(
            username=user_info.username or f"{provider}_{user_info.provider_id}",
            email=user_info.email,
            full_name=user_info.name,
            hashed_password=get_password_hash(f"oauth_{user_info.provider_id}_{user_info.provider}"),
            subscription_tier="free",
            api_calls_limit=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    jwt_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "oauth_provider": provider
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "expires_in": 30 * 60
    }

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password with validation"""
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    try:
        new_hashed_password = get_password_hash(new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Update password
    current_user.hashed_password = new_hashed_password
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/password-strength")
async def check_password_strength(password: str):
    """Check password strength without storing it"""
    is_valid, message = PasswordValidator.validate_password(password)
    entropy = PasswordValidator.calculate_entropy(password)
    
    return {
        "is_valid": is_valid,
        "message": message,
        "entropy_bits": round(entropy, 1),
        "strength": "weak" if entropy < 40 else "medium" if entropy < 60 else "strong"
    }