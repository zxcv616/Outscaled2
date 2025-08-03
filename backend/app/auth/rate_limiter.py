#!/usr/bin/env python3
"""
Rate limiting system for Outscaled.GG
Protects authentication endpoints from brute force attacks
"""

import time
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to in-memory if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis not available, using in-memory rate limiting")
    REDIS_AVAILABLE = False

class RateLimiter:
    """
    Rate limiting implementation with Redis support and in-memory fallback
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.redis_client = None
        self.memory_store = defaultdict(list)  # Fallback in-memory store
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                self.redis_client.ping()
                logger.info("Redis connected for rate limiting")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory store")
                self.redis_client = None
                
    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate a unique key for rate limiting"""
        return f"rate_limit:{endpoint}:{identifier}"
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        endpoint: str, 
        max_requests: int, 
        window_seconds: int
    ) -> Dict[str, Any]:
        """
        Check if request should be rate limited
        Returns dict with allowed status and metadata
        """
        key = self._get_key(identifier, endpoint)
        now = time.time()
        window_start = now - window_seconds
        
        if self.redis_client:
            return await self._check_redis(key, now, window_start, max_requests, window_seconds)
        else:
            return self._check_memory(key, now, window_start, max_requests, window_seconds)
    
    async def _check_redis(
        self, 
        key: str, 
        now: float, 
        window_start: float, 
        max_requests: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """Check rate limit using Redis"""
        try:
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            request_count = self.redis_client.zcard(key)
            
            if request_count >= max_requests:
                # Get oldest request time to calculate retry
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + window_seconds - now)
                else:
                    retry_after = window_seconds
                    
                return {
                    "allowed": False,
                    "limit": max_requests,
                    "remaining": 0,
                    "reset": int(now + retry_after),
                    "retry_after": retry_after
                }
            
            # Add current request
            self.redis_client.zadd(key, {str(now): now})
            self.redis_client.expire(key, window_seconds)
            
            return {
                "allowed": True,
                "limit": max_requests,
                "remaining": max_requests - request_count - 1,
                "reset": int(now + window_seconds)
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fall back to memory check
            return self._check_memory(key, now, window_start, max_requests, window_seconds)
    
    def _check_memory(
        self, 
        key: str, 
        now: float, 
        window_start: float, 
        max_requests: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """Check rate limit using in-memory store"""
        # Clean old entries
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key] 
            if timestamp > window_start
        ]
        
        request_count = len(self.memory_store[key])
        
        if request_count >= max_requests:
            # Calculate retry after
            oldest = min(self.memory_store[key]) if self.memory_store[key] else now
            retry_after = int(oldest + window_seconds - now)
            
            return {
                "allowed": False,
                "limit": max_requests,
                "remaining": 0,
                "reset": int(now + retry_after),
                "retry_after": retry_after
            }
        
        # Add current request
        self.memory_store[key].append(now)
        
        return {
            "allowed": True,
            "limit": max_requests,
            "remaining": max_requests - request_count - 1,
            "reset": int(now + window_seconds)
        }

# Rate limit configurations for different endpoints
RATE_LIMIT_CONFIG = {
    "login": {
        "max_requests": 5,
        "window_seconds": 300,  # 5 minutes
        "message": "Too many login attempts. Please try again later."
    },
    "register": {
        "max_requests": 3,
        "window_seconds": 3600,  # 1 hour
        "message": "Too many registration attempts. Please try again later."
    },
    "password_reset": {
        "max_requests": 3,
        "window_seconds": 3600,  # 1 hour
        "message": "Too many password reset attempts. Please try again later."
    },
    "api_free": {
        "max_requests": 60,
        "window_seconds": 60,  # 1 minute
        "message": "API rate limit exceeded. Please upgrade your plan."
    },
    "api_pro": {
        "max_requests": 300,
        "window_seconds": 60,  # 1 minute
        "message": "API rate limit exceeded."
    },
    "api_enterprise": {
        "max_requests": 1000,
        "window_seconds": 60,  # 1 minute
        "message": "API rate limit exceeded. Please contact support."
    }
}

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(
    request: Request,
    endpoint: str,
    identifier: Optional[str] = None,
    tier: str = "free"
) -> None:
    """
    Rate limiting middleware for FastAPI
    Raises HTTPException if rate limit exceeded
    """
    # Get client identifier (IP or user ID)
    if not identifier:
        identifier = request.client.host if request.client else "unknown"
    
    # Get rate limit config
    if endpoint.startswith("api_"):
        config_key = f"api_{tier}"
    else:
        config_key = endpoint
        
    config = RATE_LIMIT_CONFIG.get(config_key, RATE_LIMIT_CONFIG["api_free"])
    
    # Check rate limit
    result = await rate_limiter.check_rate_limit(
        identifier,
        endpoint,
        config["max_requests"],
        config["window_seconds"]
    )
    
    # Add rate limit headers to response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(result["limit"]),
        "X-RateLimit-Remaining": str(result["remaining"]),
        "X-RateLimit-Reset": str(result["reset"])
    }
    
    if not result["allowed"]:
        # Add retry header
        request.state.rate_limit_headers["Retry-After"] = str(result["retry_after"])
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=config["message"],
            headers=request.state.rate_limit_headers
        )

# Dependency for FastAPI routes
async def check_login_rate_limit(request: Request):
    """Rate limit check for login endpoint"""
    await rate_limit_middleware(request, "login")

async def check_register_rate_limit(request: Request):
    """Rate limit check for registration endpoint"""
    await rate_limit_middleware(request, "register")

async def check_api_rate_limit(request: Request, user_tier: str = "free"):
    """Rate limit check for API endpoints based on user tier"""
    await rate_limit_middleware(request, "api", tier=user_tier)

# IP-based rate limiting for anonymous users
class IPRateLimiter:
    """
    Specialized rate limiter for IP-based restrictions
    """
    
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_ips = defaultdict(int)
        
    def check_ip(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip not in self.blocked_ips
    
    def report_suspicious_activity(self, ip: str, activity_type: str):
        """Report suspicious activity from an IP"""
        self.suspicious_ips[ip] += 1
        
        # Auto-block after threshold
        if self.suspicious_ips[ip] >= 10:
            self.block_ip(ip, reason=f"Suspicious activity: {activity_type}")
    
    def block_ip(self, ip: str, reason: str, duration_hours: int = 24):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP blocked: {ip} - Reason: {reason}")
        
        # In production, store in Redis with expiration
        if rate_limiter.redis_client:
            key = f"blocked_ip:{ip}"
            rate_limiter.redis_client.setex(
                key, 
                timedelta(hours=duration_hours), 
                json.dumps({"reason": reason, "blocked_at": datetime.utcnow().isoformat()})
            )

# Global IP rate limiter
ip_limiter = IPRateLimiter()

# Middleware for adding rate limit headers to all responses
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit headers to response"""
    response = await call_next(request)
    
    # Add headers if they exist
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value
            
    return response

if __name__ == "__main__":
    # Test rate limiting
    import asyncio
    
    async def test_rate_limiting():
        limiter = RateLimiter()
        
        # Test multiple requests
        for i in range(7):
            result = await limiter.check_rate_limit(
                "test_user",
                "login",
                max_requests=5,
                window_seconds=60
            )
            
            print(f"Request {i+1}: Allowed={result['allowed']}, Remaining={result['remaining']}")
            
            if not result["allowed"]:
                print(f"Rate limited! Retry after {result['retry_after']} seconds")
                
            await asyncio.sleep(0.1)
    
    asyncio.run(test_rate_limiting())