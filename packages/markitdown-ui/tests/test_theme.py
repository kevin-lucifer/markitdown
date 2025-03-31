#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Tests for the ThemeManager class."""

import unittest
import tkinter as tk
from tkinter import ttk, TclError
from unittest.mock import patch, MagicMock, call

from markitdown_ui.theme import ThemeManager
from markitdown_ui.preferences import PreferencesManager


class TestThemeManager(unittest.TestCase):
    """Test cases for the ThemeManager class."""

    def setUp(self):
        """Set up test environment."""
        # Reset the singleton instances
        ThemeManager._instance = None
        PreferencesManager._instance = None
        
        # Patch PreferencesManager to avoid file operations
        self.prefs_patcher = patch('markitdown_ui.theme.PreferencesManager')
        self.mock_prefs_class = self.prefs_patcher.start()
        self.mock_prefs = MagicMock()
        self.mock_prefs_class.return_value = self.mock_prefs
        self.mock_prefs.get_theme.return_value = "light"

        # Create theme manager
        self.theme_manager = ThemeManager()

        try:
            # Create a root window for testing with widgets
            self.root = tk.Tk()
        except TclError:
            # Skip tests if no display is available (CI environment)
            self.skipTest("No display available")

    def tearDown(self):
        """Clean up after tests."""
        # Stop the preference manager patch
        self.prefs_patcher.stop()
        
        # Clear the singleton instance
        ThemeManager._instance = None
        PreferencesManager._instance = None
        
        # Destroy the root window if it was created
        if hasattr(self, 'root'):
            try:
                self.root.destroy()
            except:
                pass

    def test_singleton_pattern(self):
        """Test that ThemeManager is a singleton."""
        # Create two instances
        manager1 = ThemeManager()
        manager2 = ThemeManager()
        
        # Check that they are the same instance
        self.assertIs(manager1, manager2)
        
        # Check that _initialized is only set once
        manager1._initialized = False
        manager1.__init__()
        manager2.__init__()
        
        self.assertFalse(manager1._initialized)
        self.assertFalse(manager2._initialized)

    def test_initialization(self):
        """Test initialization of the theme manager."""
        self.assertEqual(self.theme_manager._current_theme, "light")
        self.assertIsNone(self.theme_manager._root)
        self.assertIsNone(self.theme_manager._style)
        
        # Test initialize with root window
        self.theme_manager.initialize(self.root)
        
        self.assertEqual(self.theme_manager._root, self.root)
        self.assertIsInstance(self.theme_manager._style, ttk.Style)
        
        # Check that apply_theme was called during initialization
        self.mock_prefs.get_theme.assert_called_once()

    def test_apply_theme_with_no_root(self):
        """Test apply_theme throws error when called before initialization."""
        manager = ThemeManager()
        
        with self.assertRaises(RuntimeError):
            manager.apply_theme("dark")

    @patch('markitdown_ui.theme.ThemeManager._configure_ttk_style')
    @patch('markitdown_ui.theme.ThemeManager._configure_tk_widgets')
    def test_apply_theme(self, mock_configure_tk, mock_configure_ttk):
        """Test applying a theme."""
        # Initialize the theme manager
        self.theme_manager.initialize(self.root)
        
        # Apply light theme
        self.theme_manager.apply_theme("light")
        
        # Check that the current theme was updated
        self.assertEqual(self.theme_manager._current_theme, "light")
        
        # Check that the style configuration methods were called
        mock_configure_ttk.assert_called_once()
        mock_configure_tk.assert_called_once()
        
        # Check that the theme was saved to preferences
        self.mock_prefs.set_theme.assert_called_once_with("light")
        
        # Reset mocks
        mock_configure_ttk.reset_mock()
        mock_configure_tk.reset_mock()
        self.mock_prefs.set_theme.reset_mock()
        
        # Apply dark theme
        self.theme_manager.apply_theme("dark")
        
        # Check that the current theme was updated
        self.assertEqual(self.theme_manager._current_theme, "dark")
        
        # Check that the style configuration methods were called again
        mock_configure_ttk.assert_called_once()
        mock_configure_tk.assert_called_once()
        
        # Check that the theme was saved to preferences
        self.mock_prefs.set_theme.assert_called_once_with("dark")
        
        # Check that correct colors dict was passed to configure methods
        colors_arg = mock_configure_ttk.call_args[0][0]
        self.assertEqual(colors_arg["background"], "#2d2d2d")  # Dark theme background

    def test_toggle_theme(self):
        """Test toggle_theme method."""
        # Initialize the theme manager with light theme
        self.theme_manager.initialize(self.root)
        self.theme_manager._current_theme = "light"
        
        with patch.object(self.theme_manager, 'apply_theme') as mock_apply:
            # Toggle from light to dark
            result = self.theme_manager.toggle_theme()
            
            # Check return value and method call
            self.assertEqual(result, "dark")
            mock_apply.assert_called_once_with("dark")
            
            # Reset mock and theme
            mock_apply.reset_mock()
            self.theme_manager._current_theme = "dark"
            
            # Toggle from dark to light
            result = self.theme_manager.toggle_theme()
            
            # Check return value and method call
            self.assertEqual(result, "light")
            mock_apply.assert_called_once_with("light")

    def test_get_current_theme_and_colors(self):
        """Test get_current_theme and get_theme_colors methods."""
        # Test with light theme
        self.theme_manager._current_theme = "light"
        self.assertEqual(self.theme_manager.get_current_theme(), "light")
        colors = self.theme_manager.get_theme_colors()
        self.assertEqual(colors["background"], "#ffffff")
        
        # Test with dark theme
        self.theme_manager._current_theme = "dark"
        self.assertEqual(self.theme_manager.get_current_theme(), "dark")
        colors = self.theme_manager.get_theme_colors()
        self.assertEqual(colors["background"], "#2d2d2d")

    def test_configure_ttk_style(self):
        """Test _configure_ttk_style method."""
        # Initialize the theme manager
        self.theme_manager.initialize(self.root)
        mock_style = MagicMock()
        self.theme_manager._style = mock_style
        
        # Get light theme colors
        colors = ThemeManager.LIGHT_THEME
        
        # Call configure method
        self.theme_manager._configure_ttk_style(colors)
        
        # Verify style configuration calls
        mock_style.theme_use.assert_called_once_with("clam")
        
        # Check that all widget styles were configured
        mock_style.configure.assert_any_call(".", 
            background=colors["background"],
            foreground=colors["foreground"],
            fieldbackground=colors["field_bg"],
            troughcolor=colors["border"],
            bordercolor=colors["border"],
            darkcolor=colors["border"],
            lightcolor=colors["background"],
            selectbackground=colors["highlight"],
            selectforeground=colors["highlight_text"],
            selectborderwidth=0,
            relief="flat"
        )
        
        # Check that specific widget styles were configured
        self.assertEqual(mock_style.configure.call_count, 14)  # Should be called for multiple widgets
        
        # Check that style mapping was set for some widgets
        self.assertEqual(mock_style.map.call_count, 5)  # Should be called for multiple widgets

    def test_apply_text_widget_theme(self):
        """Test apply_text_widget_theme method."""
        # Initialize the theme manager with light theme
        self.theme_manager.initialize(self.root)
        self.theme_manager._current_theme = "light"
        
        # Create a text widget
        text_widget = tk.Text(self.root)
        
        # Apply theme to text widget
        with patch.object(self.theme_manager, 'get_theme_colors', return_value=ThemeManager.LIGHT_THEME) as mock_get_colors:
            self.theme_manager.apply_text_widget_theme(text_widget)
            
            # Check that get_theme_colors was called
            mock_get_colors.assert_called_once()
        
        # Check that the text widget was configured with the correct colors
        self.assertEqual(text_widget["background"], ThemeManager.LIGHT_THEME["text_background"])
        self.assertEqual(text_widget["foreground"], ThemeManager.LIGHT_THEME["text_foreground"])
        self.assertEqual(text_widget["selectbackground"], ThemeManager.LIGHT_THEME["highlight"])
        self.assertEqual(text_widget["selectforeground"], ThemeManager.LIGHT_THEME["highlight_text"])
        self.assertEqual(text_widget["insertbackground"], ThemeManager.LIGHT_THEME["foreground"])

    def test_apply_menu_theme(self):
        """Test apply_menu_theme method."""
        # Initialize the theme manager with light theme
        self.theme_manager.initialize(self.root)
        self.theme_manager._current_theme = "light"
        
        # Create menu hierarchy
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar)
        edit_menu = tk.Menu(menu_bar)
        submenu = tk.Menu(file_menu)
        
        # Add menus to hierarchy
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        file_menu.add_cascade(label="Submenu", menu=submenu)
        
        # Apply theme to menu bar
        with patch.object(self.theme_manager, 'get_theme_colors', return_value=ThemeManager.LIGHT_THEME) as mock_get_colors:
            self.theme_manager.apply_menu_theme(menu_bar)
            
            # Check that get_theme_colors was called
            mock_get_colors.assert_called_once()
        
        # Check that all menus were configured with the correct colors
        self.assertEqual(menu_bar["background"], ThemeManager.LIGHT_THEME["menu_bg"])
        self.assertEqual(menu_bar["foreground"], ThemeManager.LIGHT_THEME["menu_fg"])
        self.assertEqual(file_menu["background"], ThemeManager.LIGHT_THEME["menu_bg"])
        self.assertEqual(edit_menu["background"], ThemeManager.LIGHT_THEME["menu_bg"])
        self.assertEqual(submenu["background"], ThemeManager.LIGHT_THEME["menu_bg"])

    def test_find_widgets_by_class(self):
        """Test _find_widgets_by_class method."""
        # Create a hierarchy of widgets
        frame = tk.Frame(self.root)
        text1 = tk.Text(frame)
        text2 = tk.Text(self.root)
        button = tk.Button(frame)
        
        # Find Text widgets
        text_widgets = self.theme_manager._find_widgets_by_class(self.root, tk.Text)
        
        # Should find both text widgets
        self.assertEqual(len(text_widgets), 2)
        self.assertIn(text1, text_widgets)
        self.assertIn(text2, text_widgets)
        
        # Find Button widgets
        button_widgets = self.theme_manager._find_widgets_by_class(self.root, tk.Button)
        
        # Should find one button
        self.assertEqual(len(button_widgets), 1)
        self.assertIn(button, button_widgets)
        
        # Test with widget raising TclError
        with patch('tkinter.Widget.winfo_children', side_effect=TclError):
            # Should handle the exception gracefully
            result = self.theme_manager._find_widgets_by_class(self.root, tk.Text)
            self.assertEqual(result, [])

    @patch('markitdown_ui.theme.ThemeManager._configure_ttk_style')
    @patch('markitdown_ui.theme.ThemeManager._configure_tk_widgets')
    def test_theme_preference_saving(self, mock_configure_tk, mock_configure_ttk):
        """Test that theme changes are saved to preferences."""
        # Initialize the theme manager
        self.theme_manager.initialize(self.root)
        
        # Apply theme
        self.theme_manager.apply_theme("dark")
        
        # Check that theme was saved to preferences
        self.mock_prefs.set_theme.assert_called_once_with("dark")
        
        # Toggle theme
        self.theme_manager.toggle_theme()
        
        # Check that new theme was saved
        self.mock_prefs.set_theme.assert_called_with("light")


if __name__ == '__main__':
    unittest.main()