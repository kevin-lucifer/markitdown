#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Tests for the MarkItDown UI application."""

import os
import sys
import unittest
import tkinter as tk
from tkinter import TclError
from unittest.mock import patch, MagicMock, PropertyMock

# Import the UI components
from markitdown_ui.app import MarkItDownUI
from markitdown_ui.converter import ConverterManager, ConversionProgress
from markitdown_ui.__main__ import main


class TestMarkItDownUI(unittest.TestCase):
    """Test cases for the MarkItDown UI application."""

    def setUp(self):
        """Set up the test environment."""
        try:
            self.root = tk.Tk()
            self.ui = MarkItDownUI(self.root)
        except TclError:
            # Skip tests if no display is available (CI environment)
            self.skipTest("No display available")

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass

    def test_ui_initialization(self):
        """Test that the UI initializes correctly."""
        # Check that main components are created
        self.assertIsNotNone(self.ui.main_frame)
        self.assertIsNotNone(self.ui.file_path_var)
        self.assertIsNotNone(self.ui.preview_text)
        self.assertIsNotNone(self.ui.status_var)
        
        # Check default values
        self.assertEqual(self.ui.file_path_var.get(), "")
        self.assertEqual(self.ui.status_var.get(), "Ready")
        self.assertIsNone(self.ui.current_file)
        self.assertIsNone(self.ui.current_result)
        self.assertFalse(self.ui.is_converting)

    def test_parameter_controls(self):
        """Test parameter controls in the UI."""
        # Check that parameter variables are initialized
        self.assertIsNotNone(self.ui.extension_var)
        self.assertIsNotNone(self.ui.mimetype_var)
        self.assertIsNotNone(self.ui.charset_var)
        self.assertIsNotNone(self.ui.use_docintel_var)
        self.assertIsNotNone(self.ui.endpoint_var)
        self.assertIsNotNone(self.ui.use_plugins_var)
        self.assertIsNotNone(self.ui.keep_data_uris_var)
        
        # Check default values
        self.assertEqual(self.ui.extension_var.get(), "")
        self.assertEqual(self.ui.mimetype_var.get(), "")
        self.assertEqual(self.ui.charset_var.get(), "")
        self.assertFalse(self.ui.use_docintel_var.get())
        self.assertEqual(self.ui.endpoint_var.get(), "")
        self.assertTrue(self.ui.use_plugins_var.get())
        self.assertFalse(self.ui.keep_data_uris_var.get())
        
        # Test toggle_docintel
        self.ui.use_docintel_var.set(True)
        self.ui._toggle_docintel()
        self.assertEqual(self.ui.endpoint_entry["state"], "normal")
        
        self.ui.use_docintel_var.set(False)
        self.ui._toggle_docintel()
        self.assertEqual(self.ui.endpoint_entry["state"], "disabled")

    @patch('tkinter.filedialog.askopenfilename')
    def test_file_selection(self, mock_filedialog):
        """Test file selection functionality."""
        # Setup mock return value
        mock_path = "/path/to/test.pdf"
        mock_filedialog.return_value = mock_path
        
        # Test open file dialog
        self.ui._open_file_dialog()
        
        # Check that the dialog was called
        mock_filedialog.assert_called_once()
        
        # Check that the file path was set
        self.assertEqual(self.ui.file_path_var.get(), mock_path)
        self.assertEqual(self.ui.current_file, mock_path)
        self.assertEqual(self.ui.extension_var.get(), ".pdf")
        
        # Test direct file opening
        self.ui.file_path_var.set("")
        self.ui.current_file = None
        self.ui.extension_var.set("")
        
        self.ui.open_file(mock_path)
        self.assertEqual(self.ui.file_path_var.get(), mock_path)
        self.assertEqual(self.ui.current_file, mock_path)
        self.assertEqual(self.ui.extension_var.get(), ".pdf")

    @patch('markitdown_ui.app.MarkItDown')
    def test_convert_file(self, mock_markitdown):
        """Test file conversion process."""
        # Setup
        mock_result = MagicMock()
        mock_result.text_content = "# Converted Markdown"
        mock_converter_instance = mock_markitdown.return_value
        mock_converter_instance.convert.return_value = mock_result
        
        # Set a file path
        test_path = "/path/to/test.pdf"
        self.ui.file_path_var.set(test_path)
        self.ui.current_file = test_path
        
        # Mock thread to avoid background processing
        with patch('threading.Thread') as mock_thread:
            # Run the conversion
            self.ui._convert_file()
            
            # Check that the thread was created and started
            mock_thread.assert_called_once()
            thread_instance = mock_thread.return_value
            thread_instance.start.assert_called_once()
            
            # Check UI state
            self.assertTrue(self.ui.is_converting)
            
            # Simulate thread completion by calling the callback directly
            thread_args = mock_thread.call_args[1]['args']
            thread_kwargs = mock_thread.call_args[1]['kwargs']
            
            # Call the target function with the arguments
            self.ui._do_conversion(test_path, **thread_kwargs)
            
            # Check that the converter was called correctly
            mock_markitdown.assert_called_once_with(enable_plugins=True)
            mock_converter_instance.convert.assert_called_once()

    def test_preview_update(self):
        """Test updating the preview with conversion results."""
        # Setup a mock result
        mock_result = MagicMock()
        mock_result.text_content = "# Test Markdown\n\nThis is a test."
        self.ui.current_result = mock_result
        
        # Update the preview
        self.ui._update_preview_with_result()
        
        # Check preview content
        preview_text = self.ui.preview_text.get(1.0, tk.END).strip()
        self.assertEqual(preview_text, mock_result.text_content)
        
        # Check button states
        self.assertEqual(self.ui.copy_button["state"], "normal")
        self.assertEqual(self.ui.save_button["state"], "normal")

    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('builtins.open', create=True)
    def test_save_functionality(self, mock_open, mock_filedialog):
        """Test saving converted markdown to a file."""
        # Setup
        mock_result = MagicMock()
        mock_result.text_content = "# Test Markdown\n\nThis is a test."
        self.ui.current_result = mock_result
        
        # Mock the file dialog
        save_path = "/path/to/output.md"
        mock_filedialog.return_value = save_path
        
        # Test save functionality
        self.ui._save_file_dialog()
        
        # Verify dialog was shown
        mock_filedialog.assert_called_once()
        
        # Verify file was opened and written
        mock_open.assert_called_once_with(save_path, "w", encoding="utf-8")
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write.assert_called_once_with(mock_result.text_content)

    def test_clipboard_operations(self):
        """Test clipboard operations."""
        # Setup
        mock_result = MagicMock()
        mock_result.text_content = "# Test Markdown"
        self.ui.current_result = mock_result
        
        # Mock clipboard methods
        with patch.object(self.ui.root, 'clipboard_clear') as mock_clear, \
             patch.object(self.ui.root, 'clipboard_append') as mock_append:
            
            # Test copy to clipboard
            self.ui._copy_markdown()
            
            # Verify clipboard operations
            mock_clear.assert_called_once()
            mock_append.assert_called_once_with(mock_result.text_content)


