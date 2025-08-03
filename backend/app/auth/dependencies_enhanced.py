#!/usr/bin/env python3
"""
Enhanced authentication dependencies with improved security
"""

import json
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from .models import User, APIKey, TokenData
from .security_enhanced import SecureTokenManager, SecureAPIKeyManager
from ..database_enhanced import get_db

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# API Key scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token with enhanced validation"""
    if not token:
        return None
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = SecureTokenManager.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    token_type: str = payload.get("type")
    
    if username is None or user_id is None or token_type != "access":
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

async def get_api_key_user(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key with enhanced security"""
    if not api_key:
        return None
    
    # Validate API key format
    if not api_key.startswith("osk_"):
        return None
    
    # Find the API key in database by hash
    # We need to hash the provided key and compare with stored hashes
    key_records = db.query(APIKey).filter(
        APIKey.is_active == True,
        APIKey.key_prefix == api_key[:12]  # First filter by prefix for performance
    ).all()
    
    valid_key_record = None
    for key_record in key_records:
        if SecureAPIKeyManager.verify_api_key(api_key, key_record.key_hash):
            valid_key_record = key_record
            break
    
    if not valid_key_record:
        return None
    
    # Check if key is expired
    if valid_key_record.expires_at and valid_key_record.expires_at < datetime.utcnow():
        return None
    
    # Check IP restrictions
    if valid_key_record.allowed_ips:
        allowed_ips = json.loads(valid_key_record.allowed_ips)
        client_ip = request.client.host if request.client else "unknown"
        
        # Get real IP considering proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        if client_ip not in allowed_ips and "0.0.0.0/0" not in allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key not authorized for this IP address"
            )
    
    # Update last used
    valid_key_record.last_used = datetime.utcnow()
    db.commit()
    
    return valid_key_record.user

async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    api_key_user: Optional[User] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from either JWT or API key (optional)"""
    # Try API key first (more specific)
    if api_key_user:
        return api_key_user
    
    # Try JWT token
    if token:
        try:
            return await get_current_user(token, db)
        except HTTPException:
            pass
    
    return None

async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Get current active user (required)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def rate_limit_check(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> None:
    """Enhanced rate limiting with user context"""
    from .rate_limiter import rate_limiter, RATE_LIMITS
    
    if not current_user:
        # Anonymous users get stricter limits
        config = RATE_LIMITS["api_general"]
        allowed, info = rate_limiter.check_rate_limit(
            request, 
            config["limit"] // 3,  # Reduced limit for anonymous users
            config["window"]
        )
    else:
        # Check daily API call limit
        if current_user.api_calls_used >= current_user.api_calls_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily API limit exceeded ({current_user.api_calls_limit} calls). "
                       f"Upgrade your subscription for higher limits."
            )
        
        # Check per-minute rate limit based on subscription tier
        tier_multipliers = {
            "free": 1,
            "pro": 2,
            "enterprise": 5
        }
        multiplier = tier_multipliers.get(current_user.subscription_tier, 1)
        
        config = RATE_LIMITS["api_general"]
        allowed, info = rate_limiter.check_rate_limit(
            request,
            config["limit"] * multiplier,
            config["window"],
            current_user.id
        )
    
    if not allowed:
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
            "Retry-After": str(info["window"])
        }
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {info['window']} seconds.",
            headers=headers
        )
    
    # Increment API calls for authenticated users
    if current_user:
        current_user.api_calls_used += 1

# Enhanced subscription tier limits
TIER_LIMITS = {
    "free": {
        "daily_api_calls": 100,
        "predictions_per_request": 1,
        "historical_data_days": 30,
        "rate_limit_multiplier": 1,
        "features": ["basic_predictions"],
        "max_api_keys": 1,
        "api_key_permissions": ["predictions:basic"]
    },
    "pro": {
        "daily_api_calls": 1000,
        "predictions_per_request": 5,
        "historical_data_days": 90,
        "rate_limit_multiplier": 2,
        "features": ["basic_predictions", "prediction_curve", "advanced_stats"],
        "max_api_keys": 5,
        "api_key_permissions": ["predictions:basic", "predictions:advanced", "history:read"]
    },
    "enterprise": {
        "daily_api_calls": 10000,
        "predictions_per_request": 20,
        "historical_data_days": 365,
        "rate_limit_multiplier": 5,
        "features": [
            "basic_predictions", "prediction_curve", "advanced_stats", 
            "api_access", "webhooks", "priority_support", "custom_models"
        ],
        "max_api_keys": 20,
        "api_key_permissions": [
            "predictions:basic", "predictions:advanced", "predictions:custom",
            "history:read", "history:write", "admin:read"
        ]
    }
}

def check_subscription_feature(user: User, feature: str) -> bool:
    """Check if user's subscription tier has access to a feature"""
    tier_features = TIER_LIMITS.get(user.subscription_tier, {}).get("features", [])
    return feature in tier_features

def check_api_key_permission(user: User, permission: str) -> bool:
    """Check if user's subscription tier allows specific API key permission"""
    tier_permissions = TIER_LIMITS.get(user.subscription_tier, {}).get("api_key_permissions", [])
    return permission in tier_permissions

def get_subscription_limits(user: User) -> dict:
    """Get subscription limits for user"""
    return TIER_LIMITS.get(user.subscription_tier, TIER_LIMITS["free"])

async def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def check_permission(
        current_user: User = Depends(get_current_active_user)
    ):
        if not check_api_key_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required. Upgrade your subscription."
            )
        return current_user
    
    return check_permission

# Common permission dependencies
require_basic_predictions = require_permission("predictions:basic")
require_advanced_predictions = require_permission("predictions:advanced")
require_history_read = require_permission("history:read")
require_admin_read = require_permission("admin:read")