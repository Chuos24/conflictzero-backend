import redis
from typing import Optional, Any
import json
import pickle
from .config import settings
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis cache manager for Conflict Zero."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration (seconds)."""
        if not self.redis_client:
            return False
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, expire, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        if not self.redis_client:
            return 0
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache."""
        if not self.redis_client:
            return None
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get_json error: {e}")
            return None
    
    def set_json(self, key: str, value: dict, expire: int = 3600) -> bool:
        """Set JSON value in cache."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set_json error: {e}")
            return False
    
    def flush_all(self) -> bool:
        """Clear all cache (use with caution)."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False

# Global cache instance
cache = CacheManager()

# Decorator for function result caching
def cached(timeout: int = 3600, key_prefix: str = "cache"):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
