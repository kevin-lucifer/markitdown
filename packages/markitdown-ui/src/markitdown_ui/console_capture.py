#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Console capture module for redirecting and monitoring console output."""

import io
import logging
import re
import sys
import threading
from typing import Callable, Dict, List, Optional, Pattern, Set, Tuple, Union, Any

from markitdown_ui.notifications import NotificationManager, NotificationType


class StreamRedirector:
    """Class to redirect and monitor standard output and error streams."""
    
    def __init__(
        self, 
        stream_type: str = "stdout", 
        notification_callback: Optional[Callable[[str, NotificationType], None]] = None
    ) -> None:
        """Initialize stream redirector.
        
        Args:
            stream_type: Type of stream to redirect ("stdout" or "stderr")
            notification_callback: Optional callback for notifications
        """
        self.stream_type = stream_type
        self.notification_callback = notification_callback
        self.notification_manager = NotificationManager()
        
        # Store original stream
        self.original_stream = sys.stdout if stream_type == "stdout" else sys.stderr
        
        # Create buffer to capture output
        self.buffer = io.StringIO()
        
        # Flag to indicate if redirection is active
        self.is_redirecting = False
        
        # Thread lock for thread safety
        self.lock = threading.RLock()
        
        # Define patterns for warning and error detection
        self.warning_patterns = [
            re.compile(r"warning", re.IGNORECASE),
            re.compile(r"warn:", re.IGNORECASE),
            re.compile(r"libpng warning", re.IGNORECASE),
            re.compile(r"deprecation", re.IGNORECASE),
        ]
        
        self.error_patterns = [
            re.compile(r"error", re.IGNORECASE),
            re.compile(r"exception", re.IGNORECASE),
            re.compile(r"fail", re.IGNORECASE),
            re.compile(r"critical", re.IGNORECASE),
        ]
        
        # Define patterns to ignore (false positives or noisy messages)
        self.ignore_patterns = [
            re.compile(r"^\s*$"),  # Empty lines
            re.compile(r"^debug:", re.IGNORECASE),  # Debug messages
        ]
        
        # Create logger for captured output
        self.logger = logging.getLogger(f"markitdown_ui.console_capture.{stream_type}")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler to log captured output if needed
        # Comment out for now, uncomment if file logging is needed
        # log_filename = f"markitdown_ui_{stream_type}.log"
        # file_handler = logging.FileHandler(log_filename)
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        # file_handler.setFormatter(formatter)
        # self.logger.addHandler(file_handler)
    
    def start_redirect(self) -> None:
        """Start redirecting the stream."""
        with self.lock:
            if not self.is_redirecting:
                if self.stream_type == "stdout":
                    sys.stdout = self
                else:
                    sys.stderr = self
                self.is_redirecting = True
    
    def stop_redirect(self) -> None:
        """Stop redirecting the stream and restore original."""
        with self.lock:
            if self.is_redirecting:
                if self.stream_type == "stdout":
                    sys.stdout = self.original_stream
                else:
                    sys.stderr = self.original_stream
                self.is_redirecting = False
    
    def write(self, text: str) -> int:
        """Write to both the original stream and our buffer.
        
        Args:
            text: Text to write
            
        Returns:
            Number of characters written
        """
        with self.lock:
            # Forward to original stream
            if self.original_stream:
                self.original_stream.write(text)
            
            # Also write to our buffer
            self.buffer.write(text)
            
            # Check for complete lines to process
            if '\n' in text:
                self._process_buffer()
            
            return len(text)
    
    def _process_buffer(self) -> None:
        """Process the buffer content for warnings and errors."""
        buffer_content = self.buffer.getvalue()
        lines = buffer_content.split('\n')
        
        # Keep last line if it's not complete (no newline at the end)
        if buffer_content and not buffer_content.endswith('\n'):
            last_line = lines[-1]
            lines = lines[:-1]
        else:
            last_line = ""
            
        # Process complete lines
        for line in lines:
            if line:  # Skip empty lines
                self._analyze_and_notify(line)
        
        # Clear buffer and keep the last incomplete line
        self.buffer = io.StringIO()
        if last_line:
            self.buffer.write(last_line)
    
    def _analyze_and_notify(self, line: str) -> None:
        """Analyze a line of text for warnings or errors and send notifications.
        
        Args:
            line: Line of text to analyze
        """
        # Skip ignored patterns
        for pattern in self.ignore_patterns:
            if pattern.search(line):
                return
        
        # Check for errors first (higher priority)
        for pattern in self.error_patterns:
            if pattern.search(line):
                self._notify(line, NotificationType.ERROR)
                # Log the error
                self.logger.error(line)
                return
        
        # Then check for warnings
        for pattern in self.warning_patterns:
            if pattern.search(line):
                self._notify(line, NotificationType.WARNING)
                # Log the warning
                self.logger.warning(line)
                return
        
        # For non-matching lines, just log as info
        self.logger.info(line)
    
    def _notify(self, message: str, notification_type: NotificationType) -> None:
        """Send notification about captured output.
        
        Args:
            message: Message content
            notification_type: Type of notification (warning or error)
        """
        # Call the provided callback if available
        if self.notification_callback:
            self.notification_callback(message, notification_type)
            
        # Also use the notification manager directly
        source = f"console_{self.stream_type}"
        
        if notification_type == NotificationType.ERROR:
            self.notification_manager.add_error(
                message=message,
                source=source
            )
        elif notification_type == NotificationType.WARNING:
            self.notification_manager.add_warning(
                message=message,
                source=source
            )
    
    def flush(self) -> None:
        """Flush the stream."""
        with self.lock:
            if self.original_stream:
                self.original_stream.flush()
            self._process_buffer()
    
    def close(self) -> None:
        """Close the stream and restore original."""
        self.stop_redirect()
        self.flush()
    
    def add_warning_pattern(self, pattern: Union[str, Pattern]) -> None:
        """Add a new pattern to detect warnings.
        
        Args:
            pattern: Regular expression pattern to match warnings
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
        self.warning_patterns.append(pattern)
    
    def add_error_pattern(self, pattern: Union[str, Pattern]) -> None:
        """Add a new pattern to detect errors.
        
        Args:
            pattern: Regular expression pattern to match errors
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
        self.error_patterns.append(pattern)
    
    def add_ignore_pattern(self, pattern: Union[str, Pattern]) -> None:
        """Add a new pattern to ignore.
        
        Args:
            pattern: Regular expression pattern to ignore
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
        self.ignore_patterns.append(pattern)


class ConsoleCaptureManager:
    """Manager class for handling console output redirection."""
    
    _instance: Optional["ConsoleCaptureManager"] = None
    
    def __new__(cls) -> "ConsoleCaptureManager":
        """Create or return the singleton instance of ConsoleCaptureManager.
        
        Returns:
            The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(ConsoleCaptureManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the console capture manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.notification_manager = NotificationManager()
        self.redirectors = {}
        self.is_capturing = False
    
    def start_capture(self) -> None:
        """Start capturing stdout and stderr."""
        if not self.is_capturing:
            # Create stdout redirector
            stdout_redirector = StreamRedirector(
                stream_type="stdout",
                notification_callback=self._on_notification
            )
            stdout_redirector.start_redirect()
            self.redirectors["stdout"] = stdout_redirector
            
            # Create stderr redirector
            stderr_redirector = StreamRedirector(
                stream_type="stderr",
                notification_callback=self._on_notification
            )
            stderr_redirector.start_redirect()
            self.redirectors["stderr"] = stderr_redirector
            
            self.is_capturing = True
    
    def stop_capture(self) -> None:
        """Stop capturing and restore original streams."""
        if self.is_capturing:
            # Stop all redirectors
            for redirector in self.redirectors.values():
                redirector.stop_redirect()
            
            self.redirectors = {}
            self.is_capturing = False
    
    def _on_notification(self, message: str, notification_type: NotificationType) -> None:
        """Handle notifications from redirectors.
        
        Args:
            message: Message text
            notification_type: Type of notification
        """
        # This method could be expanded to handle notifications differently
        # Currently, the StreamRedirector already sends notifications to the NotificationManager
        pass
    
    def add_warning_pattern(self, pattern: Union[str, Pattern]) -> None:
        """Add a warning pattern to all redirectors.
        
        Args:
            pattern: Pattern to add
        """
        for redirector in self.redirectors.values():
            redirector.add_warning_pattern(pattern)
    
    def add_error_pattern(self, pattern: Union[str, Pattern]) -> None:
        """Add an error pattern to all redirectors.
        
        Args:
            pattern: Pattern to add
        """
        for redirector in self.redirectors.values():
            redirector.add_error_pattern(pattern)
    
    def add_ignore_pattern(self, pattern: Union[str, Pattern]) -> None:
        """Add an ignore pattern to all redirectors.
        
        Args:
            pattern: Pattern to add
        """
        for redirector in self.redirectors.values():
            redirector.add_ignore_pattern(pattern)


# Create singleton instance for easy import
console_capture = ConsoleCaptureManager()