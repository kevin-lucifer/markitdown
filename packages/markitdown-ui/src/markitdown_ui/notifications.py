#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Notification system for MarkItDown UI application."""

import enum
import logging
import queue
import sys
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Union, Any

from markitdown_ui.theme import ThemeManager


class NotificationType(enum.Enum):
    """Types of notifications with different severity levels."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class Notification:
    """Class representing a single notification message."""
    type: NotificationType
    message: str
    details: Optional[str] = None
    timestamp: datetime = None
    id: Optional[str] = None
    dismissed: bool = False
    auto_dismiss_after: Optional[int] = None  # Seconds after which notification auto-dismisses
    source: Optional[str] = None  # Source of the notification (e.g., "converter", "console")
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
        if self.id is None:
            # Create a simple ID based on timestamp and message
            self.id = f"{int(time.time())}-{hash(self.message) % 10000}"


class NotificationManager:
    """Manager for handling notifications in the application."""
    
    _instance: Optional["NotificationManager"] = None
    
    def __new__(cls) -> "NotificationManager":
        """Create or return the singleton instance of NotificationManager.
        
        Returns:
            The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the notification manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self._notifications: List[Notification] = []  # History of all notifications
        self._active_notifications: Dict[str, Notification] = {}  # Currently active notifications
        self._notification_queue = queue.Queue()  # Queue for pending notifications
        self._display_callbacks: List[Callable[[Notification], None]] = []  # Callbacks for display
        self._dismiss_callbacks: List[Callable[[Notification], None]] = []  # Callbacks for dismiss
        self._theme_manager = ThemeManager()
        self._max_history = 100  # Maximum number of notifications to keep in history
        self._console_logger = None
        self._logging_setup_complete = False
        self._popup_windows: Dict[str, Any] = {}  # Store references to popup windows
        
    def initialize(self, root: tk.Tk) -> None:
        """Initialize the notification manager with the root window.
        
        Args:
            root: The root window of the application
        """
        self._root = root
        self._setup_logging()
        
        # Start processing the notification queue periodically
        self._process_notification_queue()
        
    def _setup_logging(self) -> None:
        """Set up logging handlers to capture console output."""
        if self._logging_setup_complete:
            return
            
        # Create a logger for the application
        self._console_logger = logging.getLogger('markitdown_ui')
        self._console_logger.setLevel(logging.INFO)
        
        # Create a handler for the logger that will forward to our notification system
        class NotificationLogHandler(logging.Handler):
            def __init__(self, notification_callback):
                super().__init__()
                self.notification_callback = notification_callback
                
            def emit(self, record):
                msg = self.format(record)
                
                # Determine notification type based on log level
                if record.levelno >= logging.ERROR:
                    notification_type = NotificationType.ERROR
                elif record.levelno >= logging.WARNING:
                    notification_type = NotificationType.WARNING
                else:
                    notification_type = NotificationType.INFO
                    
                # Forward to notification system
                self.notification_callback(notification_type, msg, source="console")
        
        # Add the custom handler to our logger
        handler = NotificationLogHandler(self.add_from_console)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        self._console_logger.addHandler(handler)
        
        self._logging_setup_complete = True
    
    def _process_notification_queue(self) -> None:
        """Process the notification queue and display notifications."""
        try:
            # Process all pending notifications
            while not self._notification_queue.empty():
                notification = self._notification_queue.get_nowait()
                
                # Add to active notifications
                self._active_notifications[notification.id] = notification
                
                # Add to history
                self._notifications.append(notification)
                if len(self._notifications) > self._max_history:
                    self._notifications.pop(0)
                
                # Call display callbacks
                for callback in self._display_callbacks:
                    try:
                        callback(notification)
                    except Exception as e:
                        print(f"Error in notification display callback: {e}")
                        
                # Set auto-dismiss timer if specified
                if notification.auto_dismiss_after is not None:
                    if hasattr(self, '_root') and self._root is not None:
                        self._root.after(
                            int(notification.auto_dismiss_after * 1000),
                            lambda n=notification: self.dismiss(n.id)
                        )
        except Exception as e:
            print(f"Error processing notification queue: {e}")
        
        # Schedule next processing if root window exists
        if hasattr(self, '_root') and self._root is not None:
            self._root.after(100, self._process_notification_queue)
    
    def register_display_callback(self, callback: Callable[[Notification], None]) -> None:
        """Register a callback function to be called when a notification is displayed.
        
        Args:
            callback: Function that takes a Notification object as parameter
        """
        if callback not in self._display_callbacks:
            self._display_callbacks.append(callback)
    
    def register_dismiss_callback(self, callback: Callable[[Notification], None]) -> None:
        """Register a callback function to be called when a notification is dismissed.
        
        Args:
            callback: Function that takes a Notification object as parameter
        """
        if callback not in self._dismiss_callbacks:
            self._dismiss_callbacks.append(callback)
    
    def add_notification(
        self,
        type_: NotificationType,
        message: str,
        details: Optional[str] = None,
        auto_dismiss_after: Optional[int] = None,
        source: Optional[str] = None
    ) -> str:
        """Add a new notification to the queue.
        
        Args:
            type_: Type of notification (info, warning, error, success)
            message: Main notification message
            details: Optional detailed information
            auto_dismiss_after: Seconds after which notification auto-dismisses, or None
            source: Source of the notification (e.g., "converter", "console")
            
        Returns:
            ID of the created notification
        """
        notification = Notification(
            type=type_,
            message=message,
            details=details,
            auto_dismiss_after=auto_dismiss_after,
            source=source
        )
        
        # Add to queue for processing
        self._notification_queue.put(notification)
        
        return notification.id
    
    def add_info(
        self,
        message: str,
        details: Optional[str] = None,
        auto_dismiss_after: int = 5,
        source: Optional[str] = None
    ) -> str:
        """Add an informational notification.
        
        Args:
            message: Main notification message
            details: Optional detailed information
            auto_dismiss_after: Seconds after which notification auto-dismisses
            source: Source of the notification
            
        Returns:
            ID of the created notification
        """
        return self.add_notification(
            NotificationType.INFO,
            message,
            details,
            auto_dismiss_after,
            source
        )
    
    def add_warning(
        self,
        message: str,
        details: Optional[str] = None,
        auto_dismiss_after: Optional[int] = 10,
        source: Optional[str] = None
    ) -> str:
        """Add a warning notification.
        
        Args:
            message: Main notification message
            details: Optional detailed information
            auto_dismiss_after: Seconds after which notification auto-dismisses, or None
            source: Source of the notification
            
        Returns:
            ID of the created notification
        """
        return self.add_notification(
            NotificationType.WARNING,
            message,
            details,
            auto_dismiss_after,
            source
        )
    
    def add_error(
        self,
        message: str,
        details: Optional[str] = None,
        auto_dismiss_after: Optional[int] = None,  # Errors don't auto-dismiss by default
        source: Optional[str] = None
    ) -> str:
        """Add an error notification.
        
        Args:
            message: Main notification message
            details: Optional detailed information
            auto_dismiss_after: Seconds after which notification auto-dismisses, or None
            source: Source of the notification
            
        Returns:
            ID of the created notification
        """
        return self.add_notification(
            NotificationType.ERROR,
            message,
            details,
            auto_dismiss_after,
            source
        )
    
    def add_success(
        self,
        message: str,
        details: Optional[str] = None,
        auto_dismiss_after: int = 5,
        source: Optional[str] = None
    ) -> str:
        """Add a success notification.
        
        Args:
            message: Main notification message
            details: Optional detailed information
            auto_dismiss_after: Seconds after which notification auto-dismisses
            source: Source of the notification
            
        Returns:
            ID of the created notification
        """
        return self.add_notification(
            NotificationType.SUCCESS,
            message,
            details,
            auto_dismiss_after,
            source
        )
    
    def add_from_console(
        self,
        type_: NotificationType,
        message: str,
        source: str = "console"
    ) -> str:
        """Add a notification from console output.
        
        Args:
            type_: Type of notification
            message: Console message
            source: Source identifier
            
        Returns:
            ID of the created notification
        """
        # Define auto-dismiss durations based on type
        auto_dismiss_map = {
            NotificationType.INFO: 5,
            NotificationType.WARNING: 10,
            NotificationType.ERROR: None,  # Errors don't auto-dismiss
            NotificationType.SUCCESS: 5
        }
        
        return self.add_notification(
            type_,
            message,
            auto_dismiss_after=auto_dismiss_map.get(type_),
            source=source
        )
    
    def add_from_exception(
        self,
        exception: Exception,
        message: Optional[str] = None,
        auto_dismiss_after: Optional[int] = None,
        source: Optional[str] = None
    ) -> str:
        """Add an error notification from an exception.
        
        Args:
            exception: The exception object
            message: Optional custom message, uses str(exception) if None
            auto_dismiss_after: Seconds after which notification auto-dismisses
            source: Source of the notification
            
        Returns:
            ID of the created notification
        """
        if message is None:
            message = str(exception)
            
        return self.add_error(
            message,
            details=f"{exception.__class__.__name__}: {str(exception)}",
            auto_dismiss_after=auto_dismiss_after,
            source=source
        )
    
    def dismiss(self, notification_id: str) -> bool:
        """Dismiss a notification by ID.
        
        Args:
            notification_id: ID of the notification to dismiss
            
        Returns:
            True if notification was found and dismissed, False otherwise
        """
        if notification_id in self._active_notifications:
            notification = self._active_notifications[notification_id]
            notification.dismissed = True
            
            # Remove from active notifications
            del self._active_notifications[notification_id]
            
            # Call dismiss callbacks
            for callback in self._dismiss_callbacks:
                try:
                    callback(notification)
                except Exception as e:
                    print(f"Error in notification dismiss callback: {e}")
            
            # Close popup window if it exists
            if notification_id in self._popup_windows:
                try:
                    self._popup_windows[notification_id].destroy()
                except tk.TclError:
                    pass  # Window was already closed
                del self._popup_windows[notification_id]
                
            return True
            
        return False
    
    def dismiss_all(self, type_: Optional[NotificationType] = None) -> int:
        """Dismiss all notifications or all of a specific type.
        
        Args:
            type_: Optional type of notifications to dismiss, or None for all
            
        Returns:
            Number of notifications dismissed
        """
        # Create a copy of IDs to avoid modifying dictionary during iteration
        ids_to_dismiss = [
            notification_id for notification_id, notification in self._active_notifications.items()
            if type_ is None or notification.type == type_
        ]
        
        count = 0
        for notification_id in ids_to_dismiss:
            if self.dismiss(notification_id):
                count += 1
                
        return count
    
    def get_active_notifications(self, type_: Optional[NotificationType] = None) -> List[Notification]:
        """Get all active notifications or all of a specific type.
        
        Args:
            type_: Optional type of notifications to get, or None for all
            
        Returns:
            List of active notifications, newest first
        """
        result = [
            notification for notification in self._active_notifications.values()
            if type_ is None or notification.type == type_
        ]
        
        # Sort by timestamp, newest first
        result.sort(key=lambda n: n.timestamp, reverse=True)
        return result
    
    def get_notification_history(self, type_: Optional[NotificationType] = None) -> List[Notification]:
        """Get the notification history or history of a specific type.
        
        Args:
            type_: Optional type of notifications to get, or None for all
            
        Returns:
            List of historical notifications, newest first
        """
        result = [
            notification for notification in self._notifications
            if type_ is None or notification.type == type_
        ]
        
        # Sort by timestamp, newest first
        result.sort(key=lambda n: n.timestamp, reverse=True)
        return result
    
    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by its ID.
        
        Args:
            notification_id: ID of the notification to get
            
        Returns:
            The notification if found, None otherwise
        """
        # Check active notifications first
        if notification_id in self._active_notifications:
            return self._active_notifications[notification_id]
            
        # Check history
        for notification in self._notifications:
            if notification.id == notification_id:
                return notification
                
        return None
    
    def clear_history(self) -> None:
        """Clear the notification history while preserving active notifications."""
        active_ids = set(self._active_notifications.keys())
        
        # Keep only active notifications in history
        self._notifications = [n for n in self._notifications if n.id in active_ids]
    
    def get_notification_count(self, type_: Optional[NotificationType] = None) -> int:
        """Get the count of active notifications of a specific type.
        
        Args:
            type_: Optional type of notifications to count, or None for all
            
        Returns:
            Number of active notifications
        """
        if type_ is None:
            return len(self._active_notifications)
            
        return sum(1 for n in self._active_notifications.values() if n.type == type_)
    
    def register_popup_window(self, notification_id: str, window: Any) -> None:
        """Register a popup window for a notification.
        
        Args:
            notification_id: ID of the notification
            window: Window object
        """
        self._popup_windows[notification_id] = window
    
    def get_color_for_type(self, type_: NotificationType) -> Dict[str, str]:
        """Get color scheme for notification type based on current theme.
        
        Args:
            type_: The notification type
            
        Returns:
            Dictionary with background, foreground, border and icon colors
        """
        theme_colors = self._theme_manager.get_theme_colors()
        
        # Default colors
        colors = {
            "background": theme_colors["background"],
            "foreground": theme_colors["foreground"],
            "border": theme_colors["border"],
            "icon": theme_colors["foreground"]
        }
        
        # Override based on notification type
        if type_ == NotificationType.INFO:
            colors["background"] = theme_colors["field_bg"]
            colors["border"] = theme_colors["accent"]
            colors["icon"] = theme_colors["accent"]
            
        elif type_ == NotificationType.WARNING:
            colors["background"] = "#fff3cd" if self._theme_manager.get_current_theme() == "light" else "#332b00"
            colors["foreground"] = "#664d03" if self._theme_manager.get_current_theme() == "light" else "#ffda6a"
            colors["border"] = "#ffecb5" if self._theme_manager.get_current_theme() == "light" else "#664d03"
            colors["icon"] = "#664d03" if self._theme_manager.get_current_theme() == "light" else "#ffda6a"
            
        elif type_ == NotificationType.ERROR:
            colors["background"] = "#f8d7da" if self._theme_manager.get_current_theme() == "light" else "#2c0b0e"
            colors["foreground"] = "#842029" if self._theme_manager.get_current_theme() == "light" else "#ea868f"
            colors["border"] = "#f5c2c7" if self._theme_manager.get_current_theme() == "light" else "#842029"
            colors["icon"] = "#842029" if self._theme_manager.get_current_theme() == "light" else "#ea868f"
            
        elif type_ == NotificationType.SUCCESS:
            colors["background"] = "#d1e7dd" if self._theme_manager.get_current_theme() == "light" else "#0f5132"
            colors["foreground"] = "#0f5132" if self._theme_manager.get_current_theme() == "light" else "#a3cfbb"
            colors["border"] = "#badbcc" if self._theme_manager.get_current_theme() == "light" else "#146c43"
            colors["icon"] = "#0f5132" if self._theme_manager.get_current_theme() == "light" else "#a3cfbb"
            
        return colors