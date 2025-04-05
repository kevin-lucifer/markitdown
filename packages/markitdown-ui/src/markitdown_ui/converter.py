#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Converter module for handling file conversions in the MarkItDown UI."""

import os
import threading
import time
from typing import Any, Dict, Optional, Callable, Tuple, List

from markitdown import MarkItDown, StreamInfo, DocumentConverterResult
from markitdown._exceptions import FileConversionException, MarkItDownException
from markitdown_ui.notifications import NotificationManager


class ConversionError(Exception):
    """Exception raised for conversion errors."""
    
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        """Initialize a conversion error.
        
        Args:
            message: Error message
            original_exception: Original exception that caused this error, if any
        """
        self.message = message
        self.original_exception = original_exception
        super().__init__(message)


class ConversionProgress:
    """Class for tracking conversion progress."""
    
    def __init__(self):
        """Initialize a new progress tracker."""
        self.status: str = "Initializing..."
        self.progress: float = 0.0
        self.is_complete: bool = False
        self.is_error: bool = False
        self.error_message: Optional[str] = None
        self.warning_count: int = 0
        self.error_count: int = 0
        self.warnings: List[str] = []
        
    def update(self, status: str, progress: float = None) -> None:
        """Update the conversion progress.
        
        Args:
            status: Status message to display
            progress: Progress value between 0.0 and 1.0, or None for indeterminate
        """
        self.status = status
        if progress is not None:
            self.progress = max(0.0, min(1.0, progress))
    
    def add_warning(self, message: str) -> None:
        """Add a warning to the conversion progress.
        
        Args:
            message: Warning message
        """
        self.warning_count += 1
        self.warnings.append(message)
    
    def complete(self, status: str = "Conversion complete") -> None:
        """Mark the conversion as complete.
        
        Args:
            status: Final status message
        """
        self.status = status
        self.progress = 1.0
        self.is_complete = True
    
    def error(self, message: str) -> None:
        """Mark the conversion as failed.
        
        Args:
            message: Error message to display
        """
        self.status = f"Error: {message}"
        self.is_complete = True
        self.is_error = True
        self.error_message = message
        self.error_count += 1


