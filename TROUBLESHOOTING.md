# MarkItDown - Troubleshooting Guide

This document provides solutions for common issues you might encounter when using MarkItDown, particularly with the UI application.

## Tkinter Installation Issues

Tkinter is the standard Python GUI toolkit and is required for the MarkItDown UI application. Here's how to resolve common Tkinter-related issues on different platforms.

### Verifying Tkinter Installation

Before troubleshooting, check if Tkinter is properly installed:

```
python -c "import tkinter; print('Tkinter Version:', tkinter.TkVersion); print('Tkinter Successfully Installed!')"
```

If you see an error like `ModuleNotFoundError: No module named '_tkinter'`, Tkinter is not properly installed on your system.

### Installing Tkinter on Different Platforms

#### Windows

Tkinter is typically included with the standard Python installation on Windows. If it's missing:

1. Reinstall Python and ensure you check "tcl/tk and IDLE" during installation.
2. Alternatively, use the Microsoft Store version of Python which includes Tkinter.

#### macOS

On macOS, you can install Tkinter using:

1. **Homebrew**:
   ```
   brew install python-tk@3.10  # Replace 3.10 with your Python version
   ```

2. **Official Python installer**:
   - Download the official Python installer from python.org
   - The installer includes Tkinter by default

If you're using Homebrew Python and encounter Tkinter issues, ensure Tcl/Tk is installed:
```
brew install tcl-tk
```

#### Linux

On Debian/Ubuntu-based systems:
```
sudo apt-get update
sudo apt-get install python3-tk
```

On Fedora:
```
sudo dnf install python3-tkinter
```

On CentOS/RHEL:
```
sudo yum install python3-tkinter
```

On Arch Linux:
```
sudo pacman -S tk
```

### Common Tkinter Errors and Solutions

#### "_tkinter module not found" Error

**Problem**: `ModuleNotFoundError: No module named '_tkinter'`

**Solutions**:
1. Install Tkinter using the platform-specific instructions above
2. Ensure you're using the same Python environment where Tkinter is installed
3. For virtual environments, you may need to install Tkinter in the base system first

#### "No display name and no $DISPLAY environment variable" Error

**Problem**: `_tkinter.TclError: no display name and no $DISPLAY environment variable`

**Solutions**:
1. This occurs when running in a headless environment (like SSH without X forwarding)
2. Enable X forwarding when connecting via SSH: `ssh -X user@host`
3. Set the DISPLAY environment variable: `export DISPLAY=:0`
4. For WSL users, install an X server like VcXsrv or Xming on Windows

#### Tcl/Tk Version Mismatch

**Problem**: `_tkinter.TclError: Can't find a usable tk.tcl`

**Solutions**:
1. Reinstall Python with matching Tcl/Tk versions
2. On macOS with Homebrew: `brew install tcl-tk` and then reinstall Python
3. Check if multiple Tcl/Tk installations exist on your system

## Environment Setup Issues

### Virtual Environment Setup

For best results, we recommend using a virtual environment. Here's how to set one up:

**Windows**:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Common Issues**:
1. **Activation Fails on Windows**:
   - Error: "Running scripts is disabled on this system"
   - Solution: Run PowerShell as Admin and execute:
     ```powershell
     Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```
2. **Wrong Python Version**:
   - Ensure you're using Python 3.10+ in the virtual environment
   - Verify with: `python --version`

### Package Installation Issues

When installing with `-e` (editable mode):

**Basic Installation**:
```bash
pip install -e packages/markitdown[all]
pip install -e packages/markitdown-ui
```

**Common Problems**:
1. **Missing Dependencies**:
   - Ensure you ran both installation commands above
   - Update pip first: `python -m pip install --upgrade pip`

2. **Editable Mode Conflicts**:
   - If files appear missing, reinstall with:
     ```bash
     pip install --force-reinstall -e packages/markitdown[all]
     ```

3. **Permission Errors**:
   - On Linux/macOS, try: `pip install --user ...`
   - Or use sudo (not recommended): `sudo pip install ...`

## Other Common Issues with markitdown-ui

### Application Crashes on Startup

**Problem**: The application crashes immediately when trying to launch

**Solutions**:
1. Check Python version compatibility (requires Python 3.10+)
2. Run from terminal to see error messages: `python -m markitdown_ui`
3. Check if all dependencies are installed: `pip install -e packages/markitdown[all]`
4. Try reinstalling: `pip install -e packages/markitdown-ui`

### File Conversion Fails

**Problem**: Files cannot be converted or produce unexpected results

**Solutions**:
1. Verify the file is not corrupted or password-protected
2. Check if the file format is supported by MarkItDown
3. Try specifying the file extension or MIME type manually
4. For PDF files, try enabling Document Intelligence if available
5. Check console output for specific error messages

### Performance Issues with Large Files

**Problem**: UI becomes unresponsive when processing large files

**Solutions**:
1. Increase available memory if possible
2. Try breaking large files into smaller chunks
3. Use the command-line interface instead of the UI for very large files
4. For large PDFs, consider using Document Intelligence which may handle them better

### Azure Document Intelligence Issues

**Problem**: Document Intelligence functionality doesn't work

**Solutions**:
1. Verify your Azure endpoint URL format is correct
2. Check your Azure subscription status and quota
3. Ensure network connectivity to Azure services
4. Verify authentication is set up correctly

## Additional Resources

- [MarkItDown GitHub Repository](https://github.com/microsoft/markitdown)
- [Official Python Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Azure Document Intelligence Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Detailed Installation Instructions](markitdown-ui-instructions.md)
- [User Guide](USAGE.md)

## Getting Help

If you encounter issues not covered in this guide:

1. Search existing issues on the [GitHub repository](https://github.com/microsoft/markitdown/issues)
2. Open a new issue with detailed information about your problem
3. Include your system information, Python version, and error messages