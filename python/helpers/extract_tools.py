"""
Tools for extracting and processing data from various sources.
"""
from typing import Any, Dict, List, Optional, Union
import re
import json
from pathlib import Path


def extract_json_from_text(text: str) -> Union[Dict, List, None]:
    """Extract JSON object or array from a string.
    
    Args:
        text: Input text potentially containing JSON
        
    Returns:
        Parsed JSON object/array or None if no valid JSON found
    """
    # Try to find JSON object or array using regex
    json_match = re.search(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|\[[^\]]*\]', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from a given text.
    
    Args:
        text: Input text potentially containing URLs
        
    Returns:
        List of URLs found in the text
    """
    # Simple URL regex pattern
    url_pattern = r'https?://\S+'
    return re.findall(url_pattern, text)


def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from a given text.
    
    Args:
        text: Input text potentially containing email addresses
        
    Returns:
        List of email addresses found in the text
    """
    # Simple email regex pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from a given text.
    
    Args:
        text: Input text potentially containing phone numbers
        
    Returns:
        List of phone numbers found in the text
    """
    # Simple phone number pattern (supports various formats)
    phone_pattern = r'\+?[\d\s-]+\(?[\d\s-]+\)?[\d\s-]+\d'
    return re.findall(phone_pattern, text)


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from a given text.
    
    Args:
        text: Input text potentially containing hashtags
        
    Returns:
        List of hashtags (without the # symbol)
    """
    # Extract hashtags (words starting with #)
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)


def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from a given text.
    
    Args:
        text: Input text potentially containing @mentions
        
    Returns:
        List of mentions (without the @ symbol)
    """
    # Extract mentions (words starting with @)
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, text)


def extract_file_extension(filename: str) -> str:
    """Extract the file extension from a filename.
    
    Args:
        filename: Name of the file with extension
        
    Returns:
        File extension in lowercase (without the dot)
    """
    return Path(filename).suffix.lower().lstrip('.')


def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract basic metadata from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file metadata
    """
    path = Path(file_path)
    return {
        'filename': path.name,
        'extension': extract_file_extension(path.name),
        'size': path.stat().st_size if path.exists() else 0,
        'created': path.stat().st_ctime if path.exists() else None,
        'modified': path.stat().st_mtime if path.exists() else None,
    }
