# MarkItDown UI - User Guide

## Overview

MarkItDown UI is a user-friendly graphical interface that makes it easy to convert various file formats to Markdown. Built on top of the powerful MarkItDown command-line utility, this application provides a simple way to transform documents, images, audio files, and more into clean, structured Markdown without requiring command-line knowledge.

## Prerequisites

Before using MarkItDown UI, ensure you have the following installed:

- **Python**: Version 3.10 or higher
- **Tkinter**: The standard Python interface to the Tk GUI toolkit (included with most Python installations)
- **MarkItDown package**: The core conversion functionality
- **Optional dependencies**: For specific file format support

## Installation

### Verifying Your Installation

To check if MarkItDown UI is already installed on your system, run:

```
pip show markitdown-ui
```

This command should display package information if it's installed. If not, you'll see a message indicating the package was not found.

### Installing MarkItDown UI

#### From PyPI (Recommended)

Install MarkItDown UI and all optional dependencies with:

```
pip install markitdown-ui
pip install markitdown[all]
```

This ensures you have full support for all file formats.

#### From Source

For the latest development version:

```
git clone https://github.com/microsoft/markitdown.git
cd markitdown
pip install -e packages/markitdown-ui
pip install -e packages/markitdown[all]
```

## Starting the Application

There are multiple ways to launch MarkItDown UI:

### Command Line

The simplest way to start the application:

```
markitdown-ui
```

### With a File

To open the application with a file already loaded:

```
markitdown-ui path/to/your/file.pdf
```

### As a Python Module

If you prefer running it as a Python module:

```
python -m markitdown_ui
```

### GUI Shortcut (Windows)

On Windows, you can also use:

```
markitdown-gui
```

This launches the application without showing a console window.

## UI Interface Walkthrough

The MarkItDown UI interface is divided into several key sections:

### 1. Menu Bar

- **File Menu**: Options for opening files, saving converted Markdown, and exiting the application.
- **Edit Menu**: Functions for copying Markdown to clipboard, selecting all text, and clearing the preview.
- **Help Menu**: Contains the About dialog with version information.

### 2. File Selection Area

Located at the top of the window, this section contains:
- **File Path Entry**: Shows the currently selected file path.
- **Browse Button**: Opens a file selection dialog.
- **Convert Button**: Starts the conversion process.

### 3. Parameters Panel

Contains settings that control the conversion process:
- **Extension**: Hint for the file extension when it can't be determined automatically.
- **MIME Type**: Specify the MIME type if needed.
- **Charset**: Set character encoding for text-based files.
- **Document Intelligence**: Enable Azure Document Intelligence for enhanced PDF processing.
- **Plugin Support**: Toggle the use of plugins.
- **Keep Data URIs**: Option to retain data URIs in the output.

### 4. Preview Area

- **Markdown Display**: Shows the converted Markdown content.
- **Save As Button**: Exports the Markdown to a file.
- **Copy to Clipboard Button**: Copies the entire Markdown content.

### 5. Status Bar

- Displays current application status and conversion progress.
- Shows a progress bar during conversion operations.

## Step-by-Step Usage Guide

### Basic File Conversion

1. **Start the application** using one of the methods described above.
2. **Select a file** by clicking the "Browse" button and navigating to your desired file.
3. **Click "Convert"** to process the file with default settings.
4. **Review the output** in the preview area.
5. **Save the result** by clicking "Save As..." and choosing a destination.

### Using Advanced Options

1. Follow steps 1-2 from the basic conversion process.
2. **Configure conversion parameters**:
   - For a PDF file with poor text extraction, enable "Use Document Intelligence" and provide an endpoint.
   - For a file with incorrect automatic type detection, specify the Extension or MIME Type.
   - For text files with specific encodings, set the appropriate Charset.
3. **Click "Convert"** to process with your custom settings.
4. **Review and save** the result.

## Conversion Options Explained

### Extension

- **Purpose**: Helps identify the file type when it can't be determined automatically.
- **Examples**: `.pdf`, `.docx`, `.html`
- **When to use**: When converting files without extensions or when the automatic detection fails.

