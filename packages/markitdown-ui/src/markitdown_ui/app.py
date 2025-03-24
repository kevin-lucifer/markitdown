#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Main application class for MarkItDown UI."""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, Menu
from typing import Optional, Dict, Any, List, Tuple

from markitdown import MarkItDown, StreamInfo, DocumentConverterResult
from markitdown.__about__ import __version__ as markitdown_version


class MarkItDownUI:
    """Main application class for the MarkItDown UI."""

    def __init__(self, root: tk.Tk):
        """Initialize the MarkItDown UI application.
        
        Args:
            root: The root window for the application
        """
        self.root = root
        self.converter = MarkItDown(enable_plugins=True)
        self.current_file: Optional[str] = None
        self.current_result: Optional[DocumentConverterResult] = None
        self.conversion_thread: Optional[threading.Thread] = None
        self.is_converting = False
        
        # Configure the root window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)  # Make the preview area expandable
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create the file selection frame
        self._create_file_selection_frame()
        
        # Create parameters frame
        self._create_parameters_frame()
        
        # Create preview frame
        self._create_preview_frame()
        
        # Create status bar
        self._create_status_bar()
        
        # Update status
        self._update_status("Ready")

    def _create_menu_bar(self) -> None:
        """Create the menu bar with File, Edit, and Help menus."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self._open_file_dialog)
        file_menu.add_command(label="Save As...", command=self._save_file_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy Markdown", command=self._copy_markdown)
        edit_menu.add_command(label="Select All", command=self._select_all)
        edit_menu.add_command(label="Clear", command=self._clear_preview)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_file_selection_frame(self) -> None:
        """Create the file selection frame with Browse button and file path entry."""
        file_frame = ttk.LabelFrame(self.main_frame, text="File Selection")
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        # File path entry and browse button
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var)
        file_entry.grid(row=0, column=0, sticky="ew", padx=(5, 5), pady=5)
        
        browse_button = ttk.Button(file_frame, text="Browse", command=self._open_file_dialog)
        browse_button.grid(row=0, column=1, padx=(0, 5), pady=5)
        
        convert_button = ttk.Button(file_frame, text="Convert", command=self._convert_file)
        convert_button.grid(row=0, column=2, padx=(0, 5), pady=5)

    def _create_parameters_frame(self) -> None:
        """Create the parameters frame with all conversion options."""
        params_frame = ttk.LabelFrame(self.main_frame, text="Parameters")
        params_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        params_frame.columnconfigure(1, weight=1)
        
        # Extension hint
        ttk.Label(params_frame, text="Extension:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.extension_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.extension_var).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(params_frame, text="(e.g., .pdf, .docx)").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        
        # MIME type
        ttk.Label(params_frame, text="MIME Type:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.mimetype_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.mimetype_var).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(params_frame, text="(e.g., application/pdf)").grid(row=1, column=2, sticky="w", padx=(0, 5), pady=2)
        
        # Charset
        ttk.Label(params_frame, text="Charset:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.charset_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.charset_var).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(params_frame, text="(e.g., UTF-8)").grid(row=2, column=2, sticky="w", padx=(0, 5), pady=2)
        
        # Document Intelligence
        self.use_docintel_var = tk.BooleanVar(value=False)
        docintel_check = ttk.Checkbutton(params_frame, text="Use Document Intelligence", variable=self.use_docintel_var,
                                         command=self._toggle_docintel)
        docintel_check.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        
        # Document Intelligence Endpoint
        ttk.Label(params_frame, text="Endpoint:").grid(row=3, column=1, sticky="w", padx=5, pady=2)
        self.endpoint_var = tk.StringVar()
        self.endpoint_entry = ttk.Entry(params_frame, textvariable=self.endpoint_var, state="disabled")
        self.endpoint_entry.grid(row=3, column=2, sticky="ew", padx=(0, 5), pady=2)
        
        # Use plugins
        self.use_plugins_var = tk.BooleanVar(value=True)
        plugins_check = ttk.Checkbutton(params_frame, text="Use Plugins", variable=self.use_plugins_var)
        plugins_check.grid(row=4, column=0, sticky="w", padx=5, pady=2)
        
        # Keep data URIs
        self.keep_data_uris_var = tk.BooleanVar(value=False)
        data_uris_check = ttk.Checkbutton(params_frame, text="Keep Data URIs", variable=self.keep_data_uris_var)
        data_uris_check.grid(row=4, column=1, sticky="w", padx=5, pady=2)

    def _create_preview_frame(self) -> None:
        """Create the preview frame with markdown display area and save button."""
        preview_frame = ttk.LabelFrame(self.main_frame, text="Markdown Preview")
        preview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Scrolled text widget for markdown preview
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, wrap=tk.WORD, width=80, height=20, font=("Courier", 10)
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Bottom button frame
        button_frame = ttk.Frame(preview_frame)
        button_frame.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        
        self.copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=self._copy_markdown)
        self.copy_button.pack(side=tk.RIGHT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save As...", command=self._save_file_dialog)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        # Initially disable buttons
        self.copy_button["state"] = "disabled"
        self.save_button["state"] = "disabled"

    def _create_status_bar(self) -> None:
        """Create a status bar at the bottom of the application."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(row=3, column=0, sticky="ew")
        
        # Progress bar for conversions
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            self.main_frame, orient=tk.HORIZONTAL, length=100, mode="indeterminate", variable=self.progress_var
        )
        self.progress_bar.grid(row=4, column=0, sticky="ew", pady=(5, 0))
        self.progress_bar.grid_remove()  # Hide initially

    def _toggle_docintel(self) -> None:
        """Enable or disable the Document Intelligence endpoint field."""
        if self.use_docintel_var.get():
            self.endpoint_entry["state"] = "normal"
        else:
            self.endpoint_entry["state"] = "disabled"

    def _open_file_dialog(self) -> None:
        """Open a file dialog to select a file for conversion."""
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[
                ("All Files", "*.*"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("PowerPoint Presentations", "*.pptx"),
                ("Excel Workbooks", "*.xlsx"),
                ("HTML Files", "*.html"),
                ("Images", "*.jpg *.jpeg *.png"),
                ("Audio Files", "*.mp3 *.wav *.m4a"),
            ],
        )
        
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path: str) -> None:
        """Open a file and update the UI.
        
        Args:
            file_path: Path to the file to open
        """
        self.file_path_var.set(file_path)
        self.current_file = file_path
        
        # Auto-detect extension and set the extension field
        _, ext = os.path.splitext(file_path)
        if ext:
            self.extension_var.set(ext)
        
        # Clear the preview
        self._clear_preview()
        
        # Update status
        self._update_status(f"File selected: {os.path.basename(file_path)}")

    def _convert_file(self) -> None:
        """Convert the selected file to Markdown."""
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select a file first.")
            return
        
        if self.is_converting:
            messagebox.showinfo("Info", "Conversion already in progress.")
            return
        
        # Get file path
        file_path = self.file_path_var.get()
        
        # Prepare stream info
        stream_info = StreamInfo(
            extension=self.extension_var.get() if self.extension_var.get() else None,
            mimetype=self.mimetype_var.get() if self.mimetype_var.get() else None,
            charset=self.charset_var.get() if self.charset_var.get() else None,
        )
        
        # Prepare kwargs
        kwargs = {
            "stream_info": stream_info,
            "keep_data_uris": self.keep_data_uris_var.get(),
        }
        
        # Handle Document Intelligence options
        if self.use_docintel_var.get() and self.endpoint_var.get():
            kwargs["docintel_endpoint"] = self.endpoint_var.get()
        
        # Show progress
        self.is_converting = True
        self.progress_bar.grid()
        self.progress_bar.start()
        self._update_status("Converting file...")
        
        # Disable UI elements during conversion
        self._set_ui_state(False)
        
        # Start conversion in a background thread
        self.conversion_thread = threading.Thread(
            target=self._do_conversion,
            args=(file_path,),
            kwargs=kwargs
        )
        self.conversion_thread.daemon = True
        self.conversion_thread.start()

    def _do_conversion(self, file_path: str, **kwargs) -> None:
        """Perform the conversion in a background thread.
        
        Args:
            file_path: Path to the file to convert
            **kwargs: Additional arguments for the conversion
        """
        try:
            # Reinitialize converter with plugin setting
            self.converter = MarkItDown(enable_plugins=self.use_plugins_var.get())
            
            # Convert the file
            self.current_result = self.converter.convert(file_path, **kwargs)
            
            # Update the UI on the main thread
            self.root.after(0, self._update_preview_with_result)
            
        except Exception as e:
            # Show error on the main thread
            self.root.after(0, lambda: self._show_error(str(e)))
        finally:
            # Reset conversion state on the main thread
            self.root.after(0, self._reset_conversion_state)

    def _update_preview_with_result(self) -> None:
        """Update the preview with the conversion result."""
        if self.current_result:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, self.current_result.text_content)
            self._update_status(f"Conversion complete: {len(self.current_result.text_content)} characters")
            
            # Enable save and copy buttons
            self.copy_button["state"] = "normal"
            self.save_button["state"] = "normal"
        else:
            self._update_status("Conversion produced no result.")

    def _reset_conversion_state(self) -> None:
        """Reset the conversion state after completion."""
        self.is_converting = False
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self._set_ui_state(True)

    def _set_ui_state(self, enabled: bool) -> None:
        """Enable or disable UI elements during conversion.
        
        Args:
            enabled: Whether to enable or disable the UI elements
        """
        state = "normal" if enabled else "disabled"
        for widget in [
            self.main_frame.nametowidget(w)
            for w in self.main_frame.winfo_children()
            if w != str(self.status_var) and w != str(self.progress_bar)
        ]:
            try:
                widget["state"] = state
            except:
                # Not all widgets have a state attribute
                pass

    def _show_error(self, message: str) -> None:
        """Show an error message.
        
        Args:
            message: Error message to display
        """
        messagebox.showerror("Conversion Error", message)
        self._update_status(f"Error: {message[:50]}...")

    def _update_status(self, status: str) -> None:
        """Update the status bar.
        
        Args:
            status: Status message to display
        """
        self.status_var.set(status)

    def _save_file_dialog(self) -> None:
        """Open a save file dialog to save the converted markdown."""
        if not self.current_result:
            messagebox.showinfo("Info", "No conversion result to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Markdown File",
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.current_result.text_content)
                self._update_status(f"File saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def _copy_markdown(self) -> None:
        """Copy the markdown content to clipboard."""
        if not self.current_result:
            messagebox.showinfo("Info", "No conversion result to copy.")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_result.text_content)
        self._update_status("Copied to clipboard")

    def _select_all(self) -> None:
        """Select all text in the preview."""
        self.preview_text.tag_add(tk.SEL, "1.0", tk.END)
        self.preview_text.mark_set(tk.INSERT, "1.0")
        self.preview_text.see(tk.INSERT)
        return "break"

    def _clear_preview(self) -> None:
        """Clear the preview area."""
        self.preview_text.delete(1.0, tk.END)
        self.current_result = None
        self.copy_button["state"] = "disabled"
        self.save_button["state"] = "disabled"

    def _show_about(self) -> None:
        """Show the about dialog."""
        about_text = (
            f"MarkItDown UI v{markitdown_version}\n\n"
            "A graphical interface for MarkItDown, a tool for converting\n"
            "various file formats to Markdown.\n\n"
            "© 2024 Microsoft Corporation\n"
            "Licensed under the MIT License"
        )
        messagebox.showinfo("About MarkItDown UI", about_text)