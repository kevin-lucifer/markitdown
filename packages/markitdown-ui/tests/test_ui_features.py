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
        self.assertEqual(self.ui.stats_var.get(), "Words: 6  Characters: 39")
        
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
        self.assertEqual(mock_menu.add_command.call_count, 4)  # 3 files + separator + clear option
        mock_menu.add_separator.assert_called_once()
        
        # Test clearing recent files
        self.ui._clear_recent_files()
        self.mock_prefs.clear_recent_files.assert_called_once()
        self.mock_prefs.get_recent_files.assert_called()
        
        # Test file opening adds to recent files
        with patch.object(self.ui, '_clear_preview'):
            self.ui.open_file("/path/to/newfile.xlsx")
            self.mock_prefs.add_recent_file.assert_called_once_with("/path/to/newfile.xlsx")

    def test_toolbar_creation(self):
        """Test toolbar creation and button functionality."""
        # Check that toolbar exists
        self.assertTrue(hasattr(self.ui, 'toolbar'))
        
        # Check that toolbar has buttons
        toolbar_buttons = [widget for widget in self.ui.toolbar.winfo_children() 
                          if isinstance(widget, ttk.Button)]
        self.assertGreaterEqual(len(toolbar_buttons), 5)  # Should have at least 5 buttons
        
        # Test button commands
        button_commands = set(btn.cget('command') for btn in toolbar_buttons)
        self.assertIn(self.ui._open_file_dialog, button_commands)
        self.assertIn(self.ui._save_file, button_commands)
        self.assertIn(self.ui._toggle_theme, button_commands)
        self.assertIn(self.ui.zoom_in, button_commands)
        self.assertIn(self.ui.zoom_out, button_commands)
        
        # Check style
        for btn in toolbar_buttons:
            self.assertEqual(btn.cget('style'), 'Toolbar.TButton')

    def test_theme_switching(self):
        """Test theme switching functionality."""
        # Test toggle_theme from menu
        self.ui._toggle_theme()
        self.mock_theme.toggle_theme.assert_called_once()
        self.mock_theme.apply_theme.assert_called_once()
        self.mock_theme.apply_text_widget_theme.assert_called_once_with(self.ui.preview_text)
        self.mock_theme.apply_menu_theme.assert_called_once()

    def test_keyboard_shortcuts(self):
        """Test keyboard shortcut bindings."""
        # Get root bindings
        bindings = self.root.bind()
        
        # Check for required bindings
        self.assertIn("<Control-o>", bindings)
        self.assertIn("<Control-s>", bindings)
        self.assertIn("<Control-+>", bindings)
        self.assertIn("<Control-->", bindings)
        self.assertIn("<Control-0>", bindings)
        self.assertIn("<Control-t>", bindings)
        
        # Test binding callbacks
        with patch.object(self.ui, 'zoom_in') as mock_zoom:
            self.root.event_generate("<Control-+>")
            mock_zoom.assert_called_once()
        # Note: Can't directly test event callbacks in unittest
        # but we can check that the bindings exist and point to the correct methods
        callback = self.root.bind("<Control-o>")
        self.assertIsNotNone(callback)

    def test_status_bar_updates(self):
        """Test status bar updates with document statistics."""
        # Check status bar initialization
        self.assertTrue(hasattr(self.ui, 'stats_var'))
        self.assertTrue(hasattr(self.ui, 'status_var'))
        
        # Test status update
        test_status = "Test status message"
        self.ui._update_status(test_status)
        self.assertEqual(self.ui.status_var.get(), test_status)
        
        # Test document statistics update
        self.ui._update_document_stats()
        self.assertNotEqual(self.ui.stats_var.get(), "")
        self.assertTrue(self.ui.stats_var.get().startswith("Words:"))

    def test_menu_structure(self):
        """Test the menu structure and content."""
        menubar = self.root.nametowidget(self.root["menu"])
        
        # Check menu labels
        menu_labels = [menubar.entrycget(i, "label") for i in range(menubar.index("end") + 1)]
        self.assertIn("File", menu_labels)
        self.assertIn("Edit", menu_labels)
        self.assertIn("View", menu_labels)
        self.assertIn("Help", menu_labels)
        
        # Check View menu items
        view_menu_index = menu_labels.index("View")
        view_menu = menubar.nametowidget(menubar.entrycget(view_menu_index, "menu"))
        
        view_commands = []
        for i in range(view_menu.index("end") + 1):
            if view_menu.type(i) == "command":
                view_commands.append(view_menu.entrycget(i, "label"))
        
        self.assertIn("Zoom In", view_commands)
        self.assertIn("Zoom Out", view_commands)
        self.assertIn("Reset Zoom", view_commands)
        self.assertIn("Toggle Theme", view_commands)
        
        # Check File menu items
        file_menu_index = menu_labels.index("File")
        file_menu = menubar.nametowidget(menubar.entrycget(file_menu_index, "menu"))
        
        file_items = []
        for i in range(file_menu.index("end") + 1):
            if file_menu.type(i) in ["command", "cascade"]:
                file_items.append(file_menu.entrycget(i, "label"))
        
        self.assertIn("New", file_items)
        self.assertIn("Open...", file_items)
        self.assertIn("Save", file_items)
        self.assertIn("Save As...", file_items)
        self.assertIn("Recent Files", file_items)
        self.assertIn("Exit", file_items)

    def test_new_file(self):
        """Test new file functionality."""
        with patch.object(self.ui, 'open_file') as mock_open, \
             patch.object(self.ui, '_clear_preview') as mock_clear, \
             patch.object(self.ui, '_update_status') as mock_status:
            
            self.ui._new_file()
            
            mock_open.assert_called_once_with("")
            mock_clear.assert_called_once()
            mock_status.assert_called_once_with("New file created")


if __name__ == "__main__":
    unittest.main()