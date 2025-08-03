#!/usr/bin/env python3
"""
Authentication dependencies for FastAPI
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from .models import User, APIKey, SubscriptionTier
from .security_enhanced import verify_token, api_key_manager
from .rate_limiter import check_api_rate_limit
from ..database import get_db

logger = logging.getLogger(__name__)

# Security scheme for Bearer tokens (JWT and API keys)
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Extract and validate current user from JWT token or API key"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    
    # Check if it's an API key (starts with our prefix)
    if token.startswith("osk_"):
        return await get_user_from_api_key(token, db, request)
    else:
        return await get_user_from_jwt(token, db)

async def get_user_from_jwt(token: str, db: Session) -> User:
    """Extract user from JWT access token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify JWT token
    payload = verify_token(token, expected_type="access")
    if not payload:
        raise credentials_exception
    
    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked"
        )
    
    # Reset API calls daily
    if user.last_api_reset.date() < datetime.utcnow().date():
        user.api_calls_used = 0
        user.last_api_reset = datetime.utcnow()
        db.commit()
    
    return user

async def get_user_from_api_key(api_key: str, db: Session, request: Request) -> User:
    """Extract user from API key with rate limiting"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract key prefix for lookup
    key_prefix = api_key_manager.extract_key_prefix(api_key)
    
    # Find API key in database
    api_key_record = db.query(APIKey).filter(
        APIKey.key_prefix == key_prefix,
        APIKey.is_active == True
    ).first()
    
    if not api_key_record:
        raise credentials_exception
    
    # Verify the full API key against stored hash
    if not api_key_manager.verify_api_key(api_key, api_key_record.key_hash):
        logger.warning(f"Invalid API key attempted: {key_prefix}")
        raise credentials_exception
    
    # Check expiration
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    # Get the user
    user = db.query(User).filter(User.id == api_key_record.user_id).first()
    if not user or not user.is_active:
        raise credentials_exception
    
    # Apply rate limiting based on user's subscription tier
    tier_names = {
        SubscriptionTier.FREE: "free",
        SubscriptionTier.PRO: "pro", 
        SubscriptionTier.ENTERPRISE: "enterprise"
    }
    
    user_tier = tier_names.get(user.subscription_tier, "free")
    
    # Check API rate limit
    try:
        await check_api_rate_limit(request, user_tier)
    except HTTPException as e:
        logger.info(f"API rate limit exceeded for user {user.id} ({user_tier})")
        raise e
    
    # Update last used timestamp
    api_key_record.last_used = datetime.utcnow()
    db.commit()
    
    # Store API key info in request for logging
    request.state.api_key_used = True
    request.state.api_key_prefix = key_prefix
    
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

def require_subscription_tier(minimum_tier: SubscriptionTier):
    """Dependency factory to require minimum subscription tier"""
    async def check_subscription(current_user: User = Depends(get_current_user)) -> User:
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PRO: 1,
            SubscriptionTier.ENTERPRISE: 2
        }
        
        user_tier_level = tier_hierarchy.get(current_user.subscription_tier, 0)
        required_tier_level = tier_hierarchy.get(minimum_tier, 2)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Requires {minimum_tier.value} subscription or higher"
            )
        
        return current_user
    
    return check_subscription

# Convenience dependencies for different subscription levels
require_pro = require_subscription_tier(SubscriptionTier.PRO)
require_enterprise = require_subscription_tier(SubscriptionTier.ENTERPRISE)

async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, db, credentials)
    except HTTPException:
        # Authentication failed, but that's okay for optional auth
        return None

async def rate_limit_check(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
) -> None:
    """Check rate limits for the current user"""
    if not current_user:
        # Anonymous users get minimal rate limit via IP-based limiting
        return
    
    # Check daily API call limit
    if current_user.api_calls_used >= current_user.api_calls_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily API limit exceeded ({current_user.api_calls_limit} calls)"
        )
    
    # Increment API calls (done after successful response in production)
    current_user.api_calls_used += 1

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
    # Convert enum to string for lookup
    tier_name = user.subscription_tier.value if isinstance(user.subscription_tier, SubscriptionTier) else user.subscription_tier
    tier_features = TIER_LIMITS.get(tier_name, {}).get("features", [])
    return feature in tier_features