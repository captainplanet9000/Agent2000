"""
Environment variable management for Agent2000.
Provides functionality to load environment variables from .env files.
"""
import os
from typing import Optional, Dict, Any

def load_dotenv(filepath: Optional[str] = None, override: bool = False) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        filepath: Path to the .env file. If None, looks for .env in the current directory.
        override: Whether to override existing environment variables.
        
    Returns:
        bool: True if the file was loaded successfully, False otherwise.
    """
    if filepath is None:
        filepath = os.path.join(os.getcwd(), '.env')
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                    
                # Parse key-value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Set environment variable if not already set or if override is True
                    if override or key not in os.environ:
                        os.environ[key] = value
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return False

def get_env(key: str, default: Any = None) -> str:
    """
    Get an environment variable or return a default value.
    
    Args:
        key: The environment variable name.
        default: Default value to return if the variable is not set.
        
    Returns:
        The value of the environment variable or the default value.
    """
    return os.environ.get(key, default)

def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get an environment variable as a boolean.
    
    Args:
        key: The environment variable name.
        default: Default value to return if the variable is not set.
        
    Returns:
        The boolean value of the environment variable or the default value.
    """
    value = os.environ.get(key, '').lower()
    if value in ('true', '1', 't', 'y', 'yes'):
        return True
    elif value in ('false', '0', 'f', 'n', 'no'):
        return False
    return default

def get_env_int(key: str, default: int = 0) -> int:
    """
    Get an environment variable as an integer.
    
    Args:
        key: The environment variable name.
        default: Default value to return if the variable is not set or invalid.
        
    Returns:
        The integer value of the environment variable or the default value.
    """
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default

# Export commonly used functions
__all__ = ['load_dotenv', 'get_env', 'get_env_bool', 'get_env_int']

# For backward compatibility
load_dotenv = load_dotenv
