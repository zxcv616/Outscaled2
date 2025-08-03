#!/usr/bin/env python3
"""
Authentication dependencies for FastAPI
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from .models import User, APIKey, TokenData
from .security import decode_token
from ..database import get_db

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# API Key scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if username is None or user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Check and reset API calls if needed
    if user.last_api_reset.date() < datetime.utcnow().date():
        user.api_calls_used = 0
        user.last_api_reset = datetime.utcnow()
        db.commit()
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_api_key_user(
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key"""
    if not api_key:
        return None
    
    # Find the API key in database
    key_record = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()
    
    if not key_record:
        return None
    
    # Check if key is expired
    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        return None
    
    # Update last used
    key_record.last_used = datetime.utcnow()
    db.commit()
    
    return key_record.user

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key_user: Optional[User] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from either JWT or API key (optional)"""
    # Try API key first
    if api_key_user:
        return api_key_user
    
    # Try JWT token
    if token:
        try:
            return await get_current_user(token, db)
        except HTTPException:
            pass
    
    return None

async def rate_limit_check(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> None:
    """Check rate limits for the current user"""
    if not current_user:
        # Anonymous users get minimal rate limit
        # TODO: Implement IP-based rate limiting
        return
    
    # Check daily API call limit
    if current_user.api_calls_used >= current_user.api_calls_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily API limit exceeded ({current_user.api_calls_limit} calls)"
        )
    
    # Increment API calls
    current_user.api_calls_used += 1
    # Note: In production, this should be done after successful response

# Subscription tier limits
TIER_LIMITS = {
    "free": {
        "daily_api_calls": 100,
        "predictions_per_request": 1,
        "historical_data_days": 30,
        "features": ["basic_predictions"]
    },
    "pro": {
        "daily_api_calls": 1000,
        "predictions_per_request": 5,
        "historical_data_days": 90,
        "features": ["basic_predictions", "prediction_curve", "advanced_stats"]
    },
    "enterprise": {
        "daily_api_calls": 10000,
        "predictions_per_request": 20,
        "historical_data_days": 365,
        "features": ["basic_predictions", "prediction_curve", "advanced_stats", "api_access", "webhooks"]
    }
}

def check_subscription_feature(user: User, feature: str) -> bool:
    """Check if user's subscription tier has access to a feature"""
    tier_features = TIER_LIMITS.get(user.subscription_tier, {}).get("features", [])
    return feature in tier_features