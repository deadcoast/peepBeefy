"""Command history management for peepBeefy interactive CLI.

This module provides command history tracking and navigation support
for the interactive menu, allowing users to access recent commands
and navigate history with arrow keys.
"""

from typing import List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class CommandHistory:
    """Manages command history for the interactive CLI.
    
    Stores recent commands in memory and optionally persists them to disk.
    Provides navigation through history and quick-access to recent commands.
    
    Attributes:
        _history: List of command strings in chronological order
        _max_size: Maximum number of commands to store
        _current_index: Current position in history for navigation
        _history_file: Optional path to persist history to disk
    """
    
    def __init__(self, max_size: int = 100, history_file: Optional[Path] = None):
        """Initialize command history.
        
        Args:
            max_size: Maximum number of commands to store (default: 100)
            history_file: Optional path to persist history to disk
        """
        self._history: List[str] = []
        self._max_size = max_size
        self._current_index: int = -1
        self._history_file = history_file
        
        # Load history from disk if file specified
        if self._history_file:
            self._load_from_disk()
    
    def add(self, command: str) -> None:
        """Add a command to history.
        
        Avoids adding duplicate consecutive commands and empty commands.
        Maintains max_size limit by removing oldest commands when full.
        
        Args:
            command: Command string to add to history
        """
        # Skip empty commands
        if not command or not command.strip():
            return
        
        # Skip if same as last command (avoid consecutive duplicates)
        if self._history and self._history[-1] == command:
            return
        
        # Add to history
        self._history.append(command)
        
        # Trim to max size (remove oldest)
        if len(self._history) > self._max_size:
            self._history = self._history[-self._max_size:]
        
        # Reset navigation index
        self._current_index = len(self._history)
        
        # Persist to disk if configured
        if self._history_file:
            self._save_to_disk()
        
        logger.debug(f"Added command to history: {command}")
    
    def get_previous(self) -> Optional[str]:
        """Navigate to previous command in history (up arrow).
        
        Returns:
            Previous command string, or None if at beginning of history
        """
        if not self._history:
            return None
        
        # Move back in history
        if self._current_index > 0:
            self._current_index -= 1
        
        return self._history[self._current_index] if self._current_index >= 0 else None
    
    def get_next(self) -> Optional[str]:
        """Navigate to next command in history (down arrow).
        
        Returns:
            Next command string, or None if at end of history
        """
        if not self._history:
            return None
        
        # Move forward in history
        if self._current_index < len(self._history) - 1:
            self._current_index += 1
            return self._history[self._current_index]
        else:
            # At end of history, return empty string
            self._current_index = len(self._history)
            return ""
    
    def get_recent(self, count: int = 5) -> List[str]:
        """Get the most recent commands.
        
        Args:
            count: Number of recent commands to return (default: 5)
        
        Returns:
            List of recent command strings, most recent first
        """
        if not self._history:
            return []
        
        # Return last N commands in reverse order (most recent first)
        return list(reversed(self._history[-count:]))
    
    def clear(self) -> None:
        """Clear all command history."""
        self._history.clear()
        self._current_index = -1
        
        # Clear persisted history if configured
        if self._history_file and self._history_file.exists():
            try:
                self._history_file.unlink()
                logger.info("Cleared command history from disk")
            except Exception as e:
                logger.error(f"Failed to clear history file: {e}")
    
    def _load_from_disk(self) -> None:
        """Load command history from disk.
        
        Silently fails if file doesn't exist or is corrupted.
        """
        if not self._history_file or not self._history_file.exists():
            return
        
        try:
            with open(self._history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'history' in data:
                history = data['history']
                if isinstance(history, list):
                    # Validate all items are strings
                    self._history = [cmd for cmd in history if isinstance(cmd, str)]
                    # Trim to max size
                    if len(self._history) > self._max_size:
                        self._history = self._history[-self._max_size:]
                    self._current_index = len(self._history)
                    logger.info(f"Loaded {len(self._history)} commands from history")
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupted history file, starting fresh: {e}")
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
    
    def _save_to_disk(self) -> None:
        """Save command history to disk.
        
        Uses atomic write (temp file + rename) to prevent corruption.
        """
        if not self._history_file:
            return
        
        try:
            # Create directory if it doesn't exist
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file
            temp_file = self._history_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({'history': self._history}, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self._history_file)
            
            logger.debug(f"Saved {len(self._history)} commands to history")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
    
    def __len__(self) -> int:
        """Return the number of commands in history."""
        return len(self._history)
    
    def __bool__(self) -> bool:
        """Return True if history is not empty."""
        return bool(self._history)