class ConverterManager:
    """Class to manage the conversion process from the UI."""
    
    def __init__(self):
        """Initialize a new converter manager."""
        self.converter: Optional[MarkItDown] = None
        self.conversion_thread: Optional[threading.Thread] = None
        self.progress = ConversionProgress()
        self.current_result: Optional[DocumentConverterResult] = None
        self.callback: Optional[Callable[[ConversionProgress], None]] = None
    
    def set_progress_callback(self, callback: Callable[[ConversionProgress], None]) -> None:
        """Set a callback function to be called when progress updates.
        
        Args:
            callback: Function to call with progress updates
        """
        self.callback = callback
        
    def _update_progress(self, status: str, progress: float = None) -> None:
        """Update the progress and invoke the callback.
        
        Args:
            status: Status message
            progress: Progress value or None
        """
        status_with_counts = f"{status} | Warnings: {self.progress.warning_count}, Errors: {self.progress.error_count}"
        self.progress.update(status_with_counts, progress)
        if self.callback:
            self.callback(self.progress)
    
    def convert(self, 
                file_path: str, 
                parameters: Dict[str, Any],
                progress_callback: Optional[Callable[[ConversionProgress], None]] = None) -> None:
        """Start conversion process in a separate thread.
        
        Args:
            file_path: Path to the file to convert
            parameters: Dictionary of conversion parameters
            progress_callback: Optional callback function for progress updates
        
        Raises:
            ValueError: If file_path is empty or conversion is already in progress
        """
        if not file_path:
            raise ValueError("File path must be provided")
        
        if self.conversion_thread and self.conversion_thread.is_alive():
            raise ValueError("Conversion already in progress")
        
        # Reset progress tracking
        self.progress = ConversionProgress()
        self.current_result = None
        
        # Set callback if provided
        if progress_callback:
            self.set_progress_callback(progress_callback)
        
        # Extract parameters
        enable_plugins = parameters.get("enable_plugins", True)
        extension = parameters.get("extension")
        mimetype = parameters.get("mimetype")
        charset = parameters.get("charset")
        keep_data_uris = parameters.get("keep_data_uris", False)
        docintel_endpoint = parameters.get("docintel_endpoint")
        
        # Start conversion in a separate thread
        self.conversion_thread = threading.Thread(
            target=self._convert_thread,
            args=(file_path, enable_plugins, extension, mimetype, charset, keep_data_uris, docintel_endpoint)
        )
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
    
    def _convert_thread(self, 
                        file_path: str, 
                        enable_plugins: bool, 
                        extension: Optional[str],
                        mimetype: Optional[str],
                        charset: Optional[str],
                        keep_data_uris: bool,
                        docintel_endpoint: Optional[str]) -> None:
        """Run the conversion process in a separate thread.
        
        Args:
            file_path: Path to the file to convert
            enable_plugins: Whether to enable plugins
            extension: File extension hint
            mimetype: MIME type hint
            charset: Character set hint
            keep_data_uris: Whether to keep data URIs
            docintel_endpoint: Azure Document Intelligence endpoint, if any
        """
        try:
            # Initialize progress
            self._update_progress("Initializing conversion...", 0.1)
            
            # Create converter with appropriate settings
            kwargs = {}
            if docintel_endpoint:
                kwargs["docintel_endpoint"] = docintel_endpoint
                
            self.converter = MarkItDown(enable_plugins=enable_plugins, **kwargs)
            self._update_progress("Analyzing file...", 0.2)
            
            # Create stream info if any hints were provided
            stream_info = None
            if any(x is not None for x in [extension, mimetype, charset]):
                stream_info = StreamInfo(
                    extension=extension,
                    mimetype=mimetype,
                    charset=charset
                )
            
            # File size check for progress estimation
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10 MB
                self._update_progress(f"Processing large file ({file_size / 1024 / 1024:.1f} MB)...", 0.3)
            
            # Start conversion
            self._update_progress("Converting...", 0.4)
            self.current_result = self.converter.convert(
                file_path,
                stream_info=stream_info,
                keep_data_uris=keep_data_uris
            )
            
            # Mark conversion complete
            if self.current_result:
                content_length = len(self.current_result.markdown)
                self._update_progress(f"Conversion complete: {content_length} characters", 1.0)
                self.progress.complete()
            else:
                raise ConversionError("Conversion produced no result")
                
        except FileConversionException as e:
            # Format a more user-friendly error message from the exception
            error_msg = "Unable to convert file format. "
            if e.attempts:
                converters_tried = len(e.attempts)
                error_msg += f"Tried {converters_tried} converters, but none succeeded."
            else:
                error_msg += "No suitable converter found for this file."
                
            self.progress.error(error_msg)
            NotificationManager().add_error(error_msg, source="conversion")
            if self.callback:
                self.callback(self.progress)
                
        except MarkItDownException as e:
            # Handle other MarkItDown exceptions
            self.progress.error(str(e))
            NotificationManager().add_error(str(e), source="conversion")
            if self.callback:
                self.callback(self.progress)
                
        except Exception as e:
            # Handle unexpected exceptions
            error_msg = f"Unexpected error: {str(e)}"
            self.progress.error(error_msg)
            NotificationManager().add_error(error_msg, source="conversion")
            if self.callback:
                self.callback(self.progress)
    
    def get_result(self) -> Optional[DocumentConverterResult]:
        """Get the conversion result.
        
        Returns:
            The conversion result, or None if no conversion has completed
        """
        return self.current_result
    
    def is_converting(self) -> bool:
        """Check if a conversion is currently in progress.
        
        Returns:
            True if a conversion is in progress, False otherwise
        """
        return self.conversion_thread is not None and self.conversion_thread.is_alive()
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate that a file exists and is readable.
        
        Args:
            file_path: Path to the file to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "No file selected"
            
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
            
        if not os.path.isfile(file_path):
            return False, f"Not a file: {file_path}"
            
        if not os.access(file_path, os.R_OK):
            return False, f"File not readable: {file_path}"
            
        return True, ""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate conversion parameters.
        
        Args:
            parameters: Dictionary of parameters to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check docintel_endpoint format if provided
        docintel_endpoint = parameters.get("docintel_endpoint")
        if docintel_endpoint:
            if not docintel_endpoint.startswith(("http://", "https://")):
                return False, "Document Intelligence endpoint must be a valid URL"
        
        # All parameters valid
        return True, ""