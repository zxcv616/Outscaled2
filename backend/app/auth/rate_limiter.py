#!/usr/bin/env python3
"""
Redis-based rate limiting with IP tracking for authentication endpoints
"""

import redis
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
import os
from dotenv import load_dotenv

load_dotenv()

class RateLimiter:
    """Redis-based rate limiter with IP tracking and user-specific limits"""
    
    def __init__(self):
        # Redis connection with fallback to in-memory for development
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            print("Connected to Redis for rate limiting")
        except (redis.ConnectionError, redis.RedisError) as e:
            print(f"Redis connection failed, using in-memory fallback: {e}")
            self.use_redis = False
            self._memory_store = {}
    
    def _get_client_identifier(self, request: Request, user_id: Optional[int] = None) -> str:
        """Get unique identifier for rate limiting"""
        if user_id:
            return f"user:{user_id}"
        
        # Get real IP address considering proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _redis_check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis sliding window"""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(identifier, 0, window_start)
        
        # Count current requests
        pipe.zcard(identifier)
        
        # Add current request
        pipe.zadd(identifier, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(identifier, window_seconds + 10)
        
        results = pipe.execute()
        current_requests = results[1]
        
        allowed = current_requests < limit
        remaining = max(0, limit - current_requests - 1)
        
        # Calculate reset time
        oldest_entry = self.redis_client.zrange(identifier, 0, 0, withscores=True)
        if oldest_entry:
            reset_time = oldest_entry[0][1] + window_seconds
        else:
            reset_time = current_time + window_seconds
        
        return allowed, {
            "remaining": remaining,
            "limit": limit,
            "reset": int(reset_time),
            "window": window_seconds
        }
    
    def _memory_check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory store (fallback)"""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if identifier not in self._memory_store:
            self._memory_store[identifier] = []
        
        # Remove old entries
        self._memory_store[identifier] = [
            timestamp for timestamp in self._memory_store[identifier]
            if timestamp > window_start
        ]
        
        current_requests = len(self._memory_store[identifier])
        allowed = current_requests < limit
        
        if allowed:
            self._memory_store[identifier].append(current_time)
        
        remaining = max(0, limit - current_requests - (1 if allowed else 0))
        reset_time = current_time + window_seconds
        
        return allowed, {
            "remaining": remaining,
            "limit": limit,
            "reset": int(reset_time),
            "window": window_seconds
        }
    
    def check_rate_limit(
        self, 
        request: Request, 
        limit: int, 
        window_seconds: int = 60,
        user_id: Optional[int] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits"""
        identifier = self._get_client_identifier(request, user_id)
        
        if self.use_redis:
            return self._redis_check_rate_limit(identifier, limit, window_seconds)
        else:
            return self._memory_check_rate_limit(identifier, limit, window_seconds)
    
    def get_rate_limit_info(self, request: Request, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get current rate limit information without incrementing"""
        identifier = self._get_client_identifier(request, user_id)
        
        if self.use_redis:
            current_time = time.time()
            current_requests = self.redis_client.zcard(identifier)
            return {
                "current_requests": current_requests,
                "identifier": identifier
            }
        else:
            current_time = time.time()
            if identifier in self._memory_store:
                # Clean old entries for accurate count
                window_start = current_time - 60
                self._memory_store[identifier] = [
                    timestamp for timestamp in self._memory_store[identifier]
                    if timestamp > window_start
                ]
                current_requests = len(self._memory_store[identifier])
            else:
                current_requests = 0
            
            return {
                "current_requests": current_requests,
                "identifier": identifier
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limiting configurations for different endpoints
RATE_LIMITS = {
    "auth_login": {"limit": 5, "window": 300},      # 5 attempts per 5 minutes
    "auth_register": {"limit": 3, "window": 3600},  # 3 registrations per hour
    "auth_refresh": {"limit": 10, "window": 300},   # 10 refreshes per 5 minutes
    "auth_password_reset": {"limit": 3, "window": 3600},  # 3 resets per hour
    "api_general": {"limit": 60, "window": 60},     # 60 requests per minute
    "api_prediction": {"limit": 30, "window": 60},  # 30 predictions per minute
}

class RateLimitDependency:
    """FastAPI dependency for rate limiting"""
    
    def __init__(self, endpoint_type: str):
        self.endpoint_type = endpoint_type
        self.config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS["api_general"])
    
    async def __call__(self, request: Request, user_id: Optional[int] = None):
        """Check rate limit and raise HTTPException if exceeded"""
        allowed, info = rate_limiter.check_rate_limit(
            request, 
            self.config["limit"], 
            self.config["window"],
            user_id
        )
        
        if not allowed:
            # Add rate limit headers
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
        
        # Add rate limit info to response headers (handled by middleware)
        request.state.rate_limit_info = info
        return info

# Convenience functions for common endpoints
login_rate_limit = RateLimitDependency("auth_login")
register_rate_limit = RateLimitDependency("auth_register")
refresh_rate_limit = RateLimitDependency("auth_refresh")
password_reset_rate_limit = RateLimitDependency("auth_password_reset")
api_rate_limit = RateLimitDependency("api_general")
prediction_rate_limit = RateLimitDependency("api_prediction")

def add_rate_limit_headers(response, rate_limit_info: Dict[str, Any]):
    """Add rate limit headers to response"""
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
    return response