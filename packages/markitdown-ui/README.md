# MarkItDown UI

A user-friendly graphical interface for the MarkItDown document conversion utility.

## Overview

MarkItDown UI is a Tkinter-based graphical user interface for the popular MarkItDown command-line utility. This UI makes it easy to convert various file formats to Markdown without having to use the command line, making the power of MarkItDown accessible to everyone.

## Features

- **Simple File Selection**: Easily browse and select files for conversion
- **Format Support**: Convert all formats supported by MarkItDown including:
  - PDF documents
  - Word documents (DOCX)
  - PowerPoint presentations (PPTX)
  - Excel spreadsheets (XLSX)
  - Images (with EXIF metadata and optional OCR)
  - Audio files (with transcription)
  - HTML pages
  - YouTube URLs
  - And many more!
- **Conversion Options**: Access all MarkItDown command-line parameters through an intuitive interface
- **Live Preview**: See the converted Markdown output instantly
- **Save Options**: Export converted Markdown to file
- **Progress Feedback**: Monitor conversion progress for larger files
- **Error Handling**: Clear error messages and troubleshooting guidance

## Installation

### From PyPI

```
pip install markitdown-ui
```

### From Source

```
git clone https://github.com/microsoft/markitdown.git
cd markitdown
pip install -e packages/markitdown-ui
```

**Note**: MarkItDown UI requires the base MarkItDown package. If you haven't installed it yet, use:

```
pip install markitdown[all]
```

## Usage

### Starting the Application

Simply run:

```
markitdown-ui
```

Or with Python:

```
python -m markitdown_ui
```

### Using the Interface

1. **Select a File**: Click the "Browse" button to select the file you want to convert.
2. **Configure Options**: Set any conversion options (extension, MIME type, etc.) if needed.
3. **Convert**: Click the "Convert" button to start the conversion process.
4. **Preview and Save**: View the Markdown output in the preview area and click "Save" to export it to a file.

## Relation to CLI Version

The UI version uses the same core conversion functionality as the command-line version, providing identical results. The UI simply provides a graphical way to access these features without requiring command-line knowledge.

Key differences:

- **Accessibility**: The UI is more approachable for users unfamiliar with command-line interfaces
- **Visualization**: Live preview of conversion results
- **Convenience**: No need to remember command-line arguments and syntax

## Advanced Features

- **Plugin Support**: Enable or disable MarkItDown plugins through the UI
- **Azure Document Intelligence**: Configure Azure Document Intelligence for enhanced conversion capabilities
- **LLM Integration**: Configure Large Language Model support for image descriptions and other AI-enhanced features
- **Batch Processing**: Convert multiple files at once (coming soon)

## Requirements

- Python 3.10 or higher
- Tkinter (included with most Python installations)
- MarkItDown package

## Contributing

Contributions to improve MarkItDown UI are welcome! Please see the main project's [contribution guidelines](https://github.com/microsoft/markitdown#contributing) for more information.

## License

MarkItDown UI is licensed under the MIT License. See the LICENSE file for more details.