"""
Runtime utilities for Agent2000.
Provides platform-independent runtime information and utilities.
"""
import os
import sys
import platform
import subprocess
from typing import Optional, Dict, Any, List, Tuple, Union

# Platform detection
IS_WINDOWS = os.name == 'nt'
IS_LINUX = os.name == 'posix' and 'linux' in sys.platform.lower()
IS_MAC = os.name == 'posix' and 'darwin' in sys.platform.lower()
IS_POSIX = os.name == 'posix'

# Python version info
PYTHON_VERSION = sys.version_info
PYTHON_VERSION_STR = f"{PYTHON_VERSION.major}.{PYTHON_VERSION.minor}.{PYTHON_VERSION.micro}"

# Platform info
PLATFORM = platform.system().lower()
PLATFORM_RELEASE = platform.release()
PLATFORM_VERSION = platform.version()

# CPU info
CPU_COUNT = os.cpu_count() or 1

# Memory info (in bytes)
MEMORY_TOTAL: Optional[int] = None
MEMORY_AVAILABLE: Optional[int] = None

try:
    if IS_WINDOWS:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        MEMORYSTATUS = ctypes.wintypes._MEMORYSTATUSEX()
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(MEMORYSTATUS))
        MEMORY_TOTAL = getattr(MEMORYSTATUS, 'ullTotalPhys', None)
        MEMORY_AVAILABLE = getattr(MEMORYSTATUS, 'ullAvailPhys', None)
    elif IS_LINUX or IS_MAC:
        import resource
        MEMORY_TOTAL = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # Total physical memory
        MEMORY_AVAILABLE = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_AVPHYS_PAGES')  # Available physical memory
except Exception:
    pass  # Ignore errors in memory detection

def get_platform_info() -> Dict[str, Any]:
    """
    Get detailed platform information.
    
    Returns:
        Dict containing platform information.
    """
    return {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation(),
        'python_compiler': platform.python_compiler(),
        'architecture': platform.architecture(),
        'cpu_count': CPU_COUNT,
        'memory_total': MEMORY_TOTAL,
        'memory_available': MEMORY_AVAILABLE,
    }

def is_program_installed(program: str) -> bool:
    """
    Check if a program is installed and available in the system PATH.
    
    Args:
        program: The name of the program to check.
        
    Returns:
        bool: True if the program is installed, False otherwise.
    """
    try:
        if IS_WINDOWS:
            cmd = ['where', program]
        else:
            cmd = ['which', program]
            
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def run_command(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    shell: bool = False,
    capture_output: bool = True,
    check: bool = False,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.
    
    Args:
        command: The command to run as a string or list of strings.
        cwd: Working directory for the command.
        env: Environment variables to use.
        shell: Whether to use the shell to execute the command.
        capture_output: Whether to capture stdout and stderr.
        check: If True, raises CalledProcessError if the command fails.
        **kwargs: Additional arguments to subprocess.run().
        
    Returns:
        subprocess.CompletedProcess: The result of the command execution.
    """
    if isinstance(command, str) and not shell:
        command = [command]
    
    return subprocess.run(
        command,
        cwd=cwd,
        env=env or os.environ,
        shell=shell,
        capture_output=capture_output,
        text=True,
        check=check,
        **kwargs
    )

def get_environment_vars(prefix: str = '') -> Dict[str, str]:
    """
    Get environment variables with an optional prefix.
    
    Args:
        prefix: Optional prefix to filter environment variables.
        
    Returns:
        Dict of environment variables with the given prefix.
    """
    if not prefix:
        return dict(os.environ)
    
    prefix = prefix.upper()
    return {k: v for k, v in os.environ.items() if k.startswith(prefix)}

# Common constants and utility functions
BYTE_UNITS = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 ** 2,
    'GB': 1024 ** 3,
    'TB': 1024 ** 4,
}

def format_bytes(size_bytes: int) -> str:
    """
    Format a size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted size string with appropriate unit.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    
    for unit in ['KB', 'MB', 'GB', 'TB']:
        size_bytes /= 1024
        if size_bytes < 1024 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
    
    return f"{size_bytes} B"

# Export commonly used functions and variables
__all__ = [
    'IS_WINDOWS',
    'IS_LINUX',
    'IS_MAC',
    'IS_POSIX',
    'PYTHON_VERSION',
    'PYTHON_VERSION_STR',
    'PLATFORM',
    'PLATFORM_RELEASE',
    'PLATFORM_VERSION',
    'CPU_COUNT',
    'MEMORY_TOTAL',
    'MEMORY_AVAILABLE',
    'get_platform_info',
    'is_program_installed',
    'run_command',
    'get_environment_vars',
    'format_bytes',
]
