# MarkItDown UI - Installation and Usage Instructions

## Introduction
MarkItDown UI is a graphical user interface for the MarkItDown document conversion utility. This guide provides detailed instructions on how to install and run the markitdown-ui package.

## Package Status
**Important Note**: The markitdown-ui package is not currently available on PyPI. It must be installed from the local source code.

## Installation Requirements
- Python 3.10 or higher
- Git (to clone the repository)
- Tkinter (usually included with Python)

## Installation Steps

### Step 1: Clone the Repository
First, you need to clone the MarkItDown repository:

```
git clone https://github.com/microsoft/markitdown.git
cd markitdown
```

### Step 2: Install the Core Package with All Dependencies
Install the core MarkItDown package with all optional dependencies:

```
pip install -e packages/markitdown[all]
```

The `-e` flag installs the package in "development mode," allowing you to modify the code if needed.

### Step 3: Install the UI Package
Install the MarkItDown UI package:

```
pip install -e packages/markitdown-ui
```

## Verifying Installation

### Check Package Installation
You can verify that the packages are correctly installed by running:

```
pip list | grep markitdown
```

This should show both `markitdown` and `markitdown-ui` in the list of installed packages.

### Check Application Availability
Verify that the application is available by checking its version:

```
markitdown-ui --version
```

This should display the version of the markitdown-ui package.

## Running the Application

There are several ways to start the MarkItDown UI application:

### Method 1: Command-Line Interface
Run the application with the following command:

```
markitdown-ui
```

### Method 2: Python Module
Alternatively, you can run it as a Python module:

```
python -m markitdown_ui
```

### Method 3: Open with a Specific File
You can also start the application and immediately open a file:

```
markitdown-ui path/to/your/file.pdf
```

### Method 4: GUI Shortcut (Windows)
On Windows, you can use the GUI shortcut to avoid showing a console window:

```
markitdown-gui
```

## Available Features

MarkItDown UI provides a user-friendly interface with the following features:

### File Management
- File selection through a browse dialog
- Drag and drop support (if your system supports it)
- Recent files list in the File menu

### Conversion Options
- File type hints (extension, MIME type, charset)
- Document Intelligence integration for enhanced PDF processing
- Plugin support toggle
- Data URI handling options

### Preview and Export
- Live preview of converted Markdown
- Copy to clipboard functionality
- Save as Markdown file
- Preview rendering options

### User Interface
- Intuitive controls and status feedback
- Progress tracking for large file conversions
- Error handling with clear messages

## Troubleshooting

### Application Won't Start
- **Check Python version**: Ensure you have Python 3.10+
  ```
  python --version
  ```
- **Verify Tkinter installation**: Run
  ```
  python -c "import tkinter; print(tkinter.TkVersion)"
  ```
- **Check for dependency conflicts**: Try installing in a new virtual environment

### Unable to Convert Files
- Ensure the file format is supported
- Try specifying the file extension or MIME type manually
- Check file permissions (ensure the file isn't locked by another application)
- For large files, allow more time for conversion

### UI Rendering Issues
- Update your Tkinter installation
- Try adjusting your system's display scaling
- On Linux, ensure required dependencies are installed:
  ```
  sudo apt-get install python3-tk
  ```

### Conversion Quality Problems
- For PDF files with poor conversion quality, try enabling Document Intelligence
- For images, ensure proper OCR components are available
- For audio files, check audio quality and supported language

## Advanced Usage

### Creating Conversion Presets
You can save frequently used conversion settings by:
1. Setting up your preferred parameters
2. Converting a test file
3. Using the same settings for future similar files

### Plugin Integration
If you have additional plugins for MarkItDown:
1. Install the plugin package
2. Enable plugins in the UI
3. Configure any plugin-specific options

## Getting Help
If you encounter issues not covered in this guide:
- Check the MarkItDown documentation
- Open an issue on the GitHub repository
- Check for known issues in the issue tracker

## Project Development
Since you've installed in development mode, you can:
- Modify the source code to customize functionality
- Restart the application to see your changes
- Contribute improvements back to the main repository

## License
MarkItDown UI is licensed under the MIT License.