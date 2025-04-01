#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT
#
"""Main application class for MarkItDown UI."""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, Menu, font
from typing import Optional, Dict, Any, List, Tuple

from markitdown import MarkItDown, StreamInfo, DocumentConverterResult
from markitdown.__about__ import __version__ as markitdown_version

from markitdown_ui.preferences import PreferencesManager
from markitdown_ui.theme import ThemeManager

COMMON_MIMETYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/html',
    'text/plain',
    'image/jpeg',
    'image/png',
    'audio/mpeg',
    'audio/wav',
    'application/epub+zip',
    'application/json',
]

COMMON_CHARSETS = [
    # Unicode Encodings
    'UTF-8',
    'UTF-8-SIG',
    'UTF-16',
    'UTF-16-BE',
    'UTF-16-LE',
    'UTF-32',
    'UTF-32-BE',
    'UTF-32-LE',
    
    # ISO-8859 Series (Latin)
    'ISO-8859-1',
    'ISO-8859-2',
    'ISO-8859-3',
    'ISO-8859-4',
    'ISO-8859-5',
    'ISO-8859-6',
    'ISO-8859-7',
    'ISO-8859-8',
    'ISO-8859-9',
    'ISO-8859-10',
    'ISO-8859-11',
    'ISO-8859-13',
    'ISO-8859-14',
    'ISO-8859-15',
    'ISO-8859-16',
    
    # Windows Codepages
    'Windows-1250',
    'Windows-1251',
    'Windows-1252',
    'Windows-1253',
    'Windows-1254',
    'Windows-1255',
    'Windows-1256',
    'Windows-1257',
    'Windows-1258',
    
    # Asian Encodings
    # Chinese
    'Big5',
    'GB18030',
    'GB2312',
    'GBK',
    'HZ-GB-2312',
    # Japanese
    'EUC-JP',
    'ISO-2022-JP',
    'Shift-JIS',
    # Korean
    'EUC-KR',
    'ISO-2022-KR',
    'Johab',
    
    # Legacy and Special Encodings
    'ASCII',
    'EBCDIC-CP-HE',
    'IBM437',
    'IBM850',
    'ISO-2022-CN',
    'ISO-2022-CN-EXT',
    'KOI8-R',
    'KOI8-U',
    'MacRoman',
    'TIS-620',
]

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
        self.zoom_level = 0
        
        # Configure the root window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Override default window size
        PreferencesManager.DEFAULT_PREFERENCES['window_size'] = (1024, 768)
        
        # Add these after root configuration
        self.prefs = PreferencesManager()
        self.theme = ThemeManager()
        self.theme.initialize(root)
        
        # Load saved preferences
        self._load_window_geometry()
        self.zoom_level = self.prefs.get_zoom_level()
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)  # Make the preview area expandable
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create the file selection frame
        self._create_file_selection_frame()
        
        # Create parameters frame
        self._create_parameters_frame()
        
        # Create preview frame
        self._create_preview_frame()
        
        # Initialize zoom font after preview frame exists
        self._update_zoom_font()
        
        # Create status bar
        self._create_status_bar()
        
        # Update status
        self._update_status("Ready")
        
        # Set closing handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Add search bindings
        self._setup_search_bindings()
        
        # Add these bindings
        root.bind("<Control-o>", lambda e: self._open_file_dialog())
        root.bind("<Control-s>", lambda e: self._save_file())
        root.bind("<Control-plus>", lambda e: self.zoom_in())
        root.bind("<Control-minus>", lambda e: self.zoom_out())
        root.bind("<Control-0>", lambda e: self.reset_zoom())
        root.bind("<Control-t>", lambda e: self._toggle_theme())
        
        # Add window resize binding
        root.bind("<Configure>", lambda e: self._save_window_geometry())

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self._new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self._open_file_dialog)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self._save_file)
        file_menu.add_command(label="Save As...", command=self._save_file_dialog)
        
        # Recent Files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_files_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Alt+F4", command=self._on_close)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self._copy_markdown)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self._paste_content)
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", accelerator="Ctrl+0", command=self.reset_zoom)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Theme", accelerator="Ctrl+T", command=self._toggle_theme)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_docs)

    def _create_toolbar(self) -> None:
        """Create the toolbar with common actions."""
        self.toolbar = ttk.Frame(self.main_frame, style="Toolbar.TFrame")
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Toolbar buttons
        ttk.Button(self.toolbar, text="📁 Open", style="Toolbar.TButton", 
              command=self._open_file_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="💾 Save", style="Toolbar.TButton",
              command=self._save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="🌓 Theme", style="Toolbar.TButton",
              command=self._toggle_theme).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="+ Zoom In", style="Toolbar.TButton",
              command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="- Zoom Out", style="Toolbar.TButton",
              command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="↺ Reset Zoom", style="Toolbar.TButton",
              command=self.reset_zoom).pack(side=tk.LEFT, padx=2)

    def _create_file_selection_frame(self) -> None:
        """Create the file selection frame with Browse button and file path entry."""
        file_frame = ttk.LabelFrame(self.main_frame, text="File Selection")
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
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
        params_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        params_frame.columnconfigure(1, weight=1)
        
        # Extension hint
        ttk.Label(params_frame, text="Extension:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.extension_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.extension_var).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(params_frame, text="(e.g., .pdf, .docx)").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        
        # MIME type
        ttk.Label(params_frame, text="MIME Type:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.mimetype_var = tk.StringVar()
        self.mimetype_combo = ttk.Combobox(params_frame, textvariable=self.mimetype_var, values=COMMON_MIMETYPES, state='normal')
        self.mimetype_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(params_frame, text="(e.g., application/pdf)").grid(row=1, column=2, sticky="w", padx=(0, 5), pady=2)
        
        # Charset
        ttk.Label(params_frame, text="Charset:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.charset_var = tk.StringVar()
        self.charset_combo = ttk.Combobox(params_frame, textvariable=self.charset_var, values=COMMON_CHARSETS, state='normal')
        self.charset_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
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

        self._original_mimetype_values = COMMON_MIMETYPES.copy()
        self._original_charset_values = COMMON_CHARSETS.copy()

        self.mimetype_combo.bind('<KeyRelease>', 
            lambda e: self._filter_combobox(self.mimetype_combo, e, self._original_mimetype_values))
        self.charset_combo.bind('<KeyRelease>',
            lambda e: self._filter_combobox(self.charset_combo, e, self._original_charset_values))

    def _create_preview_frame(self) -> None:
        """Create the preview frame with markdown display area and save button."""
        preview_frame = ttk.LabelFrame(self.main_frame, text="Markdown Preview")
        preview_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Scrolled text widget for markdown preview
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, wrap=tk.WORD, width=80, height=20, font=("Courier", 10)
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Search frame
        self.search_frame = ttk.Frame(preview_frame)
        self.search_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        # Search entry
        self.search_text_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_text_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Case sensitivity toggle
        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.search_frame, text="Aa", variable=self.case_sensitive_var,
                        command=self._find_text).pack(side=tk.LEFT, padx=2)
        
        # Navigation buttons
        ttk.Button(self.search_frame, text="▲", width=3, command=self._find_previous).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.search_frame, text="▼", width=3, command=self._find_next).pack(side=tk.LEFT, padx=2)
        
        # Close button
        ttk.Button(self.search_frame, text="✕", width=3, command=self._hide_search_frame).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.search_status_var = tk.StringVar()
        ttk.Label(self.search_frame, textvariable=self.search_status_var).pack(side=tk.RIGHT, padx=5)
        
        # Bottom button frame
        button_frame = ttk.Frame(preview_frame)
        button_frame.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        
        self.copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=self._copy_markdown)
        self.copy_button.pack(side=tk.RIGHT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save As...", command=self._save_file_dialog)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        # Initially disable buttons and hide search
        self.copy_button["state"] = "disabled"
        self.save_button["state"] = "disabled"
        self.search_frame.grid_remove()
        
        self.preview_text.bind("<<Modified>>", self._update_document_stats)
        self._configure_search_tags()

    def _create_status_bar(self) -> None:
        """Create the status bar with document statistics."""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=4, column=0, sticky="ew")
        
        # Document statistics
        self.stats_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.stats_var, style="StatusBar.TLabel",
             anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Conversion status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var, style="StatusBar.TLabel",
             anchor=tk.E).pack(side=tk.RIGHT)
        
        # Progress bar for conversions
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            self.main_frame, orient=tk.HORIZONTAL, length=100, mode="indeterminate", variable=self.progress_var
        )
        self.progress_bar.grid(row=5, column=0, sticky="ew", pady=(5, 0))
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
        
        # Add to recent files
        self.prefs.add_recent_file(file_path)
        self._update_recent_files_menu()

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
            
            # Update document statistics
            self._update_document_stats()
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
        self._update_document_stats()

    def _show_about(self) -> None:
        """Show the custom themed about dialog."""
        about_win = tk.Toplevel(self.root)
        about_win.title("About MarkItDown UI")
        about_win.geometry("400x300")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        # Center window relative to main application
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        about_win.geometry(f"+{main_x + (main_width - 400)//2}+{main_y + 50}")

        # Get theme colors
        colors = self.theme.get_theme_colors()
        text_color = colors["text_foreground"]
        bg_color = colors["background"]
        accent_color = colors["accent"]

        # Create canvas with mountain background
        canvas = tk.Canvas(about_win, bg=bg_color, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Draw simple mountain shapes
        canvas.create_rectangle(0, 0, 400, 300, fill=bg_color, outline="")
        canvas.create_polygon(0, 200, 100, 100, 200, 200, fill="#2a4a7a", outline="")
        canvas.create_polygon(150, 220, 250, 120, 350, 220, fill="#1a3a6a", outline="")
        canvas.create_polygon(-50, 250, 150, 150, 350, 250, fill="#3a5a8a", outline="")

        # Add text elements
        title_font = font.Font(family="Helvetica", size=14, weight="bold")
        canvas.create_text(200, 80, text="Wanna be Friends?", 
                        font=title_font, fill=text_color)
        
        version_text = f"MarkItDown UI v{markitdown_version}"
        canvas.create_text(200, 120, text=version_text, 
                        fill=text_color, font=("Helvetica", 10))

        # Signature
        sig_font = font.Font(family="Helvetica", size=10, slant="italic")
        canvas.create_text(380, 280, text="by Kevin", anchor=tk.SE,
                        font=sig_font, fill=accent_color)

        # Close button
        btn_frame = ttk.Frame(about_win)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Close", command=about_win.destroy).pack()

        # Apply theme to widgets
        self.theme.apply_menu_theme(about_win.nametowidget(btn_frame.winfo_children()[0].winfo_parent()))
    
    def _new_file(self) -> None:
        """Create a new file (clear the preview)."""
        self.open_file("")
        self._clear_preview()
        self._update_status("New file created")
    
    def _save_file(self) -> None:
        """Save the current markdown content."""
        if not self.current_result:
            messagebox.showinfo("Info", "No conversion result to save.")
            return
        
        if not self.current_file:
            self._save_file_dialog()
            return
        
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.current_result.text_content)
            self._update_status(f"File saved: {os.path.basename(self.current_file)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def _paste_content(self) -> None:
        """Paste content from clipboard to preview."""
        try:
            text = self.root.clipboard_get()
            self.preview_text.insert(tk.INSERT, text)
            self._update_document_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste: {str(e)}")
    
    def _show_docs(self) -> None:
        """Show the documentation."""
        messagebox.showinfo("Documentation", "No documentation available yet.")
    
    def zoom_in(self) -> None:
        """Increase the preview text zoom level."""
        self.zoom_level = min(5, self.zoom_level + 1)
        self._update_zoom_font()
        self.prefs.set_zoom_level(self.zoom_level)

    def zoom_out(self) -> None:
        """Decrease the preview text zoom level."""
        self.zoom_level = max(-5, self.zoom_level - 1)
        self._update_zoom_font()
        self.prefs.set_zoom_level(self.zoom_level)

    def reset_zoom(self) -> None:
        """Reset the zoom level to default."""
        self.zoom_level = 0
        self._update_zoom_font()
        self.prefs.set_zoom_level(self.zoom_level)

    def _update_zoom_font(self) -> None:
        """Update the preview text font size based on zoom level."""
        base_size = 10
        new_size = base_size + self.zoom_level
        self.preview_text.configure(font=("Courier", new_size))
    
    def _update_document_stats(self, event=None) -> None:
        """Update the document statistics in the status bar."""
        content = self.preview_text.get("1.0", "end-1c")
        words = len(content.split())
        chars = len(content)
        self.stats_var.set(f"Words: {words}  Characters: {chars}")
    
    def _update_recent_files_menu(self) -> None:
        """Update the Recent Files submenu with current list."""
        self.recent_menu.delete(0, tk.END)
        recent_files = self.prefs.get_recent_files()
        
        for path, _ in recent_files:
            self.recent_menu.add_command(
                label=os.path.basename(path),
                command=lambda p=path: self.open_file(p)
            )
        
        self.recent_menu.add_separator()
        self.recent_menu.add_command(label="Clear Recent", command=self._clear_recent_files)

    def _clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.prefs.clear_recent_files()
        self._update_recent_files_menu()
    
    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        new_theme = self.theme.toggle_theme()
        self.theme.apply_theme(new_theme)
        self.theme.apply_text_widget_theme(self.preview_text)
        self.theme.apply_menu_theme(self.root.nametowidget(self.root["menu"]))
        self._configure_search_tags()
    
    def _load_window_geometry(self) -> None:
        """Load and apply saved window geometry."""
        size = self.prefs.get_window_size()
        position = self.prefs.get_window_position()
        
        if not position:
            position = self._get_center_position(size)
                
        self.root.geometry(f"{size[0]}x{size[1]}+{position[0]}+{position[1]}")
    
    def _save_window_geometry(self) -> None:
        """Save current window size and position."""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.prefs.set_window_size(width, height)
        self.prefs.set_window_position(x, y)

    def _get_center_position(self, size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate center position based on screen size."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        return (
            (screen_width - size[0]) // 2,
            (screen_height - size[1]) // 2
        )

    def _on_close(self) -> None:
        """Handle window closing event."""
        self._save_window_geometry()
        self.root.quit()

    def _filter_combobox(self, combo: ttk.Combobox, event: tk.Event, original_values: list) -> None:
        """Filter combobox values based on user input."""
        current_text = combo.get()
        cursor_pos = combo.index(tk.INSERT)  # Save current cursor position
        
        filtered = [
            value for value in original_values 
            if current_text.lower() in value.lower()
        ] if current_text else original_values
        
        combo['values'] = filtered
        
        if current_text:
            # Maintain dropdown visibility without auto-selecting items
            if filtered and not combo.focus_get() == combo:  # Only open if not already focused
                combo.event_generate('<Button-1>')  # Show dropdown without selection
            # Restore original cursor position after filtering
            combo.icursor(cursor_pos)
            combo.selection_clear()
        else:
            combo.set('')

    def _setup_search_bindings(self) -> None:
        """Configure search-related key bindings."""
        self.root.bind("<Control-f>", lambda e: self._toggle_search_visibility())
        self.search_entry.bind("<Return>", lambda e: self._find_next())
        self.search_entry.bind("<Shift-Return>", lambda e: self._find_previous())
        self.search_entry.bind("<Escape>", lambda e: self._hide_search_frame())
        self.search_entry.bind("<KeyRelease>", lambda e: self._find_text())
        
        # Prevent focus stealing from search entry
        self.search_entry.bind("<Up>", lambda e: "break")
        self.search_entry.bind("<Down>", lambda e: "break")

    def _toggle_search_visibility(self) -> None:
        """Toggle search frame visibility."""
        if self.search_frame.winfo_ismapped():
            self._hide_search_frame()
        else:
            self._show_search_frame()

    def _show_search_frame(self) -> None:
        """Show the search frame and focus the entry."""
        self.search_frame.grid()
        self.search_entry.focus_set()
        self._find_text()

    def _hide_search_frame(self) -> None:
        """Hide the search frame and clear highlights."""
        self.search_frame.grid_remove()
        self._clear_search_highlighting()
        self.search_status_var.set("")
        self.preview_text.focus_set()

    def _find_text(self, event=None) -> None:
        """Search for text in the preview content."""
        self._clear_search_highlighting()
        search_term = self.search_text_var.get()
        if not search_term:
            return

        self.preview_text.tag_remove("search_highlight", "1.0", tk.END)
        self.preview_text.tag_remove("current_match", "1.0", tk.END)
        
        count = 0
        start_pos = "1.0"
        while True:
            pos = self.preview_text.search(
                search_term, 
                start_pos, 
                stopindex=tk.END,
                nocase=not self.case_sensitive_var.get(),
                regexp=False
            )
            if not pos:
                break
            end_pos = f"{pos}+{len(search_term)}c"
            self.preview_text.tag_add("search_highlight", pos, end_pos)
            start_pos = end_pos
            count += 1
        
        if count > 0:
            self.search_status_var.set(f"{count} matches")
            self._find_next()
        else:
            self.search_status_var.set("No matches found")

    def _find_next(self) -> None:
        """Navigate to next search match."""
        search_term = self.search_text_var.get()
        if not search_term:
            return

        start_pos = self.preview_text.index(tk.INSERT + "+1c")
        pos = self.preview_text.search(
            search_term, 
            start_pos, 
            stopindex=tk.END,
            nocase=not self.case_sensitive_var.get()
        )
        
        if not pos:
            pos = self.preview_text.search(
                search_term, 
                "1.0", 
                stopindex=tk.END,
                nocase=not self.case_sensitive_var.get()
            )
            if not pos:
                return

        self._highlight_current_match(pos, f"{pos}+{len(search_term)}c")

    def _find_previous(self) -> None:
        """Navigate to previous search match."""
        search_term = self.search_text_var.get()
        if not search_term:
            return

        start_pos = self.preview_text.index(tk.INSERT + "-1c")
        pos = self.preview_text.search(
            search_term, 
            start_pos, 
            stopindex="1.0",
            backwards=True,
            nocase=not self.case_sensitive_var.get()
        )
        
        if not pos:
            pos = self.preview_text.search(
                search_term, 
                tk.END, 
                stopindex="1.0",
                backwards=True,
                nocase=not self.case_sensitive_var.get()
            )
            if not pos:
                return

        self._highlight_current_match(pos, f"{pos}+{len(search_term)}c")

    def _highlight_current_match(self, start: str, end: str) -> None:
        """Highlight the current active match."""
        self.preview_text.tag_remove("current_match", "1.0", tk.END)
        self.preview_text.tag_add("current_match", start, end)
        self.preview_text.see(start)
        self.preview_text.mark_set(tk.INSERT, start)

    def _clear_search_highlighting(self) -> None:
        """Remove all search highlighting."""
        self.preview_text.tag_remove("search_highlight", "1.0", tk.END)
        self.preview_text.tag_remove("current_match", "1.0", tk.END)

    def _configure_search_tags(self) -> None:
        """Configure text tags for search highlighting."""
        colors = self.theme.get_theme_colors()
        self.preview_text.tag_configure(
            "search_highlight", 
            background=colors["highlight"],
            foreground=colors["highlight_text"]
        )
        self.preview_text.tag_configure(
            "current_match", 
            background=colors["accent"],
            foreground=colors["highlight_text"]
        )