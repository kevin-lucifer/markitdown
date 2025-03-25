#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Preferences manager for MarkItDown UI application."""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class PreferencesManager:
    """Singleton class for managing user preferences for MarkItDown UI."""
    
    _instance: Optional["PreferencesManager"] = None
    
    # Default values for preferences
    DEFAULT_PREFERENCES = {
        "theme": "light",  # Default theme (light/dark)
        "recent_files": [],  # List of recent files with timestamps
        "zoom_level": 0,  # Default zoom level (0 = normal, positive = zoom in, negative = zoom out)
        "window_size": (800, 600),  # Default window size (width, height)
        "window_position": None,  # Window position (x, y), None for center
        "max_recent_files": 10,  # Maximum number of recent files to track
    }
    
    def __new__(cls) -> "PreferencesManager":
        """Create a singleton instance of PreferencesManager.
        
        Returns:
            The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(PreferencesManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the preferences manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self._config_dir = Path.home() / ".markitdown"
        self._config_file = self._config_dir / "preferences.json"
        self._preferences = self.DEFAULT_PREFERENCES.copy()
        
        # Load preferences or create default ones
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        """Load preferences from file or create default if file doesn't exist."""
        try:
            # Create config directory if it doesn't exist
            if not self._config_dir.exists():
                self._config_dir.mkdir(parents=True)
            
            # Load preferences if file exists
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    loaded_prefs = json.load(f)
                    
                    # Update preferences with loaded values
                    for key, value in loaded_prefs.items():
                        if key in self._preferences:
                            self._preferences[key] = value
            else:
                # Save default preferences if file doesn't exist
                self._save_preferences()
                
        except Exception as e:
            print(f"Error loading preferences: {e}")
    
    def _save_preferences(self) -> None:
        """Save preferences to file."""
        try:
            # Create config directory if it doesn't exist
            if not self._config_dir.exists():
                self._config_dir.mkdir(parents=True)
            
            # Write preferences to file
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._preferences, f, indent=2)
                
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value.
        
        Args:
            key: Preference key
            default: Default value to return if key doesn't exist
            
        Returns:
            The preference value or default if key doesn't exist
        """
        return self._preferences.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a preference value and save preferences.
        
        Args:
            key: Preference key
            value: Value to set
        """
        self._preferences[key] = value
        self._save_preferences()
    
    def get_theme(self) -> str:
        """Get the current theme.
        
        Returns:
            The current theme ('light' or 'dark')
        """
        return self._preferences.get("theme", "light")
    
    def set_theme(self, theme: str) -> None:
        """Set the current theme.
        
        Args:
            theme: Theme to set ('light' or 'dark')
        """
        if theme in ["light", "dark"]:
            self._preferences["theme"] = theme
            self._save_preferences()
    
    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.
        
        Returns:
            The new theme after toggling
        """
        current_theme = self.get_theme()
        new_theme = "dark" if current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme
    
    def get_zoom_level(self) -> int:
        """Get the current zoom level.
        
        Returns:
            The current zoom level
        """
        return self._preferences.get("zoom_level", 0)
    
    def set_zoom_level(self, level: int) -> None:
        """Set the zoom level.
        
        Args:
            level: Zoom level to set
        """
        self._preferences["zoom_level"] = level
        self._save_preferences()
    
    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent files list.
        
        Args:
            file_path: Path to the file to add
        """
        # Normalize path for consistent storage
        normalized_path = os.path.abspath(file_path)
        
        # Get current recent files
        recent_files = self._preferences.get("recent_files", [])
        
        # Remove the file if it already exists in the list
        recent_files = [f for f in recent_files if f[0] != normalized_path]
        
        # Add the file to the beginning of the list with current timestamp
        recent_files.insert(0, (normalized_path, time.time()))
        
        # Trim the list if it exceeds the maximum
        max_recent = self._preferences.get("max_recent_files", 10)
        if len(recent_files) > max_recent:
            recent_files = recent_files[:max_recent]
        
        # Update preferences and save
        self._preferences["recent_files"] = recent_files
        self._save_preferences()
    
    def get_recent_files(self) -> List[Tuple[str, float]]:
        """Get the list of recent files with timestamps.
        
        Returns:
            List of tuples containing (file_path, timestamp)
        """
        return self._preferences.get("recent_files", [])
    
    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._preferences["recent_files"] = []
        self._save_preferences()
    
    def set_window_size(self, width: int, height: int) -> None:
        """Set the window size.
        
        Args:
            width: Window width
            height: Window height
        """
        self._preferences["window_size"] = (width, height)
        self._save_preferences()
    
    def get_window_size(self) -> Tuple[int, int]:
        """Get the window size.
        
        Returns:
            Tuple containing (width, height)
        """
        return self._preferences.get("window_size", (800, 600))
    
    def set_window_position(self, x: int, y: int) -> None:
        """Set the window position.
        
        Args:
            x: Window x position
            y: Window y position
        """
        self._preferences["window_position"] = (x, y)
        self._save_preferences()
    
    def get_window_position(self) -> Optional[Tuple[int, int]]:
        """Get the window position.
        
        Returns:
            Tuple containing (x, y) or None for default centering
        """
        return self._preferences.get("window_position", None)