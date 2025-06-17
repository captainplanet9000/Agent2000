"""
Python helpers package for the Agent2000 application.
This package contains various utility modules used throughout the application.
"""

# First import runtime to get its __all__
from . import runtime

# Then import everything else
from .dotenv import load_dotenv
from .rate_limiter import RateLimiter
from .extract_tools import *
from .files import *
from .errors import *
from .history import *
from .tokens import *

# Get the runtime exports
runtime_exports = getattr(runtime, '__all__', [])

# Define our exports
exports = [
    # From dotenv
    'load_dotenv',
    
    # From rate_limiter
    'RateLimiter',
    
    # From extract_tools
    'extract_json_from_text',
    'extract_urls',
    'extract_emails',
    'extract_phone_numbers',
    'extract_hashtags',
    'extract_mentions',
    'extract_file_extension',
    'extract_metadata',
    
    # From files
    'ensure_dir',
    'file_exists',
    'dir_exists',
    'get_file_size',
    'get_file_hash',
    'get_mime_type',
    'read_file_chunks',
    'write_file',
    'copy_file',
    'delete_file',
    'list_files',
    'get_file_info',
    
    # From errors
    'BaseError',
    'ConfigurationError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'RateLimitError',
    'TimeoutError',
    'NetworkError',
    'ServiceUnavailableError',
    'handle_error',
    
    # From history
    'HistoryEntry',
    'HistoryConfig',
    'HistoryManager',
    'get_default_history_manager',
    
    # From tokens
    'TokenUsageStats',
    'count_tokens',
    'estimate_tokens',
    'truncate_to_token_limit',
    'TokenWindow',
    'TokenBucket',
    'tokenize_json',
    'detokenize_json',
    'get_model_context_size',
]

# Add runtime exports
for name in runtime_exports:
    if name not in exports:  # Avoid duplicates
        exports.append(name)

# Set __all__
__all__ = exports

# Clean up
import sys
del sys.modules[__name__].runtime_exports
del sys.modules[__name__].exports
