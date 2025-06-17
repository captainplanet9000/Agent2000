"""
History tracking and management utilities for the Agent2000 application.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypedDict, Callable, TypeVar
from pathlib import Path
import json
import os
from dataclasses import dataclass, asdict, field
from uuid import uuid4

# Type variable for generic functions
T = TypeVar('T')


class HistoryEntry(TypedDict, total=False):
    """Represents a single entry in the history."""
    id: str
    timestamp: str
    type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class HistoryConfig:
    """Configuration for history management."""
    max_entries: int = 1000
    persist_to_disk: bool = True
    storage_path: str = "./data/history"
    auto_prune: bool = True
    prune_threshold: int = 2000


class HistoryManager:
    """Manages history entries with in-memory storage and optional persistence."""
    
    def __init__(self, config: Optional[HistoryConfig] = None):
        """Initialize the history manager.
        
        Args:
            config: Configuration for history management. If None, uses defaults.
        """
        self.config = config or HistoryConfig()
        self.entries: List[HistoryEntry] = []
        self._filters: Dict[str, Callable[[HistoryEntry], bool]] = {}
        self._listeners: List[Callable[[HistoryEntry], None]] = []
        
        # Create storage directory if needed
        if self.config.persist_to_disk:
            os.makedirs(self.config.storage_path, exist_ok=True)
    
    def add_entry(
        self, 
        entry_type: str, 
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new entry to the history.
        
        Args:
            entry_type: Type/category of the entry
            data: The main data for the entry
            metadata: Optional metadata about the entry
            
        Returns:
            The ID of the created entry
        """
        entry_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        entry: HistoryEntry = {
            'id': entry_id,
            'timestamp': now,
            'type': entry_type,
            'data': data,
            'metadata': metadata or {}
        }
        
        self.entries.append(entry)
        
        # Prune old entries if needed
        if self.config.auto_prune and len(self.entries) > self.config.prune_threshold:
            self.prune_entries()
        
        # Persist to disk if enabled
        if self.config.persist_to_disk:
            self._save_entry(entry)
        
        # Notify listeners
        for listener in self._listeners:
            try:
                listener(entry)
            except Exception:
                # Don't let listener exceptions break history tracking
                pass
        
        return entry_id
    
    def get_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        """Get an entry by its ID.
        
        Args:
            entry_id: The ID of the entry to retrieve
            
        Returns:
            The entry if found, None otherwise
        """
        for entry in self.entries:
            if entry.get('id') == entry_id:
                return entry
        return None
    
    def get_entries(
        self, 
        entry_type: Optional[str] = None,
        limit: Optional[int] = None,
        reverse: bool = False
    ) -> List[HistoryEntry]:
        """Get entries matching the given criteria.
        
        Args:
            entry_type: If provided, only return entries of this type
            limit: Maximum number of entries to return
            reverse: If True, return entries in reverse chronological order
            
        Returns:
            List of matching history entries
        """
        result = self.entries
        
        # Filter by type if specified
        if entry_type is not None:
            result = [e for e in result if e.get('type') == entry_type]
        
        # Apply registered filters
        for filter_func in self._filters.values():
            result = [e for e in result if filter_func(e)]
        
        # Sort by timestamp
        result.sort(key=lambda e: e.get('timestamp', ''), reverse=not reverse)
        
        # Apply limit
        if limit is not None and limit > 0:
            result = result[-limit:] if not reverse else result[:limit]
        
        return result
    
    def add_filter(self, name: str, filter_func: Callable[[HistoryEntry], bool]) -> None:
        """Add a filter function to apply to all queries.
        
        Args:
            name: Unique name for the filter
            filter_func: Function that takes an entry and returns True to include it
        """
        self._filters[name] = filter_func
    
    def remove_filter(self, name: str) -> bool:
        """Remove a filter by name.
        
        Args:
            name: Name of the filter to remove
            
        Returns:
            True if the filter was removed, False if not found
        """
        if name in self._filters:
            del self._filters[name]
            return True
        return False
    
    def add_listener(self, callback: Callable[[HistoryEntry], None]) -> Callable[[], None]:
        """Add a callback to be called when a new entry is added.
        
        Args:
            callback: Function to call with the new entry
            
        Returns:
            A function that can be called to remove the listener
        """
        self._listeners.append(callback)
        
        def remove():
            if callback in self._listeners:
                self._listeners.remove(callback)
                
        return remove
    
    def prune_entries(self) -> int:
        """Remove old entries to keep within the configured limit.
        
        Returns:
            Number of entries removed
        """
        if len(self.entries) <= self.config.max_entries:
            return 0
            
        # Sort entries by timestamp (oldest first)
        self.entries.sort(key=lambda e: e.get('timestamp', ''))
        
        # Calculate how many to remove
        remove_count = len(self.entries) - self.config.max_entries
        
        # Remove the oldest entries
        self.entries = self.entries[remove_count:]
        
        return remove_count
    
    def clear(self) -> None:
        """Clear all history entries."""
        self.entries = []
    
    def _save_entry(self, entry: HistoryEntry) -> bool:
        """Save an entry to disk.
        
        Args:
            entry: The entry to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create a filename based on timestamp and ID
            timestamp = entry.get('timestamp', '').replace(':', '-').replace('.', '-')
            filename = f"{timestamp}_{entry.get('id')}.json"
            filepath = os.path.join(self.config.storage_path, filename)
            
            # Write the entry as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception:
            return False
    
    def load_from_disk(self) -> int:
        """Load history entries from disk.
        
        Returns:
            Number of entries loaded
        """
        if not self.config.persist_to_disk or not os.path.isdir(self.config.storage_path):
            return 0
            
        count = 0
        
        for filename in os.listdir(self.config.storage_path):
            if not filename.endswith('.json'):
                continue
                
            try:
                filepath = os.path.join(self.config.storage_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                    
                if self._is_valid_entry(entry):
                    self.entries.append(entry)
                    count += 1
            except Exception:
                continue
                
        return count
    
    @staticmethod
    def _is_valid_entry(entry: Any) -> bool:
        """Check if an entry has the required fields."""
        return (
            isinstance(entry, dict) and
            'id' in entry and
            'timestamp' in entry and
            'type' in entry and
            'data' in entry
        )


def get_default_history_manager() -> HistoryManager:
    """Get the default history manager instance."""
    if not hasattr(get_default_history_manager, '_instance'):
        get_default_history_manager._instance = HistoryManager()
    return get_default_history_manager._instance
