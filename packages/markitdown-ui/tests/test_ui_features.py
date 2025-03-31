#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Tests for the new UI features in MarkItDown UI application."""

import os
import unittest
import tkinter as tk
from tkinter import TclError, Toplevel, Event, ttk
from unittest.mock import patch, MagicMock, PropertyMock, call, ANY

from markitdown_ui.app import MarkItDownUI
from markitdown_ui.preferences import PreferencesManager
from markitdown_ui.theme import ThemeManager


class TestUIFeatures(unittest.TestCase):
    """Test cases for the enhanced UI features in MarkItDown UI."""

    def setUp(self):
        """Set up test environment."""
        # Reset singleton instances
        PreferencesManager._instance = None
        ThemeManager._instance = None
        
        # Patch PreferencesManager to avoid file operations
        self.prefs_patcher = patch('markitdown_ui.app.PreferencesManager')
        self.mock_prefs_class = self.prefs_patcher.start()
        self.mock_prefs = MagicMock()
        self.mock_prefs.get_theme.return_value = "light"
        self.mock_prefs.get_zoom_level.return_value = 0
        self.mock_prefs.get_window_size.return_value = (1024, 768)
        self.mock_prefs.get_window_position.return_value = None
        self.mock_prefs.get_recent_files.return_value = []
        self.mock_prefs_class.return_value = self.mock_prefs
        self.mock_prefs.DEFAULT_PREFERENCES = PreferencesManager.DEFAULT_PREFERENCES.copy()
        
        # Patch ThemeManager
        self.theme_patcher = patch('markitdown_ui.app.ThemeManager')
        self.mock_theme_class = self.theme_patcher.start()
        self.mock_theme = MagicMock()
        self.mock_theme.get_theme_colors.return_value = ThemeManager.LIGHT_THEME
        self.mock_theme_class.return_value = self.mock_theme
        
        # Create UI instance
        try:
            self.root = tk.Tk()
            self.ui = MarkItDownUI(self.root)
        except TclError:
            # Skip tests if no display is available (CI environment)
            self.skipTest("No display available")

    def tearDown(self):
        """Clean up after tests."""
        # Stop patches
        self.prefs_patcher.stop()
        self.theme_patcher.stop()
        
        # Destroy the root window if it was created
        if hasattr(self, 'root'):
            try:
                self.root.destroy()
            except:
                pass
        
        # Reset singletons
        PreferencesManager._instance = None
        ThemeManager._instance = None

    def test_zoom_functionality(self):
        """Test zoom functionality."""
        # Test initial zoom level
        self.assertEqual(self.ui.zoom_level, 0)
        
        # Test zoom in
        self.ui.zoom_in()
        self.assertEqual(self.ui.zoom_level, 1)
        self.mock_prefs.set_zoom_level.assert_called_once_with(1)
        
        # Test zoom out
        self.ui.zoom_out()
        self.assertEqual(self.ui.zoom_level, 0)
        self.mock_prefs.set_zoom_level.assert_called_with(0)
        
        # Test reset zoom
        self.ui.zoom_level = 3
        self.ui.reset_zoom()
        self.assertEqual(self.ui.zoom_level, 0)
        self.mock_prefs.set_zoom_level.assert_called_with(0)
        
        # Test zoom limits
        self.ui.zoom_level = 5
        self.ui.zoom_in()
        self.assertEqual(self.ui.zoom_level, 5)  # Should not exceed max
        
        self.ui.zoom_level = -5
        self.ui.zoom_out()
        self.assertEqual(self.ui.zoom_level, -5)  # Should not exceed min

    def test_window_geometry_management(self):
        """Test window geometry management."""
        # Test load_window_geometry with default position
        with patch.object(self.ui, '_get_center_position', return_value=(100, 100)) as mock_center:
            self.ui._load_window_geometry()
            mock_center.assert_called_once_with((1024, 768))
        self.mock_prefs.get_window_size.assert_called_once()
        self.mock_prefs.get_window_position.assert_called_once()
        
        # Test load_window_geometry with saved position
        self.mock_prefs.get_window_position.return_value = (50, 60)
        self.ui._load_window_geometry()
        
        # Test save_window_geometry
        with patch.object(self.root, 'winfo_width', return_value=1000), \
             patch.object(self.root, 'winfo_height', return_value=700), \
             patch.object(self.root, 'winfo_x', return_value=10), \
             patch.object(self.root, 'winfo_y', return_value=20):
            self.ui._save_window_geometry()
            self.mock_prefs.set_window_size.assert_called_once_with(1000, 700)
            self.mock_prefs.set_window_position.assert_called_once_with(10, 20)
        
        # Test get_center_position
        with patch.object(self.root, 'winfo_screenwidth', return_value=1920), \
             patch.object(self.root, 'winfo_screenheight', return_value=1080):
            pos = self.ui._get_center_position((1024, 768))
            self.assertEqual(pos, (448, 156))  # Updated for 1024x768 window
        
        # Test window close handler calls save_window_geometry
        with patch.object(self.ui, '_save_window_geometry') as mock_save, \
             patch.object(self.root, 'quit') as mock_quit:
            self.ui._on_close()
            mock_save.assert_called_once()
            mock_quit.assert_called_once()

    def test_document_statistics(self):
        """Test document statistics calculation and display."""
        # Set up mock content
        self.ui.preview_text.delete(1.0, tk.END)
        self.ui.preview_text.insert(tk.END, "Hello world! This is a test document.")
        
        # Test statistics update
        self.ui._update_document_stats()
        self.assertEqual(self.ui.stats_var.get(), "Words: 7  Characters: 37")
        
        # Test with more complex content
        self.ui.preview_text.delete(1.0, tk.END)
        self.ui.preview_text.insert(tk.END, "# Heading\n\nThis is a paragraph with some **bold** text.\n\n- List item 1\n- List item 2\n")
        self.ui._update_document_stats()
        self.assertEqual(self.ui.stats_var.get(), "Words: 13  Characters: 74")
        
        # Test with empty content
        self.ui.preview_text.delete(1.0, tk.END)
        self.ui._update_document_stats()
        self.assertEqual(self.ui.stats_var.get(), "Words: 0  Characters: 0")
        
        # Test statistics update after preview clears
        self.ui._clear_preview()
        self.assertEqual(self.ui.stats_var.get(), "Words: 0  Characters: 0")

    @patch('tkinter.ttk.Frame')
    @patch('tkinter.Toplevel')
    def test_about_dialog(self, mock_toplevel, mock_frame):
        """Test the custom about dialog."""
        # Mock the Toplevel window
        mock_window = MagicMock()
        mock_toplevel.return_value = mock_window
        mock_window.nametowidget.return_value = MagicMock()
        mock_frame.return_value = MagicMock()
        
        # Mock Canvas
        mock_canvas = MagicMock()
        with patch('tkinter.Canvas', return_value=mock_canvas):
            # Show about dialog
            self.ui._show_about()
            
            # Check window configuration
            mock_toplevel.assert_called_once()
            mock_window.title.assert_called_once_with("About MarkItDown UI")
            mock_window.geometry.assert_called()
            mock_window.resizable.assert_called_once_with(False, False)
            mock_window.transient.assert_called_once()
            mock_window.grab_set.assert_called_once()
            
            # Check canvas creation and drawing
            mock_canvas.pack.assert_called_once_with(fill=tk.BOTH, expand=True)
            self.assertEqual(mock_canvas.create_rectangle.call_count, 1)
            self.assertGreaterEqual(mock_canvas.create_polygon.call_count, 3)  # Mountains
            self.assertGreaterEqual(mock_canvas.create_text.call_count, 3)  # Text elements
            
            # Check theme was applied
            self.mock_theme.apply_menu_theme.assert_called_once()

    def test_recent_files_menu(self):
        """Test recent files menu creation and updating."""
        # Setup mock recent files
        recent_files = [
            ("/path/to/file1.pdf", 1000.0),
            ("/path/to/file2.docx", 900.0),
            ("/path/to/file3.html", 800.0),
        ]
        self.mock_prefs.get_recent_files.return_value = recent_files
        
        # Mock menu
        mock_menu = MagicMock()
        self.ui.recent_menu = mock_menu
        
        # Test menu update
        self.ui._update_recent_files_menu()
        
        # Check that menu was cleared and items were added
        mock_menu.delete.assert_called_once_with(0, tk.END)
        self.assertEqual(mock_menu.add_command.call_count, 4)  # 3 files + 1 clear option
        mock_menu.add_separator.assert_called_once()
        
        # Test clearing recent files
        self.ui._clear_recent_files()
        self.mock_prefs.clear_recent_files.assert_called_once()
        self.mock_prefs.get_recent_files.assert_called()
        
