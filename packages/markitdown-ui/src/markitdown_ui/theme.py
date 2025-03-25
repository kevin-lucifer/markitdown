#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Theme manager for MarkItDown UI application."""

import tkinter as tk
from tkinter import ttk, font
from typing import Dict, Any, Optional

from markitdown_ui.preferences import PreferencesManager


class ThemeManager:
    """Manager for handling application theme switching and styling."""
    
    _instance: Optional["ThemeManager"] = None
    
    # Light theme colors
    LIGHT_THEME = {
        "background": "#ffffff",
        "foreground": "#000000",
        "text_background": "#ffffff",
        "text_foreground": "#000000",
        "accent": "#0078d7",
        "border": "#d1d1d1",
        "button": "#f0f0f0",
        "button_pressed": "#d8d8d8",
        "highlight": "#e5f1fb",
        "highlight_text": "#000000",
        "disabled_bg": "#f0f0f0",
        "disabled_fg": "#a0a0a0",
        "status_bar_bg": "#f0f0f0",
        "status_bar_fg": "#000000",
        "toolbar_bg": "#f5f5f5",
        "toolbar_fg": "#000000",
        "menu_bg": "#ffffff",
        "menu_fg": "#000000",
        "field_bg": "#ffffff",
        "field_fg": "#000000",
        "field_highlight_bg": "#e5f1fb",
        "scrollbar_bg": "#f0f0f0",
        "scrollbar_fg": "#c0c0c0"
    }
    
    # Dark theme colors
    DARK_THEME = {
        "background": "#2d2d2d",
        "foreground": "#e0e0e0",
        "text_background": "#333333",
        "text_foreground": "#e0e0e0",
        "accent": "#0078d7",
        "border": "#555555",
        "button": "#3d3d3d",
        "button_pressed": "#4d4d4d",
        "highlight": "#264f78",
        "highlight_text": "#ffffff",
        "disabled_bg": "#3d3d3d",
        "disabled_fg": "#767676",
        "status_bar_bg": "#3d3d3d",
        "status_bar_fg": "#e0e0e0",
        "toolbar_bg": "#333333",
        "toolbar_fg": "#e0e0e0",
        "menu_bg": "#2d2d2d",
        "menu_fg": "#e0e0e0",
        "field_bg": "#333333",
        "field_fg": "#e0e0e0",
        "field_highlight_bg": "#264f78",
        "scrollbar_bg": "#3d3d3d",
        "scrollbar_fg": "#5d5d5d"
    }
    
    def __new__(cls) -> "ThemeManager":
        """Create a singleton instance of ThemeManager.
        
        Returns:
            The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the theme manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self._preferences = PreferencesManager()
        self._current_theme = self._preferences.get_theme()
        self._style = None
        self._root = None
        
    def initialize(self, root: tk.Tk) -> None:
        """Initialize the theme manager with the root window.
        
        Args:
            root: The root window of the application
        """
        self._root = root
        self._style = ttk.Style(root)
        
        # Apply the initial theme
        self.apply_theme(self._current_theme)
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply the specified theme to the application.
        
        Args:
            theme_name: Name of the theme to apply ('light' or 'dark')
        """
        if self._root is None:
            raise RuntimeError("Theme manager not initialized with root window")
            
        self._current_theme = theme_name
        colors = self.LIGHT_THEME if theme_name == "light" else self.DARK_THEME
        
        # Configure ttk style
        self._configure_ttk_style(colors)
        
        # Configure standard tkinter widgets that don't use ttk styling
        self._configure_tk_widgets(colors)
        
        # Save the theme preference
        self._preferences.set_theme(theme_name)
        
    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.
        
        Returns:
            The new theme name
        """
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme
    
    def get_current_theme(self) -> str:
        """Get the name of the current theme.
        
        Returns:
            Current theme name ('light' or 'dark')
        """
        return self._current_theme
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get the color dictionary for the current theme.
        
        Returns:
            Dictionary of theme colors
        """
        return self.LIGHT_THEME if self._current_theme == "light" else self.DARK_THEME
    
    def _configure_ttk_style(self, colors: Dict[str, str]) -> None:
        """Configure ttk style with the given colors.
        
        Args:
            colors: Dictionary of colors to apply
        """
        # Configure the ttk theme
        if self._style is None:
            return
            
        # Use clam as base theme as it's the most configurable
        self._style.theme_use("clam")
        
        # Configure common elements
        self._style.configure(".", 
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
        
        # TButton
        self._style.configure("TButton",
            background=colors["button"],
            foreground=colors["foreground"],
            bordercolor=colors["border"],
            lightcolor=colors["button"],
            darkcolor=colors["button_pressed"],
            padding=6
        )
        self._style.map("TButton",
            background=[("active", colors["button_pressed"]), ("pressed", colors["button_pressed"])],
            foreground=[("disabled", colors["disabled_fg"])]
        )
        
        # TEntry
        self._style.configure("TEntry",
            fieldbackground=colors["field_bg"],
            foreground=colors["field_fg"],
            bordercolor=colors["border"],
            lightcolor=colors["field_bg"],
            selectbackground=colors["field_highlight_bg"],
            selectforeground=colors["highlight_text"],
            padding=5
        )
        
        # TCheckbutton
        self._style.configure("TCheckbutton",
            background=colors["background"],
            foreground=colors["foreground"],
            indicatorbackground=colors["field_bg"],
            indicatorforeground=colors["accent"],
            padding=5
        )
        self._style.map("TCheckbutton",
            background=[("active", colors["background"])],
            foreground=[("disabled", colors["disabled_fg"])],
            indicatorbackground=[("disabled", colors["disabled_bg"])]
        )
        
        # TRadiobutton
        self._style.configure("TRadiobutton",
            background=colors["background"],
            foreground=colors["foreground"],
            indicatorbackground=colors["field_bg"],
            indicatorforeground=colors["accent"],
            padding=5
        )
        self._style.map("TRadiobutton",
            background=[("active", colors["background"])],
            foreground=[("disabled", colors["disabled_fg"])],
            indicatorbackground=[("disabled", colors["disabled_bg"])]
        )
        
        # TProgressbar
        self._style.configure("TProgressbar",
            background=colors["accent"],
            troughcolor=colors["border"],
            bordercolor=colors["border"],
            lightcolor=colors["accent"],
            darkcolor=colors["accent"]
        )
        
        # TFrame
        self._style.configure("TFrame",
            background=colors["background"]
        )
        
        # TLabelframe
        self._style.configure("TLabelframe",
            background=colors["background"],
            foreground=colors["foreground"],
            bordercolor=colors["border"],
            lightcolor=colors["background"],
            darkcolor=colors["background"]
        )
        self._style.configure("TLabelframe.Label",
            background=colors["background"],
            foreground=colors["foreground"]
        )
        
        # TLabel
        self._style.configure("TLabel",
            background=colors["background"],
            foreground=colors["foreground"],
            padding=5
        )
        
        # Scrollbar
        self._style.configure("TScrollbar",
            background=colors["scrollbar_bg"],
            troughcolor=colors["scrollbar_bg"],
            bordercolor=colors["border"],
            arrowcolor=colors["foreground"],
            gripcount=0
        )
        self._style.map("TScrollbar",
            background=[("active", colors["scrollbar_fg"]), ("pressed", colors["scrollbar_fg"])]
        )
        
        # Notebook
        self._style.configure("TNotebook",
            background=colors["background"],
            bordercolor=colors["border"],
            lightcolor=colors["background"],
            darkcolor=colors["background"]
        )
        self._style.configure("TNotebook.Tab",
            background=colors["button"],
            foreground=colors["foreground"],
            padding=[8, 4]
        )
        self._style.map("TNotebook.Tab",
            background=[("selected", colors["background"]), ("active", colors["highlight"])],
            foreground=[("selected", colors["foreground"])]
        )
        
        # Toolbar style
        self._style.configure("Toolbar.TFrame",
            background=colors["toolbar_bg"]
        )
        
        # Toolbar button style
        self._style.configure("Toolbar.TButton",
            background=colors["toolbar_bg"],
            foreground=colors["toolbar_fg"],
            bordercolor=colors["toolbar_bg"],
            lightcolor=colors["toolbar_bg"],
            darkcolor=colors["toolbar_bg"],
            relief="flat",
            padding=4
        )
        self._style.map("Toolbar.TButton",
            background=[("active", colors["button_pressed"]), ("pressed", colors["button_pressed"])],
            relief=[("pressed", "sunken"), ("active", "raised")]
        )
        
        # Status bar style
        self._style.configure("StatusBar.TLabel",
            background=colors["status_bar_bg"],
            foreground=colors["status_bar_fg"],
            padding=2
        )
        
    def _configure_tk_widgets(self, colors: Dict[str, str]) -> None:
        """Configure standard tkinter widgets that don't use ttk styling.
        
        Args:
            colors: Dictionary of colors to apply
        """
        if self._root is None:
            return
        
        # Configure the root window
        self._root.configure(background=colors["background"])
        
        # Configure standard Text widget options
        text_opts = {
            "background": colors["text_background"],
            "foreground": colors["text_foreground"],
            "selectbackground": colors["highlight"],
            "selectforeground": colors["highlight_text"],
            "insertbackground": colors["foreground"],  # Cursor color
            "highlightbackground": colors["border"],
            "highlightcolor": colors["accent"],
            "relief": "sunken",
            "borderwidth": 1
        }
        
        # Configure Menu widget options
        menu_opts = {
            "background": colors["menu_bg"],
            "foreground": colors["menu_fg"],
            "activebackground": colors["highlight"],
            "activeforeground": colors["highlight_text"],
            "selectcolor": colors["accent"],
            "borderwidth": 1,
            "relief": "raised"
        }
        
        # Update color scheme for text widgets
        for text_widget in self._find_widgets_by_class(self._root, tk.Text):
            for opt, val in text_opts.items():
                try:
                    text_widget[opt] = val
                except tk.TclError:
                    pass  # Some options might not be available
        
        # Update color scheme for menu widgets
        for menu_widget in self._find_widgets_by_class(self._root, tk.Menu):
            for opt, val in menu_opts.items():
                try:
                    menu_widget[opt] = val
                except tk.TclError:
                    pass  # Some options might not be available
    
    def apply_text_widget_theme(self, text_widget: tk.Text) -> None:
        """Apply the current theme to a text widget.
        
        Args:
            text_widget: Text widget to apply theme to
        """
        colors = self.get_theme_colors()
        
        text_widget.configure(
            background=colors["text_background"],
            foreground=colors["text_foreground"],
            selectbackground=colors["highlight"],
            selectforeground=colors["highlight_text"],
            insertbackground=colors["foreground"],
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"]
        )
    
    def apply_menu_theme(self, menu: tk.Menu) -> None:
        """Apply the current theme to a menu widget.
        
        Args:
            menu: Menu widget to apply theme to
        """
        colors = self.get_theme_colors()
        
        menu.configure(
            background=colors["menu_bg"],
            foreground=colors["menu_fg"],
            activebackground=colors["highlight"],
            activeforeground=colors["highlight_text"],
            selectcolor=colors["accent"]
        )
        
        # Apply theme to all cascaded menus
        for i in range(menu.index("end") + 1 if menu.index("end") is not None else 0):
            if menu.type(i) == "cascade":
                submenu = menu.nametowidget(menu.entrycget(i, "menu"))
                if isinstance(submenu, tk.Menu):
                    self.apply_menu_theme(submenu)
    
    def _find_widgets_by_class(self, parent: tk.Widget, widget_class: type) -> list:
        """Find all widgets of a specific class within a parent widget.
        
        Args:
            parent: Parent widget to search in
            widget_class: Class of widgets to find
            
        Returns:
            List of found widgets
        """
        result = []
        
        if isinstance(parent, widget_class):
            result.append(parent)
        
        try:
            for child in parent.winfo_children():
                result.extend(self._find_widgets_by_class(child, widget_class))
        except (AttributeError, tk.TclError):
            pass  # Some widgets don't have children
            
        return result