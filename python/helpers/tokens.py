"""
Token management and utilities for the Agent2000 application.

This module provides functionality for working with tokens, including:
- Token counting and estimation
- Token encoding/decoding
- Token window management
- Token-based rate limiting
"""
from typing import Dict, List, Optional, Tuple, Union, Any, Callable, TypeVar, Generic, cast
import re
import tiktoken
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import time

# Type variable for generic functions
T = TypeVar('T')

# Default tokenizer to use (can be overridden)
DEFAULT_ENCODING = "cl100k_base"

class TokenUsageStats:
    """Tracks token usage statistics."""
    
    def __init__(self):
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.requests: int = 0
    
    def update(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Update the token counts."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.requests += 1
    
    def to_dict(self) -> Dict[str, int]:
        """Convert the stats to a dictionary."""
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'requests': self.requests
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'TokenUsageStats':
        """Create a TokenUsageStats instance from a dictionary."""
        stats = cls()
        stats.prompt_tokens = data.get('prompt_tokens', 0)
        stats.completion_tokens = data.get('completion_tokens', 0)
        stats.total_tokens = data.get('total_tokens', 0)
        stats.requests = data.get('requests', 0)
        return stats


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count the number of tokens in a text string.
    
    Args:
        text: The text to count tokens for
        model: The model to use for tokenization
        
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fall back to default encoding if model not found
        encoding = tiktoken.get_encoding(DEFAULT_ENCODING)
    
    return len(encoding.encode(text))


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.
    
    This is a faster but less accurate method than count_tokens.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    # Rough estimate: 1 token ~= 4 chars in English
    return (len(text) + 3) // 4


def truncate_to_token_limit(
    text: str, 
    max_tokens: int, 
    model: str = "gpt-4",
    from_end: bool = False
) -> str:
    """Truncate text to a maximum number of tokens.
    
    Args:
        text: The text to truncate
        max_tokens: Maximum number of tokens allowed
        model: The model to use for tokenization
        from_end: If True, truncate from the end instead of the beginning
        
    Returns:
        Truncated text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding(DEFAULT_ENCODING)
    
    tokens = encoding.encode(text)
    
    if len(tokens) <= max_tokens:
        return text
    
    if from_end:
        truncated = tokens[-max_tokens:]
    else:
        truncated = tokens[:max_tokens]
    
    return encoding.decode(truncated)


class TokenWindow:
    """Manages a sliding window of tokens with configurable limits."""
    
    def __init__(
        self, 
        max_tokens: int,
        max_items: Optional[int] = None,
        model: str = "gpt-4"
    ):
        """Initialize the token window.
        
        Args:
            max_tokens: Maximum number of tokens allowed in the window
            max_items: Optional maximum number of items in the window
            model: The model to use for token counting
        """
        self.max_tokens = max_tokens
        self.max_items = max_items
        self.model = model
        self.items: List[Tuple[str, int]] = []  # (content, token_count)
        self.total_tokens = 0
    
    def add(self, content: str) -> Tuple[bool, int]:
        """Add content to the window.
        
        Args:
            content: The content to add
            
        Returns:
            Tuple of (success, tokens_added)
        """
        token_count = count_tokens(content, self.model)
        
        # Check if we can add this without exceeding limits
        if self.max_items is not None and len(self.items) >= self.max_items:
            return False, 0
            
        if self.total_tokens + token_count > self.max_tokens:
            return False, 0
        
        self.items.append((content, token_count))
        self.total_tokens += token_count
        return True, token_count
    
    def pop(self) -> Optional[str]:
        """Remove and return the oldest item from the window.
        
        Returns:
            The removed content, or None if window is empty
        """
        if not self.items:
            return None
            
        content, token_count = self.items.pop(0)
        self.total_tokens -= token_count
        return content
    
    def clear(self) -> None:
        """Clear all items from the window."""
        self.items = []
        self.total_tokens = 0
    
    def get_contents(self) -> str:
        """Get all window contents as a single string."""
        return "\n".join(item[0] for item in self.items)
    
    def is_full(self) -> bool:
        """Check if the window is full."""
        if self.max_items is not None and len(self.items) >= self.max_items:
            return True
        return self.total_tokens >= self.max_tokens


class TokenBucket:
    """Implements the token bucket algorithm for rate limiting."""
    
    def __init__(self, tokens_per_interval: float, interval: float = 60.0):
        """Initialize the token bucket.
        
        Args:
            tokens_per_interval: Number of tokens to add per interval
            interval: Time interval in seconds between token additions
        """
        self.tokens_per_interval = tokens_per_interval
        self.interval = interval
        self.tokens = tokens_per_interval
        self.last_update = time.time()
        self.lock = False  # Simple lock to prevent race conditions
    
    def _update_tokens(self) -> None:
        """Update the token count based on elapsed time."""
        now = time.time()
        time_passed = now - self.last_update
        
        if time_passed > 0:
            # Add tokens based on time passed
            self.tokens += (time_passed / self.interval) * self.tokens_per_interval
            self.tokens = min(self.tokens, self.tokens_per_interval)
            self.last_update = now
    
    def consume(self, tokens: float = 1.0) -> bool:
        """Attempt to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        # Simple locking to prevent race conditions
        while self.lock:
            time.sleep(0.001)
        
        self.lock = True
        
        try:
            self._update_tokens()
            
            if tokens <= self.tokens:
                self.tokens -= tokens
                return True
            return False
        finally:
            self.lock = False
    
    def get_tokens(self) -> float:
        """Get the current number of tokens in the bucket."""
        self._update_tokens()
        return self.tokens


def tokenize_json(obj: Any) -> List[int]:
    """Tokenize a JSON-serializable object.
    
    Args:
        obj: The object to tokenize
        
    Returns:
        List of token IDs
    """
    # Convert to JSON string and count tokens
    json_str = json.dumps(obj, ensure_ascii=False)
    return list(tiktoken.get_encoding(DEFAULT_ENCODING).encode(json_str))


def detokenize_json(token_ids: List[int]) -> Any:
    """Convert token IDs back to a Python object.
    
    Args:
        token_ids: List of token IDs
        
    Returns:
        The decoded Python object
    """
    json_str = tiktoken.get_encoding(DEFAULT_ENCODING).decode(token_ids)
    return json.loads(json_str)


def get_model_context_size(model: str) -> int:
    """Get the context size (in tokens) for a given model.
    
    Args:
        model: The model name
        
    Returns:
        Context size in tokens
    """
    # Default to a reasonable value if model not found
    model_context_sizes = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "text-davinci-003": 4097,
        "text-davinci-002": 4097,
        "code-davinci-002": 8001,
    }
    
    return model_context_sizes.get(model, 4096)  # Default to 4K if unknown
