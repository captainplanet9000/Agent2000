"""
File handling utilities for the Agent2000 application.
"""
import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import BinaryIO, Generator, Optional, Tuple, Union, List, Dict, Any


def ensure_dir(directory: Union[str, Path]) -> Path:
    """Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_exists(file_path: Union[str, Path]) -> bool:
    """Check if a file exists and is a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file exists and is a file, False otherwise
    """
    path = Path(file_path)
    return path.exists() and path.is_file()


def dir_exists(directory: Union[str, Path]) -> bool:
    """Check if a directory exists and is a directory.
    
    Args:
        directory: Path to the directory
        
    Returns:
        True if the directory exists and is a directory, False otherwise
    """
    path = Path(directory)
    return path.exists() and path.is_dir()


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Size of the file in bytes
    """
    return Path(file_path).stat().st_size


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256', 
                 chunk_size: int = 8192) -> str:
    """Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: 'sha256')
        chunk_size: Size of chunks to read at a time (default: 8KB)
        
    Returns:
        Hex digest of the file's hash
    """
    hash_func = getattr(hashlib, algorithm.lower(), hashlib.sha256)
    hasher = hash_func()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def get_mime_type(file_path: Union[str, Path]) -> str:
    """Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string (e.g., 'text/plain', 'image/jpeg')
    """
    path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type or 'application/octet-stream'


def read_file_chunks(file_path: Union[str, Path], 
                    chunk_size: int = 8192) -> Generator[bytes, None, None]:
    """Read a file in chunks.
    
    Args:
        file_path: Path to the file
        chunk_size: Size of each chunk in bytes (default: 8KB)
        
    Yields:
        Chunks of file data as bytes
    """
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def write_file(file_path: Union[str, Path], content: Union[str, bytes], 
              mode: str = 'w', encoding: str = 'utf-8') -> int:
    """Write content to a file.
    
    Args:
        file_path: Path where the file should be written
        content: Content to write (str or bytes)
        mode: Write mode ('w' for text, 'wb' for binary)
        encoding: Text encoding (default: 'utf-8')
        
    Returns:
        Number of bytes written
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if 'b' in mode:
        if isinstance(content, str):
            content = content.encode(encoding)
        with open(path, mode) as f:
            return f.write(content)
    else:
        if isinstance(content, bytes):
            content = content.decode(encoding)
        with open(path, mode, encoding=encoding) as f:
            return f.write(content)


def copy_file(src: Union[str, Path], dst: Union[str, Path], 
              overwrite: bool = False) -> bool:
    """Copy a file from source to destination.
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Whether to overwrite if destination exists (default: False)
        
    Returns:
        True if the file was copied successfully, False otherwise
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists() or not src_path.is_file():
        return False
    
    if dst_path.exists() and not overwrite:
        return False
    
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)
    return True


def delete_file(file_path: Union[str, Path], missing_ok: bool = True) -> bool:
    """Delete a file.
    
    Args:
        file_path: Path to the file to delete
        missing_ok: If True, don't raise an error if the file doesn't exist
        
    Returns:
        True if the file was deleted or didn't exist, False on error
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
        return True
    except Exception:
        if not missing_ok:
            raise
        return False


def list_files(directory: Union[str, Path], pattern: str = '*', 
               recursive: bool = False) -> List[Path]:
    """List files in a directory matching a pattern.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern to match files (default: '*')
        recursive: Whether to search recursively (default: False)
        
    Returns:
        List of Path objects for matching files
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return []
    
    if recursive:
        return list(path.rglob(pattern))
    return list(path.glob(pattern))


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get detailed information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file information
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = path.stat()
    
    return {
        'path': str(path.absolute()),
        'name': path.name,
        'parent': str(path.parent.absolute()),
        'size': stat.st_size,
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'accessed': stat.st_atime,
        'permissions': oct(stat.st_mode)[-3:],
        'mime_type': get_mime_type(path),
        'is_symlink': path.is_symlink(),
        'is_dir': False,
        'is_file': True,
    }