+        # Add comment explaining recent files count includes 3 files and 1 clear option
+
         # Test file opening adds to recent files
         with patch.object(self.ui, '_clear_preview'):
             self.ui.open_file("/path/to/newfile.xlsx")
@@ -237,8 +237,8 @@
         self.assertGreaterEqual(len(toolbar_buttons), 5)  # Should have at least 5 buttons
         
         # Test button commands
-        button_commands = [str(btn.cget('command')) for btn in toolbar_buttons]
-        self.assertIn('_open_file_dialog', ''.join(button_commands))
+        button_commands = [btn.cget('command').__name__ for btn in toolbar_buttons]
+        self.assertIn('OpenFileDialog', button_commands)
         
         # Check style
         for btn in toolbar_buttons:
@@ -259,19 +259,19 @@
         bindings = self.root.bind()
         
         # Check for required bindings
-        self.assertIn("<Control-Key-o>", bindings)
-        self.assertIn("<Control-Key-s>", bindings)
-        self.assertIn("<Control-Key-plus>", bindings)
-        self.assertIn("<Control-Key-minus>", bindings)
-        self.assertIn("<Control-Key-0>", bindings)
-        self.assertIn("<Control-Key-t>", bindings)
+        self.assertIn("<Control-o>", bindings)
+        self.assertIn("<Control-s>", bindings)
+        self.assertIn("<Control-plus>", bindings)
+        self.assertIn("<Control-minus>", bindings)
+        self.assertIn("<Control-0>", bindings)
+        self.assertIn("<Control-t>", bindings)
         
         # Test binding callbacks
         with patch.object(self.ui, 'zoom_in') as mock_zoom:
-            self.root.event_generate("<Control-Key-plus>")
+            self.root.event_generate("<Control-plus>")
             mock_zoom.assert_called_once()
         # Note: Can't directly test event callbacks in unittest
         # but we can check that the bindings exist and point to the correct methods
-        callback = self.root.bind("<Control-Key-o>")
+        callback = self.root.bind("<Control-o>")
         self.assertIsNotNone(callback)

     def test_status_bar_updates(self):