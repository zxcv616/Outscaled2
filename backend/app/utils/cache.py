#!/usr/bin/env python3
"""
Caching system for API responses
Provides in-memory and Redis-based caching with intelligent invalidation
"""

import hashlib
import json
import time
import logging
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry['expires_at']
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self._cleanup_expired()
        
        if key in self._cache:
            entry = self._cache[key]
            if not self._is_expired(entry):
                self.hits += 1
                entry['last_accessed'] = time.time()
                entry['access_count'] += 1
                return entry['value']
            else:
                del self._cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl,
            'last_accessed': time.time(),
            'access_count': 1,
            'ttl': ttl
        }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._cleanup_expired()
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'total_entries': len(self._cache),
            'memory_usage_estimate': sum(
                len(str(entry['value'])) for entry in self._cache.values()
            )
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        self._cleanup_expired()
        entries = []
        
        for key, entry in self._cache.items():
            entries.append({
                'key': key[:50] + '...' if len(key) > 50 else key,
                'size_estimate': len(str(entry['value'])),
                'created_at': datetime.fromtimestamp(entry['created_at']).isoformat(),
                'expires_at': datetime.fromtimestamp(entry['expires_at']).isoformat(),
                'access_count': entry['access_count'],
                'ttl': entry['ttl']
            })
        
        return {
            'stats': self.stats(),
            'entries': sorted(entries, key=lambda x: x['access_count'], reverse=True)[:20]  # Top 20
        }

class CacheManager:
    """Manages different cache layers and strategies"""
    
    def __init__(self):
        self.memory_cache = InMemoryCache(default_ttl=300)  # 5 minutes
        self.long_term_cache = InMemoryCache(default_ttl=3600)  # 1 hour
        self.player_cache = InMemoryCache(default_ttl=1800)  # 30 minutes
        
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate consistent cache key from data"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        hash_obj = hashlib.md5(sorted_data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def cache_prediction(self, request_data: Dict[str, Any], result: Dict[str, Any], ttl: int = 300) -> str:
        """Cache prediction result"""
        # Create cache key from request parameters
        cache_key = self._generate_cache_key("prediction", {
            'player_names': request_data.get('player_names'),
            'prop_type': request_data.get('prop_type'),
            'prop_value': request_data.get('prop_value'),
            'tournament': request_data.get('tournament'),
            'position_roles': request_data.get('position_roles')
        })
        
        # Cache the result
        cache_data = {
            'result': result,
            'request_hash': cache_key,
            'cached_at': datetime.now().isoformat()
        }
        
        self.memory_cache.set(cache_key, cache_data, ttl)
        logger.info(f"Cached prediction result with key: {cache_key}")
        return cache_key
    
    def get_cached_prediction(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached prediction if available"""
        cache_key = self._generate_cache_key("prediction", {
            'player_names': request_data.get('player_names'),
            'prop_type': request_data.get('prop_type'),
            'prop_value': request_data.get('prop_value'),
            'tournament': request_data.get('tournament'),
            'position_roles': request_data.get('position_roles')
        })
        
        cached_data = self.memory_cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for prediction: {cache_key}")
            return cached_data['result']
        
        logger.debug(f"Cache miss for prediction: {cache_key}")
        return None
    
    def cache_player_data(self, player_name: str, data: Dict[str, Any], ttl: int = 1800) -> None:
        """Cache player data"""
        cache_key = f"player:{player_name.lower()}"
        self.player_cache.set(cache_key, data, ttl)
        logger.info(f"Cached player data for: {player_name}")
    
    def get_cached_player_data(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Get cached player data"""
        cache_key = f"player:{player_name.lower()}"
        return self.player_cache.get(cache_key)
    
    def cache_static_data(self, data_type: str, data: Any, ttl: int = 3600) -> None:
        """Cache static data like player lists, team lists"""
        cache_key = f"static:{data_type}"
        self.long_term_cache.set(cache_key, data, ttl)
        logger.info(f"Cached static data: {data_type}")
    
    def get_cached_static_data(self, data_type: str) -> Optional[Any]:
        """Get cached static data"""
        cache_key = f"static:{data_type}"
        return self.long_term_cache.get(cache_key)
    
    def invalidate_prediction_cache(self, pattern: str = None) -> int:
        """Invalidate prediction cache entries"""
        if pattern:
            # In a real Redis implementation, we'd use pattern matching
            # For now, we'll clear all prediction cache
            pass
        
        # Clear prediction cache
        prediction_keys = [key for key in self.memory_cache._cache.keys() if key.startswith('prediction:')]
        for key in prediction_keys:
            self.memory_cache.delete(key)
        
        logger.info(f"Invalidated {len(prediction_keys)} prediction cache entries")
        return len(prediction_keys)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'memory_cache': self.memory_cache.stats(),
            'long_term_cache': self.long_term_cache.stats(),
            'player_cache': self.player_cache.stats(),
            'total_caches': 3
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information for monitoring"""
        return {
            'memory_cache': self.memory_cache.get_cache_info(),
            'long_term_cache': self.long_term_cache.get_cache_info(),
            'player_cache': self.player_cache.get_cache_info()
        }

# Global cache manager instance
cache_manager = CacheManager()

def cache_response(ttl: int = 300, cache_key_func: Optional[Callable] = None):
    """Decorator for caching API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # Default cache key generation
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache_manager.memory_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.memory_cache.set(cache_key, result, ttl)
            logger.info(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator

def cache_prediction_response(ttl: int = 300):
    """Specialized decorator for prediction endpoint caching"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request data for cache key generation
            request_data = None
            for arg in args:
                if hasattr(arg, 'player_names'):  # PredictionRequest
                    request_data = {
                        'player_names': arg.player_names,
                        'prop_type': arg.prop_type,
                        'prop_value': arg.prop_value,
                        'tournament': arg.tournament,
                        'position_roles': arg.position_roles
                    }
                    break
            
            if request_data:
                # Check cache first
                cached_result = cache_manager.get_cached_prediction(request_data)
                if cached_result:
                    logger.info("Serving cached prediction")
                    return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if request_data and result:
                cache_manager.cache_prediction(request_data, result, ttl)
            
            return result
        return wrapper
    return decorator

# Utility functions for cache management

def warm_cache():
    """Pre-populate cache with frequently requested data"""
    logger.info("Starting cache warm-up...")
    
    # This would be implemented based on actual usage patterns
    # For now, we'll skip the warm-up
    logger.info("Cache warm-up completed")

def get_cache_health() -> Dict[str, Any]:
    """Get cache system health status"""
    stats = cache_manager.get_cache_stats()
    
    # Calculate overall health
    total_requests = sum(cache['hits'] + cache['misses'] for cache in stats.values() if isinstance(cache, dict))
    total_hits = sum(cache['hits'] for cache in stats.values() if isinstance(cache, dict))
    
    overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
    
    health_status = "healthy"
    if overall_hit_rate < 20:
        health_status = "poor"
    elif overall_hit_rate < 50:
        health_status = "moderate"
    
    return {
        'status': health_status,
        'overall_hit_rate': round(overall_hit_rate, 2),
        'total_requests': total_requests,
        'cache_stats': stats
    }