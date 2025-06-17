"""
Rate limiting utilities for API requests and other operations.
"""
import time
import math
from typing import Dict, Optional, Tuple, Union, Callable, Any
from threading import Lock
from collections import deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A thread-safe rate limiter that enforces rate limits for operations.
    
    This class can be used to limit the rate of operations, such as API calls,
    to stay within defined limits. It supports both request-based and token-based
    rate limiting.
    """
    
    def __init__(
        self,
        max_requests: int = 60,
        per_seconds: float = 60.0,
        max_tokens: Optional[int] = None,
        tokens_per_request: int = 1,
        token_refill_rate: float = 1.0,
        max_token_capacity: Optional[int] = None,
    ):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window.
            per_seconds: Time window in seconds for the rate limit.
            max_tokens: Maximum number of tokens in the token bucket (None for no token bucket).
            tokens_per_request: Number of tokens consumed per request.
            token_refill_rate: Number of tokens added per second.
            max_token_capacity: Maximum capacity of the token bucket.
        """
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.tokens_per_request = tokens_per_request
        
        # Request-based rate limiting
        self.requests = deque()
        self.lock = Lock()
        
        # Token bucket rate limiting
        self.use_token_bucket = max_tokens is not None
        if self.use_token_bucket:
            self.max_tokens = max_tokens
            self.tokens = max_tokens
            self.token_refill_rate = token_refill_rate
            self.max_token_capacity = max_token_capacity or max_tokens
            self.last_refill_time = time.time()
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on the time elapsed since the last refill."""
        if not self.use_token_bucket:
            return
            
        current_time = time.time()
        time_elapsed = current_time - self.last_refill_time
        
        if time_elapsed > 0:
            tokens_to_add = time_elapsed * self.token_refill_rate
            self.tokens = min(self.max_token_capacity, self.tokens + tokens_to_add)
            self.last_refill_time = current_time
    
    def _has_tokens(self, tokens_needed: int = 1) -> bool:
        """Check if there are enough tokens available."""
        if not self.use_token_bucket:
            return True
            
        self._refill_tokens()
        return self.tokens >= tokens_needed
    
    def _consume_tokens(self, tokens: int = 1) -> bool:
        """Consume tokens if available."""
        if not self.use_token_bucket:
            return True
            
        if self._has_tokens(tokens):
            self.tokens -= tokens
            return True
        return False
    
    def _cleanup_old_requests(self, current_time: float) -> None:
        """Remove old requests that are outside the time window."""
        while self.requests and (current_time - self.requests[0] > self.per_seconds):
            self.requests.popleft()
    
    def _is_request_allowed(self) -> bool:
        """Check if a new request is allowed based on the rate limit."""
        current_time = time.time()
        
        with self.lock:
            self._cleanup_old_requests(current_time)
            
            # Check request-based rate limit
            if len(self.requests) >= self.max_requests:
                return False
                
            # Check token bucket if enabled
            if self.use_token_bucket and not self._consume_tokens(self.tokens_per_request):
                return False
                
            # Record the request
            self.requests.append(current_time)
            return True
    
    def _get_wait_time(self) -> float:
        """Calculate how long to wait before the next request is allowed."""
        current_time = time.time()
        
        with self.lock:
            self._cleanup_old_requests(current_time)
            
            # Calculate wait time based on request rate
            wait_time = 0.0
            
            if self.requests:
                time_since_oldest = current_time - self.requests[0]
                if len(self.requests) >= self.max_requests:
                    wait_time = max(wait_time, self.per_seconds - time_since_oldest)
            
            # Calculate wait time based on token bucket
            if self.use_token_bucket:
                self._refill_tokens()
                if self.tokens < self.tokens_per_request:
                    tokens_needed = self.tokens_per_request - self.tokens
                    wait_time = max(wait_time, tokens_needed / self.token_refill_rate)
            
            return max(0.0, wait_time)
    
    def wait(self) -> None:
        """
        Wait until a new request is allowed based on the rate limit.
        
        This will block the current thread until the rate limit allows another request.
        """
        while True:
            if self._is_request_allowed():
                return
                
            wait_time = self._get_wait_time()
            if wait_time > 0:
                time.sleep(wait_time)
    
    def acquire(self, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token from the rate limiter.
        
        Args:
            block: If True, block until the request can be made or timeout occurs.
            timeout: Maximum time to wait in seconds (None for no timeout).
            
        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        if block:
            if timeout is None:
                self.wait()
                return True
            else:
                end_time = time.time() + timeout
                while time.time() < end_time:
                    if self._is_request_allowed():
                        return True
                    time.sleep(min(0.1, end_time - time.time()))
                return False
        else:
            return self._is_request_allowed()
    
    def release(self) -> None:
        """Release a request slot (useful for retries or cancellations)."""
        with self.lock:
            if self.requests:
                self.requests.pop()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current rate limiter statistics.
        
        Returns:
            Dict containing rate limiter statistics.
        """
        current_time = time.time()
        
        with self.lock:
            self._cleanup_old_requests(current_time)
            stats = {
                'max_requests': self.max_requests,
                'requests_in_window': len(self.requests),
                'window_seconds': self.per_seconds,
                'time_until_next_window': max(0.0, (self.requests[0] + self.per_seconds - current_time) if self.requests else 0.0),
            }
            
            if self.use_token_bucket:
                self._refill_tokens()
                stats.update({
                    'tokens': self.tokens,
                    'max_tokens': self.max_token_capacity,
                    'token_refill_rate': self.token_refill_rate,
                    'tokens_per_request': self.tokens_per_request,
                })
            
            return stats

# Global rate limiters
_rate_limiters: Dict[str, RateLimiter] = {}

def get_rate_limiter(
    name: str,
    max_requests: int = 60,
    per_seconds: float = 60.0,
    max_tokens: Optional[int] = None,
    tokens_per_request: int = 1,
    token_refill_rate: float = 1.0,
    max_token_capacity: Optional[int] = None,
) -> RateLimiter:
    """
    Get or create a named rate limiter.
    
    Args:
        name: Unique name for the rate limiter.
        max_requests: Maximum number of requests allowed in the time window.
        per_seconds: Time window in seconds for the rate limit.
        max_tokens: Maximum number of tokens in the token bucket (None for no token bucket).
        tokens_per_request: Number of tokens consumed per request.
        token_refill_rate: Number of tokens added per second.
        max_token_capacity: Maximum capacity of the token bucket.
        
    Returns:
        RateLimiter: The rate limiter instance.
    """
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(
            max_requests=max_requests,
            per_seconds=per_seconds,
            max_tokens=max_tokens,
            tokens_per_request=tokens_per_request,
            token_refill_rate=token_refill_rate,
            max_token_capacity=max_token_capacity,
        )
    return _rate_limiters[name]

# Export the RateLimiter class and get_rate_limiter function
__all__ = ['RateLimiter', 'get_rate_limiter']