### MIME Type

- **Purpose**: Provides a more precise file type hint than extension alone.
- **Examples**: `application/pdf`, `text/html`, `image/jpeg`
- **When to use**: When the file type is ambiguous or when you want to force a specific converter.

### Charset

- **Purpose**: Specifies the character encoding for text-based files.
- **Examples**: `UTF-8`, `ISO-8859-1`, `ASCII`
- **When to use**: When converting text files with non-default encodings.

### Document Intelligence

- **Purpose**: Uses Azure Document Intelligence for enhanced document processing, particularly useful for PDFs.
- **Setting up**: You need an Azure Document Intelligence endpoint URL.
- **When to use**: For complex PDF documents where the standard extraction provides poor results.

### Plugins

- **Purpose**: Extends MarkItDown's capabilities through external plugins.
- **Default**: Enabled
- **When to disable**: When you want to use only the core converters or if a plugin is causing issues.

### Keep Data URIs

- **Purpose**: Determines whether to keep embedded data URIs (e.g., for images) in the output.
- **Default**: Disabled (data URIs are extracted to separate files)
- **When to enable**: When you want a self-contained Markdown file with embedded images.

## Common Use Cases

### Converting a PDF Document

1. Start MarkItDown UI
2. Browse and select your PDF file
3. Click "Convert"
4. Review and save the Markdown output

For complex PDFs with tables, forms, or unusual layouts, enable Document Intelligence for better results.

### Converting a Word Document with Images

1. Select your DOCX file
2. Enable "Keep Data URIs" if you want images embedded in the Markdown
3. Convert and save

### Processing a Webpage or HTML File

1. Select an HTML file or paste a URL (if supported)
2. Convert to get a clean Markdown version without unnecessary styling
3. Review and save the content

### Extracting Text from Images

1. Select an image file
2. Convert to extract any visible text and metadata
3. For better OCR results, consider configuring additional OCR options if available

### Transcribing Audio Files

1. Select an audio file (MP3, WAV, etc.)
2. Convert to get a transcription as Markdown
3. Note that transcription quality depends on the audio clarity and language

## Troubleshooting

### Application Doesn't Start

- **Check Python version**: Ensure you have Python 3.10 or later
- **Verify installation**: Run `pip show markitdown-ui` to confirm it's installed
- **Check Tkinter**: Ensure Tkinter is available by running `python -c "import tkinter; tkinter._test()"`

### File Won't Convert

- **Check file access**: Ensure the file is not locked by another application
- **Try with extension hint**: Manually specify the file extension in the parameters
- **Check file format**: Ensure the file is not corrupted

### Document Intelligence Issues

- **Verify endpoint**: Ensure your Azure Document Intelligence endpoint is correct
- **Check connectivity**: Verify internet connection
- **Azure subscription**: Confirm your Azure subscription is active

### Poor Conversion Quality

- **PDF documents**: Try enabling Document Intelligence
- **Complex documents**: Some complex formatting may not convert perfectly
- **Special characters**: For files with special characters, try specifying the charset

### Missing Images in Output

- **Enable data URIs**: Check "Keep Data URIs" to embed images in the Markdown
- **Plugin issues**: Ensure all required plugins are installed if using image-specific features

## Additional Resources

- [MarkItDown GitHub Repository](https://github.com/microsoft/markitdown)
- [Full Documentation](https://github.com/microsoft/markitdown#readme)
- [Report Issues](https://github.com/microsoft/markitdown/issues)
- [Azure Document Intelligence](https://azure.microsoft.com/services/cognitive-services/document-intelligence/)

## Keyboard Shortcuts

- **Ctrl+O**: Open a file
- **Ctrl+S**: Save the converted Markdown
- **Ctrl+C**: Copy selected text
- **Ctrl+A**: Select all text in the preview
- **F1**: Show help information

---

This guide covers the basics of using MarkItDown UI. As MarkItDown continues to evolve, new features and file format support will be added to make document conversion even more powerful and versatile.