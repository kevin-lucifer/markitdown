#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Tests for the PreferencesManager class."""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, PropertyMock

from markitdown_ui.preferences import PreferencesManager


class TestPreferencesManager(unittest.TestCase):
    """Test cases for the PreferencesManager class."""

    def setUp(self):
        """Set up test environment with temporary directory for config files."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Reset the singleton instance
        PreferencesManager._instance = None
        
        # Patch the home directory to use our temporary directory
        self.home_patcher = patch('pathlib.Path.home')
        self.mock_home = self.home_patcher.start()
        self.mock_home.return_value = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up after tests."""
        # Stop the home directory patch
        self.home_patcher.stop()
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        
        # Reset the singleton instance
        PreferencesManager._instance = None

    def test_singleton_pattern(self):
        """Test that PreferencesManager is a singleton."""
        # Create two instances
        manager1 = PreferencesManager()
        manager2 = PreferencesManager()
        
        # Check that they are the same instance
        self.assertIs(manager1, manager2)
        
        # Modify a preference in one instance
        manager1.set_theme("dark")
        
        # Check that it's reflected in the other instance
        self.assertEqual(manager2.get_theme(), "dark")

    def test_default_preferences(self):
        """Test that default preferences are correctly initialized."""
        manager = PreferencesManager()
        
        # Check that default values are set
        self.assertEqual(manager.get_theme(), "light")
        self.assertEqual(manager.get_zoom_level(), 0)
        self.assertEqual(manager.get_window_size(), (800, 600))
        self.assertIsNone(manager.get_window_position())
        self.assertEqual(manager.get_recent_files(), [])
        self.assertEqual(manager.get("max_recent_files"), 10)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_preferences(self, mock_json_dump, mock_file):
        """Test saving preferences to file."""
        manager = PreferencesManager()
        
        # Set a preference
        manager.set_theme("dark")
        
        # Check that the file was opened for writing
        mock_file.assert_called()
        
        # Check that json.dump was called with the correct preferences
        mock_json_dump.assert_called()
        
        # The first call has the preferences dictionary as the first argument
        preferences_arg = mock_json_dump.call_args[0][0]
        self.assertEqual(preferences_arg["theme"], "dark")

    @patch('builtins.open', new_callable=mock_open, read_data='{"theme": "dark", "zoom_level": 2}')
    @patch('pathlib.Path.exists')
    def test_load_preferences(self, mock_exists, mock_file):
        """Test loading preferences from file."""
        # Configure the mock to say the file exists
        mock_exists.return_value = True
        
        # Create a preferences manager
        manager = PreferencesManager()
        
        # Check that it loaded the preferences from the mock file
        self.assertEqual(manager.get_theme(), "dark")
        self.assertEqual(manager.get_zoom_level(), 2)

    def test_theme_management(self):
        """Test theme management methods."""
        manager = PreferencesManager()
        
        # Default theme should be light
        self.assertEqual(manager.get_theme(), "light")
        
        # Set theme to dark
        manager.set_theme("dark")
        self.assertEqual(manager.get_theme(), "dark")
        
        # Toggle theme (should go back to light)
        new_theme = manager.toggle_theme()
        self.assertEqual(new_theme, "light")
        self.assertEqual(manager.get_theme(), "light")
        
        # Toggle again (should go to dark)
        new_theme = manager.toggle_theme()
        self.assertEqual(new_theme, "dark")
        self.assertEqual(manager.get_theme(), "dark")
        
        # Try to set an invalid theme (should be ignored)
        manager.set_theme("invalid")
        self.assertEqual(manager.get_theme(), "dark")  # unchanged

    def test_zoom_level_management(self):
        """Test zoom level management methods."""
        manager = PreferencesManager()
        
        # Default zoom level should be 0
        self.assertEqual(manager.get_zoom_level(), 0)
        
        # Set zoom level to 2
        manager.set_zoom_level(2)
        self.assertEqual(manager.get_zoom_level(), 2)
        
        # Set zoom level to negative value
        manager.set_zoom_level(-1)
        self.assertEqual(manager.get_zoom_level(), -1)

    @patch('time.time', return_value=1000.0)
    def test_recent_files_management(self, mock_time):
        """Test recent files management methods."""
        manager = PreferencesManager()
        
        # Initially, recent files list should be empty
        self.assertEqual(manager.get_recent_files(), [])
        
        # Add a file
        file_path = "/path/to/file.pdf"
        manager.add_recent_file(file_path)
        
        # Check that it was added with the current timestamp
        recent_files = manager.get_recent_files()
        self.assertEqual(len(recent_files), 1)
        self.assertEqual(recent_files[0][0], os.path.abspath(file_path))
        self.assertEqual(recent_files[0][1], 1000.0)
        
        # Add the same file again
        mock_time.return_value = 2000.0
        manager.add_recent_file(file_path)
        
        # Should still have one file but with updated timestamp
        recent_files = manager.get_recent_files()
        self.assertEqual(len(recent_files), 1)
        self.assertEqual(recent_files[0][1], 2000.0)
        
        # Add different files
        mock_time.return_value = 3000.0
        manager.add_recent_file("/path/to/file2.pdf")
        mock_time.return_value = 4000.0
        manager.add_recent_file("/path/to/file3.pdf")
        
        # Check order (most recent first)
        recent_files = manager.get_recent_files()
        self.assertEqual(len(recent_files), 3)
        self.assertEqual(recent_files[0][0], os.path.abspath("/path/to/file3.pdf"))
        self.assertEqual(recent_files[1][0], os.path.abspath("/path/to/file2.pdf"))
        self.assertEqual(recent_files[2][0], os.path.abspath(file_path))
        
        # Clear recent files
        manager.clear_recent_files()
        self.assertEqual(manager.get_recent_files(), [])

    def test_max_recent_files(self):
        """Test that the recent files list is limited to the maximum number."""
        manager = PreferencesManager()
        
        # Override max_recent_files to a smaller number for testing
        manager.set("max_recent_files", 3)
        
        # Add more than the maximum number of files
        for i in range(5):
            manager.add_recent_file(f"/path/to/file{i}.pdf")
        
        # Check that only the most recent 3 files are kept
        recent_files = manager.get_recent_files()
        self.assertEqual(len(recent_files), 3)
        self.assertEqual(recent_files[0][0], os.path.abspath("/path/to/file4.pdf"))
        self.assertEqual(recent_files[1][0], os.path.abspath("/path/to/file3.pdf"))
        self.assertEqual(recent_files[2][0], os.path.abspath("/path/to/file2.pdf"))

    def test_window_geometry(self):
        """Test window size and position management."""
        manager = PreferencesManager()
        
        # Default window size
        self.assertEqual(manager.get_window_size(), (800, 600))
        
        # Set window size
        manager.set_window_size(1024, 768)
        self.assertEqual(manager.get_window_size(), (1024, 768))
        
        # Default window position is None
        self.assertIsNone(manager.get_window_position())
        
        # Set window position
        manager.set_window_position(100, 200)
        self.assertEqual(manager.get_window_position(), (100, 200))

    def test_general_preferences(self):
        """Test general preference getter and setter."""
        manager = PreferencesManager()
        
        # Set a custom preference
        manager.set("custom_key", "custom_value")
        self.assertEqual(manager.get("custom_key"), "custom_value")
        
        # Test get with default value
        self.assertEqual(manager.get("nonexistent_key", "default"), "default")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_config_directory_creation(self, mock_mkdir, mock_exists):
        """Test that config directory is created if it doesn't exist."""
        # Config directory doesn't exist
        mock_exists.return_value = False
        
        # Create manager
        manager = PreferencesManager()
        
        # Check that mkdir was called
        mock_mkdir.assert_called_once()
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    @patch('builtins.print')
    def test_error_handling_save(self, mock_print, mock_open):
        """Test error handling when saving preferences."""
        manager = PreferencesManager()
        
        # Try to save preferences
        manager.set("test", "value")
        
        # Check that the error was caught and printed
        mock_print.assert_called_once()
        self.assertIn("Error saving preferences", mock_print.call_args[0][0])

    @patch('pathlib.Path.exists')
    @patch('builtins.open', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    @patch('builtins.print')
    def test_error_handling_load(self, mock_print, mock_open, mock_exists):
        """Test error handling when loading preferences."""
        # Config file exists but has invalid JSON
        mock_exists.return_value = True
        
        # Create manager
        manager = PreferencesManager()
        
        # Check that the error was caught and printed
        mock_print.assert_called_once()
        self.assertIn("Error loading preferences", mock_print.call_args[0][0])


if __name__ == "__main__":
    unittest.main()