class TestConverterManager(unittest.TestCase):
    """Test cases for the ConverterManager class."""

    def setUp(self):
        """Set up test environment."""
        self.converter_manager = ConverterManager()

    def test_progress_update(self):
        """Test progress update functionality."""
        # Create a mock callback
        mock_callback = MagicMock()
        
        # Set the callback
        self.converter_manager.set_progress_callback(mock_callback)
        
        # Update progress
        self.converter_manager._update_progress("Testing", 0.5)
        
        # Check that progress was updated
        self.assertEqual(self.converter_manager.progress.status, "Testing")
        self.assertEqual(self.converter_manager.progress.progress, 0.5)
        
        # Check that callback was called
        mock_callback.assert_called_once_with(self.converter_manager.progress)

    def test_file_validation(self):
        """Test file validation functionality."""
        # Test empty path
        is_valid, error = self.converter_manager.validate_file("")
        self.assertFalse(is_valid)
        self.assertEqual(error, "No file selected")
        
        # Test non-existent file
        is_valid, error = self.converter_manager.validate_file("/path/does/not/exist.pdf")
        self.assertFalse(is_valid)
        self.assertTrue("not found" in error)
        
        # Test directory instead of file
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=False):
            is_valid, error = self.converter_manager.validate_file("/path/is/dir")
            self.assertFalse(is_valid)
            self.assertTrue("Not a file" in error)
        
        # Test unreadable file
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('os.access', return_value=False):
            is_valid, error = self.converter_manager.validate_file("/path/to/unreadable.pdf")
            self.assertFalse(is_valid)
            self.assertTrue("not readable" in error)
        
        # Test valid file
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('os.access', return_value=True):
            is_valid, error = self.converter_manager.validate_file("/path/to/valid.pdf")
            self.assertTrue(is_valid)
            self.assertEqual(error, "")

    def test_parameter_validation(self):
        """Test parameter validation functionality."""
        # Test valid parameters
        params = {"extension": ".pdf", "enable_plugins": True}
        is_valid, error = self.converter_manager.validate_parameters(params)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        
        # Test invalid docintel endpoint
        params = {"docintel_endpoint": "invalid-url"}
        is_valid, error = self.converter_manager.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertTrue("valid URL" in error)
        
        # Test valid docintel endpoint
        params = {"docintel_endpoint": "https://example.com/endpoint"}
        is_valid, error = self.converter_manager.validate_parameters(params)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")


class TestMainModule(unittest.TestCase):
    """Test cases for the __main__ module."""

    @patch('sys.argv', ['markitdown-ui'])
    @patch('tkinter.Tk')
    @patch('markitdown_ui.app.MarkItDownUI')
    def test_main_function(self, mock_ui, mock_tk, mock_argv):
        """Test the main function."""
        # Setup mock
        mock_root = mock_tk.return_value
        
        # Run main with no args
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(filename=None, version=False)
            result = main()
        
        # Check that UI was created and mainloop was called
        mock_tk.assert_called_once()
        mock_ui.assert_called_once_with(mock_root)
        mock_root.mainloop.assert_called_once()
        
        # Check return code
        self.assertEqual(result, 0)

    @patch('sys.argv', ['markitdown-ui', 'test.pdf'])
    @patch('tkinter.Tk')
    @patch('markitdown_ui.app.MarkItDownUI')
    def test_main_with_filename(self, mock_ui, mock_tk, mock_argv):
        """Test the main function with a filename argument."""
        # Setup mock
        mock_root = mock_tk.return_value
        mock_app = mock_ui.return_value
        
        # Run main with filename
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(filename='test.pdf', version=False)
            result = main()
        
        # Check that file was opened
        mock_app.open_file.assert_called_once_with('test.pdf')
        
        # Check return code
        self.assertEqual(result, 0)

    @patch('sys.argv', ['markitdown-ui'])
    @patch('tkinter.Tk')
    @patch('tkinter.messagebox.showerror')
    def test_main_with_exception(self, mock_error, mock_tk, mock_argv):
        """Test the main function with an exception."""
        # Make Tk raise an exception
        mock_tk.side_effect = Exception("Test exception")
        
        # Run main
        result = main()
        
        # Check that error dialog was shown
        mock_error.assert_called_once()
        
        # Check return code
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()