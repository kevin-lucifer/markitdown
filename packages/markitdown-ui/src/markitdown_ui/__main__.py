#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT

"""Entry point for the MarkItDown UI application."""

import sys
import argparse
import traceback
import tkinter as tk
from tkinter import messagebox

from markitdown_ui.__about__ import __version__
from markitdown_ui.app import MarkItDownUI


def main():
    """Launch the MarkItDown UI application."""
    parser = argparse.ArgumentParser(
        description="MarkItDown - A graphical interface for converting various file formats to Markdown.",
        prog="markitdown-ui",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version number and exit",
    )

    parser.add_argument(
        "filename",
        nargs="?",
        help="Optional: Path to a file to open on startup",
    )

    # Parse arguments
    args = parser.parse_args()

    try:
        # Create the root window
        root = tk.Tk()
        root.title(f"MarkItDown UI v{__version__}")
        
        # Set minimum window size
        root.minsize(800, 600)
        
        # Set icon (if available)
        try:
            # This would need an actual icon file included with the package
            # root.iconbitmap("path/to/icon.ico")
            pass
        except tk.TclError:
            pass
        
        # Create and start the application
        app = MarkItDownUI(root)
        
        # If a filename was provided, open it
        if args.filename:
            app.open_file(args.filename)
        
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        # Show error dialog for unexpected exceptions
        error_msg = f"An unexpected error occurred:\n\n{str(e)}\n\n"
        error_details = traceback.format_exc()
        
        # Try to show a GUI error if possible
        try:
            messagebox.showerror("Error", error_msg + error_details)
        except:
            # Fall back to console error if GUI fails
            print(error_msg, file=sys.stderr)
            print(error_details, file=sys.stderr)
        
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())