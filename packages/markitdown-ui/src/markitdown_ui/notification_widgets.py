#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Notification widgets for MarkItDown UI application."""

import tkinter as tk
from tkinter import ttk, font
import time
from typing import Callable, Dict, List, Optional, Tuple, Any

from markitdown_ui.theme import ThemeManager
from markitdown_ui.notifications import NotificationManager, NotificationType, Notification


class NotificationPopup(tk.Toplevel):
    """Popup window for displaying notifications."""
    
    def __init__(
        self,
        parent: tk.Tk,
        notification: Notification,
        on_dismiss: Optional[Callable[[str], None]] = None
    ) -> None:
        """Initialize the notification popup.
        
        Args:
            parent: Parent window
            notification: The notification to display
            on_dismiss: Optional callback when notification is dismissed
        """
        super().__init__(parent)
        self.parent = parent
        self.notification = notification
        self.on_dismiss = on_dismiss
        self.theme_manager = ThemeManager()
        self.notification_manager = NotificationManager()
        
        # Configure window
        self.overrideredirect(True)  # No window decorations
        self.attributes("-topmost", True)  # Keep on top
        self.withdraw()  # Hide initially
        
        # Set initial transparency (for animation)
        self.attributes("-alpha", 0.0)
        
        # Get colors for notification type
        colors = self.notification_manager.get_color_for_type(notification.type)
        
        # Create main frame
        self.main_frame = tk.Frame(self, bd=1, relief="solid", bg=colors["background"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame["borderwidth"] = 1
        self.main_frame["highlightthickness"] = 1
        self.main_frame["highlightbackground"] = colors["border"]
        
        # Create header with icon and close button
        self.header_frame = tk.Frame(self.main_frame, bg=colors["background"])
        self.header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Icon based on notification type
        icon_text = self._get_icon_for_type(notification.type)
        icon_label = tk.Label(
            self.header_frame, 
            text=icon_text, 
            bg=colors["background"], 
            fg=colors["icon"],
            font=("Helvetica", 14, "bold")
        )
        icon_label.pack(side=tk.LEFT, padx=(5, 10))
        
        # Type label (e.g., "Warning", "Error")
        type_label = tk.Label(
            self.header_frame,
            text=notification.type.name.capitalize(),
            bg=colors["background"],
            fg=colors["foreground"],
            font=("Helvetica", 10, "bold")
        )
        type_label.pack(side=tk.LEFT)
        
        # Close button
        close_button = tk.Label(
            self.header_frame,
            text="✕",
            bg=colors["background"],
            fg=colors["foreground"],
            cursor="hand2"
        )
        close_button.pack(side=tk.RIGHT, padx=5)
        close_button.bind("<Button-1>", self._on_close_click)
        
        # Message
        message_frame = tk.Frame(self.main_frame, bg=colors["background"])
        message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        message_label = tk.Label(
            message_frame,
            text=notification.message,
            bg=colors["background"],
            fg=colors["foreground"],
            justify=tk.LEFT,
            wraplength=350  # Wrap text for better readability
        )
        message_label.pack(anchor="w")
        
        # Details (if provided)
        if notification.details:
            details_frame = tk.Frame(self.main_frame, bg=colors["background"])
            details_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            
            details_text = tk.Text(
                details_frame,
                bg=colors["background"],
                fg=colors["foreground"],
                height=3,
                width=40,
                wrap=tk.WORD,
                relief=tk.FLAT,
                font=("Helvetica", 9)
            )
            details_text.insert(tk.END, notification.details)
            details_text.config(state=tk.DISABLED)  # Make read-only
            details_text.pack(fill=tk.X)
            
        # Source info (if provided)
        if notification.source:
            source_label = tk.Label(
                self.main_frame,
                text=f"Source: {notification.source}",
                bg=colors["background"],
                fg=colors["foreground"],
                font=("Helvetica", 8),
                anchor="e"
            )
            source_label.pack(side=tk.RIGHT, padx=10, pady=(0, 5))
        
        # Register with notification manager
        self.notification_manager.register_popup_window(notification.id, self)
        
        # Position the popup
        self.position_popup()
        
        # Set up auto-dismiss timer if specified
        if notification.auto_dismiss_after is not None:
            self.after(int(notification.auto_dismiss_after * 1000), self._auto_dismiss)
        
        # Show the popup with animation
        self.show_with_animation()
    
    def _get_icon_for_type(self, type_: NotificationType) -> str:
        """Get icon symbol for notification type.
        
        Args:
            type_: Notification type
            
        Returns:
            String with icon symbol
        """
        if type_ == NotificationType.INFO:
            return "ℹ"
        elif type_ == NotificationType.WARNING:
            return "⚠"
        elif type_ == NotificationType.ERROR:
            return "❌"
        elif type_ == NotificationType.SUCCESS:
            return "✓"
        return "•"
    
    def position_popup(self) -> None:
        """Position the popup window in the bottom right corner of the parent window."""
        # Get parent window position and size
        x = self.parent.winfo_x()
        y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get notification count to stack notifications
        count = self.notification_manager.get_notification_count()
        offset = (count - 1) * 40  # Stagger popups by 40 pixels per notification
        
        # Set popup width
        popup_width = 400
        
        # Update the geometry
        self.geometry(f"{popup_width}x0")  # Set width, start with height 0
        
        # Show briefly to calculate required height, then hide again
        self.update_idletasks()
        popup_height = self.winfo_reqheight()
        
        # Calculate position (bottom right of parent window with offset)
        popup_x = x + parent_width - popup_width - 20
        popup_y = y + parent_height - popup_height - 40 - offset
        
        # Set final geometry
        self.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
    
    def show_with_animation(self) -> None:
        """Show the popup with a fade-in animation."""
        self.deiconify()  # Show the window
        
        # Animated fade-in
        for alpha in range(0, 11):
            self.attributes("-alpha", alpha/10)
            self.update()
            time.sleep(0.02)  # Short delay for animation
    
    def hide_with_animation(self) -> None:
        """Hide the popup with a fade-out animation."""
        # Animated fade-out
        for alpha in range(10, -1, -1):
            self.attributes("-alpha", alpha/10)
            self.update()
            time.sleep(0.01)  # Short delay for animation
        
        self.withdraw()  # Hide the window
    
    def _on_close_click(self, event=None) -> None:
        """Handle close button click.
        
        Args:
            event: Click event (optional)
        """
        self.hide_with_animation()
        if self.on_dismiss:
            self.on_dismiss(self.notification.id)
        else:
            # Direct dismiss
            self.notification_manager.dismiss(self.notification.id)
    
    def _auto_dismiss(self) -> None:
        """Auto dismiss the notification after timeout."""
        # Only dismiss if window still exists
        try:
            if self.winfo_exists():
                self._on_close_click()
        except tk.TclError:
            pass  # Window already destroyed


class NotificationArea(ttk.Frame):
    """Widget for displaying notification history and indicators in the main UI."""
    
    def __init__(self, parent: tk.Widget, max_displayed: int = 5) -> None:
        """Initialize the notification area.
        
        Args:
            parent: Parent widget
            max_displayed: Maximum number of notifications to display at once
        """
        super().__init__(parent)
        
        self.parent = parent
        self.max_displayed = max_displayed
        self.notification_manager = NotificationManager()
        self.theme_manager = ThemeManager()
        
        # Create indicators frame (for showing counts of different notification types)
        self.indicators_frame = ttk.Frame(self)
        self.indicators_frame.pack(fill=tk.X, pady=2)
        
        # Create indicator for each notification type
        self.indicators: Dict[NotificationType, Dict[str, Any]] = {}
        self._create_indicators()
        
        # Create expanded notifications area (initially hidden)
        self.expanded_frame = ttk.Frame(self)
        self.expanded_frame.pack(fill=tk.BOTH, expand=True)
        self.expanded_frame.pack_forget()  # Initially hidden
        
        # Create notification list inside a scrollable frame
        self.notification_list_frame = ttk.Frame(self.expanded_frame)
        self.notification_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notification_canvas = tk.Canvas(self.notification_list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.notification_list_frame, orient=tk.VERTICAL, 
                                 command=self.notification_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.notification_canvas)
        
        self.notification_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.notification_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a window for the scrollable frame
        self.scrollable_window = self.notification_canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw",
            tags="self.scrollable_frame"
        )
        
        # Configure canvas scrolling
        self.notification_canvas.bind("<Configure>", self._configure_canvas)
        self.scrollable_frame.bind("<Configure>", self._configure_scroll_region)
        
        # Bind mouse wheel for scrolling
        self.notification_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Footer with buttons
        footer_frame = ttk.Frame(self.expanded_frame)
        footer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(footer_frame, text="Clear All", 
                  command=self._clear_all_notifications).pack(side=tk.RIGHT, padx=5)
        ttk.Button(footer_frame, text="Hide", 
                  command=self._toggle_expanded_view).pack(side=tk.RIGHT, padx=5)
        
        # Register callbacks for notification events
        self.notification_manager.register_display_callback(self._on_notification_added)
        self.notification_manager.register_dismiss_callback(self._on_notification_dismissed)
        
        # Initial update
        self._update_indicators()
    
    def _create_indicators(self) -> None:
        """Create indicator labels for each notification type."""
        # Create indicator for each notification type
        for idx, type_ in enumerate(NotificationType):
            frame = ttk.Frame(self.indicators_frame)
            frame.pack(side=tk.LEFT, padx=5)
            
            icon = self._get_icon_for_type(type_)
            icon_label = ttk.Label(
                frame, 
                text=icon,
                cursor="hand2"
            )
            icon_label.pack(side=tk.LEFT)
            
            count_label = ttk.Label(frame, text="0")
            count_label.pack(side=tk.LEFT, padx=(2, 0))
            
            # Store references to labels
            self.indicators[type_] = {
                "frame": frame,
                "icon_label": icon_label,
                "count_label": count_label
            }
            
            # Bind click events to show/hide notifications
            icon_label.bind("<Button-1>", lambda e, t=type_: self._toggle_expanded_view(t))
            count_label.bind("<Button-1>", lambda e, t=type_: self._toggle_expanded_view(t))
    
    def _get_icon_for_type(self, type_: NotificationType) -> str:
        """Get icon symbol for notification type.
        
        Args:
            type_: Notification type
            
        Returns:
            String with icon symbol
        """
        if type_ == NotificationType.INFO:
            return "ℹ"
        elif type_ == NotificationType.WARNING:
            return "⚠"
        elif type_ == NotificationType.ERROR:
            return "❌"
        elif type_ == NotificationType.SUCCESS:
            return "✓"
        return "•"
    
    def _update_indicators(self) -> None:
        """Update notification count indicators."""
        for type_ in NotificationType:
            count = self.notification_manager.get_notification_count(type_)
            self.indicators[type_]["count_label"].configure(text=str(count))
            
            # Update visibility
            if count > 0:
                self.indicators[type_]["frame"].pack(side=tk.LEFT, padx=5)
            else:
                self.indicators[type_]["frame"].pack_forget()
            
            # Apply color styling
            colors = self.notification_manager.get_color_for_type(type_)
            
            # Only apply custom colors if count > 0
            if count > 0:
                self.indicators[type_]["icon_label"].configure(foreground=colors["icon"])
                self.indicators[type_]["count_label"].configure(foreground=colors["foreground"])
            else:
                # Use default theme colors for zero counts
                theme_colors = self.theme_manager.get_theme_colors()
                self.indicators[type_]["icon_label"].configure(foreground=theme_colors["foreground"])
                self.indicators[type_]["count_label"].configure(foreground=theme_colors["foreground"])
    
    def _toggle_expanded_view(self, filter_type: Optional[NotificationType] = None) -> None:
        """Toggle the expanded notifications view.
        
        Args:
            filter_type: Optional filter to show only specific notification types
        """
        if self.expanded_frame.winfo_ismapped():
            self.expanded_frame.pack_forget()
        else:
            # Clear existing notifications first
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            # Show active notifications
            notifications = self.notification_manager.get_active_notifications(filter_type)
            
            if not notifications:
                # Show empty state
                empty_label = ttk.Label(
                    self.scrollable_frame, 
                    text="No active notifications" if filter_type is None else f"No {filter_type.name.lower()} notifications"
                )
                empty_label.pack(pady=10, padx=10)
            else:
                # Show notifications
                for notification in notifications[:self.max_displayed]:
                    self._add_notification_to_list(notification)
                
                # Show "more" indicator if needed
                if len(notifications) > self.max_displayed:
                    more_label = ttk.Label(
                        self.scrollable_frame, 
                        text=f"+ {len(notifications) - self.max_displayed} more notifications"
                    )
                    more_label.pack(pady=(10, 5), padx=10)
            
            # Show the frame
            self.expanded_frame.pack(fill=tk.BOTH, expand=True)
    
    def _add_notification_to_list(self, notification: Notification) -> None:
        """Add a notification to the expanded view list.
        
        Args:
            notification: Notification to add
        """
        colors = self.notification_manager.get_color_for_type(notification.type)
        
        # Create frame for notification
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Create notification entry with icon, message, timestamp
        notification_frame = tk.Frame(
            frame, 
            bg=colors["background"], 
            bd=1, 
            relief="solid",
            highlightbackground=colors["border"],
            highlightthickness=1
        )
        notification_frame.pack(fill=tk.X, expand=True)
        
        # Header with type and timestamp
        header_frame = tk.Frame(notification_frame, bg=colors["background"])
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        # Type label with icon
        icon = self._get_icon_for_type(notification.type)
        type_label = tk.Label(
            header_frame,
            text=f"{icon} {notification.type.name.capitalize()}",
            bg=colors["background"],
            fg=colors["foreground"],
            font=("Helvetica", 9, "bold"),
            anchor="w"
        )
        type_label.pack(side=tk.LEFT)
        
        # Timestamp
        time_str = notification.timestamp.strftime("%H:%M:%S")
        time_label = tk.Label(
            header_frame,
            text=time_str,
            bg=colors["background"],
            fg=colors["foreground"],
            font=("Helvetica", 8),
            anchor="e"
        )
        time_label.pack(side=tk.RIGHT)
        
        # Message
        message_label = tk.Label(
            notification_frame,
            text=notification.message,
            bg=colors["background"],
            fg=colors["foreground"],
            justify=tk.LEFT,
            wraplength=350,
            anchor="w"
        )
        message_label.pack(fill=tk.X, padx=10, pady=(0, 5), anchor="w")
        
        # Dismiss button
        dismiss_button = ttk.Button(
            notification_frame,
            text="Dismiss",
            command=lambda n=notification: self.notification_manager.dismiss(n.id),
            style="small.TButton",
            width=8
        )
        dismiss_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Apply small button style if not already defined
        style = ttk.Style()
        if "small.TButton" not in style.layout():
            style.configure("small.TButton", padding=2, font=("Helvetica", 8))
    
    def _on_notification_added(self, notification: Notification) -> None:
        """Handle new notification added.
        
        Args:
            notification: New notification
        """
        self._update_indicators()
        
        # Update the expanded view if visible
        if self.expanded_frame.winfo_ismapped():
            self._toggle_expanded_view()  # Refresh the view
    
    def _on_notification_dismissed(self, notification: Notification) -> None:
        """Handle notification dismissed.
        
        Args:
            notification: Dismissed notification
        """
        self._update_indicators()
        
        # Update the expanded view if visible
        if self.expanded_frame.winfo_ismapped():
            self._toggle_expanded_view()  # Refresh the view
    
    def _clear_all_notifications(self) -> None:
        """Clear all notifications."""
        self.notification_manager.dismiss_all()
        self._toggle_expanded_view()  # Close the expanded view
    
    def _configure_canvas(self, event) -> None:
        """Configure canvas width when window resizes."""
        self.notification_canvas.itemconfig(self.scrollable_window, width=event.width)
    
    def _configure_scroll_region(self, event) -> None:
        """Configure scrollable region when content changes."""
        self.notification_canvas.configure(scrollregion=self.notification_canvas.bbox("all"))
    
    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling in notification list."""
        # Only process mousewheel events when mouse is over the canvas
        if self._is_mouse_over_canvas(event):
            self.notification_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _is_mouse_over_canvas(self, event) -> bool:
        """Check if mouse is over the canvas during a mousewheel event."""
        x, y = event.x_root, event.y_root
        canvas = self.notification_canvas
        
        # Convert to canvas coordinates
        canvas_x = canvas.winfo_rootx()
        canvas_y = canvas.winfo_rooty()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # Check if mouse is over canvas
        return (
            canvas_x <= x <= canvas_x + canvas_width and
            canvas_y <= y <= canvas_y + canvas_height
        )