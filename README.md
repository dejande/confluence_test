# Confluence to LLM Context Converter

A Python tool that extracts Confluence pages and converts them into clean, LLM-optimized text format. It handles both text content and embedded images (particularly tables) using OCR technology.

## Features

- **Text Extraction**: Converts Confluence HTML to clean, readable text
- **Image Processing**: Downloads and processes embedded images using OCR
- **Table Recognition**: Extracts structured data from table images
- **LLM Optimization**: Outputs text optimized for Large Language Model consumption
- **Authentication**: Supports Confluence Cloud API authentication
- **Debug Mode**: Toggle detailed debugging information

## Installation

### Prerequisites

1. **Python 3.7+**
2. **Tesseract OCR** (for image processing)

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Setup

### 1. Get Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token value

### 2. Set Environment Variables

```bash
export CONFLUENCE_EMAIL="your.email@example.com"
export CONFLUENCE_API_TOKEN="your_api_token_here"
```

## Usage

### Basic Usage

```bash
python confluence_reader.py "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title"
```

### With Debug Output

```bash
python confluence_reader.py --debug "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title"
```

### Help

```bash
python confluence_reader.py --help
```

## Output Format

The tool generates LLM-optimized output with:

### Clean Text Content
```
# Page Title
**Type:** page
**Status:** current

Clean page content without formatting noise...
```

### Extracted Table Data
```
EXTRACTED IMAGES AND TABLES:

--- ATTACHMENT 1 ---
TABLE DATA (structured for analysis):
Headers: Team FTE Revenue Costs Utilization
Row 1: TeamA 4.3 575K 45K 55%
Row 2: TeamB 2.8 195K 62K 40%
Row 3: TeamC 3.1 280K 38K 70%
```

## Supported Content Types

- **Text Content**: Paragraphs, headers, lists, formatted text
- **Images**: PNG, JPG, GIF formats  
- **Tables**: Table images converted to structured text
- **Attachments**: Confluence file attachments with image content
- **Confluence Elements**: Native Confluence storage format (`ac:image`, `ri:attachment`)

## Debug Mode

Debug mode provides detailed information about:

- Authentication status
- HTML content analysis  
- Image detection and processing
- Download progress and file sizes
- OCR processing results
- Raw HTML saved to `debug_html.html`

## Architecture

```
confluence_reader.py
├── Authentication (Basic Auth with email + API token)
├── Content Extraction (Confluence REST API)
├── HTML Processing (BeautifulSoup)
├── Image Detection (Multiple tag types)
├── Image Download (Authenticated requests)
├── OCR Processing (Tesseract + PIL)
├── Text Cleaning (html2text + custom processing)
└── LLM Optimization (Structured output format)
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CONFLUENCE_EMAIL` | Your Atlassian account email | Yes |
| `CONFLUENCE_API_TOKEN` | Confluence API token | Yes |

### URL Formats Supported

- `https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title`
- `https://domain.atlassian.net/wiki/pages/123456`
- URLs with `pageId=123456` parameter

## Testing

### Test OCR Setup
```bash
python test_ocr.py
```

### Test with Debug Mode
```bash
python confluence_reader.py --debug "your_confluence_url"
```

## Troubleshooting

### Common Issues

**Authentication Failed (403)**
- Verify `CONFLUENCE_EMAIL` and `CONFLUENCE_API_TOKEN` are set correctly
- Ensure API token has read access to the page
- Check if page exists and is accessible

**OCR Not Working**
- Install Tesseract: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- Verify installation: `tesseract --version`

**No Images Found**
- Use `--debug` mode to see what image tags are detected
- Check `debug_html.html` for raw Confluence markup
- Some pages may use different image embedding methods

**Empty Output**
- Verify the page URL is correct and accessible
- Check page permissions in Confluence
- Use debug mode to identify specific issues

### Debug Files

When using `--debug` mode, the following files are created:
- `debug_html.html` - Raw Confluence storage format
- `test_image.png` - OCR test image (when running `test_ocr.py`)

## Dependencies

- `requests` - HTTP client for API calls
- `html2text` - HTML to text conversion
- `beautifulsoup4` - HTML parsing
- `pillow` - Image processing
- `pytesseract` - OCR text extraction

## License

This project is open source. Use freely for personal and commercial purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Run with `--debug` mode to identify specific problems
3. Open an issue with debug output and error messages