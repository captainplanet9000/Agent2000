"""
Custom exception classes and error handling utilities for the Agent2000 application.
"""
from typing import Any, Dict, Optional, Type, TypeVar, Union

# Type variable for exception classes
E = TypeVar('E', bound='BaseError')

class BaseError(Exception):
    """Base class for all custom exceptions in the application."""
    
    def __init__(
        self, 
        message: str = "An error occurred",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize the error.
        
        Args:
            message: Human-readable error message
            code: Error code for programmatic error handling
            details: Additional error details
            cause: The original exception that caused this error
        """
        self.message = message
        self.code = code or "internal_error"
        self.details = details or {}
        self.cause = cause
        
        # Store the cause as __cause__ for Python's exception chaining
        if cause is not None:
            self.__cause__ = cause
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for serialization."""
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details,
                'type': self.__class__.__name__
            }
        }
    
    @classmethod
    def from_exception(
        cls: Type[E], 
        exc: Exception, 
        message: Optional[str] = None,
        code: Optional[str] = None,
        **details: Any
    ) -> E:
        """Create an error from an existing exception."""
        return cls(
            message=message or str(exc),
            code=code or getattr(exc, 'code', None) or 'internal_error',
            details={
                **getattr(exc, 'details', {}),
                **details
            },
            cause=exc
        )


class ConfigurationError(BaseError):
    """Raised when there is a configuration error."""
    def __init__(self, message: str = "Configuration error", **kwargs: Any) -> None:
        super().__init__(message, code="configuration_error", **kwargs)


class ValidationError(BaseError):
    """Raised when validation of input data fails."""
    def __init__(self, message: str = "Validation error", **kwargs: Any) -> None:
        super().__init__(message, code="validation_error", **kwargs)


class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, code="authentication_error", **kwargs)


class AuthorizationError(BaseError):
    """Raised when a user is not authorized to perform an action."""
    def __init__(self, message: str = "Not authorized", **kwargs: Any) -> None:
        super().__init__(message, code="authorization_error", **kwargs)


class NotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str = "resource", **kwargs: Any) -> None:
        super().__init__(f"{resource} not found", code="not_found", **kwargs)


class RateLimitError(BaseError):
    """Raised when a rate limit is exceeded."""
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        retry_after: Optional[float] = None,
        limit: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialize the rate limit error.
        
        Args:
            message: Error message
            retry_after: Number of seconds after which to retry
            limit: The rate limit that was exceeded
            **kwargs: Additional arguments for BaseError
        """
        details = kwargs.pop('details', {})
        if retry_after is not None:
            details['retry_after'] = retry_after
        if limit is not None:
            details['limit'] = limit
            
        super().__init__(
            message=message,
            code='rate_limit_exceeded',
            details=details,
            **kwargs
        )


class TimeoutError(BaseError):
    """Raised when an operation times out."""
    def __init__(self, message: str = "Operation timed out", **kwargs: Any) -> None:
        super().__init__(message, code="timeout_error", **kwargs)


class NetworkError(BaseError):
    """Raised when a network-related error occurs."""
    def __init__(self, message: str = "Network error occurred", **kwargs: Any) -> None:
        super().__init__(message, code="network_error", **kwargs)


class ServiceUnavailableError(BaseError):
    """Raised when a required service is unavailable."""
    def __init__(self, service: str = "service", **kwargs: Any) -> None:
        super().__init__(
            f"{service} is currently unavailable", 
            code="service_unavailable", 
            **kwargs
        )


def handle_error(
    error: Exception, 
    default_message: str = "An unexpected error occurred",
    **context: Any
) -> BaseError:
    """Handle an exception and return an appropriate BaseError.
    
    Args:
        error: The exception to handle
        default_message: Default message if none can be derived from the error
        **context: Additional context to include in the error details
        
    Returns:
        An appropriate BaseError subclass
    """
    if isinstance(error, BaseError):
        # If it's already one of our custom errors, just return it
        return error
    
    # Map standard exceptions to our custom errors
    if isinstance(error, TimeoutError):
        return TimeoutError(str(error) or default_message, **context)
    
    if isinstance(error, (ConnectionError, OSError)):
        return NetworkError(str(error) or "Network operation failed", **context)
    
    if isinstance(error, (ValueError, TypeError, AttributeError)):
        return ValidationError(str(error) or "Invalid data provided", **context)
    
    if isinstance(error, ImportError):
        return ConfigurationError(
            f"Failed to import required module: {str(error) or 'Unknown module'}",
            **context
        )
    
    # Fall back to a generic error
    return BaseError(
        message=str(error) if str(error) else default_message,
        details={
            'error_type': error.__class__.__name__,
            **context
        },
        cause=error
    )
