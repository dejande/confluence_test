#!/usr/bin/env python3

import os
import sys
import json
import argparse
import requests
import base64
import html2text
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract

# Global debug flag
DEBUG_MODE = False

def debug_print(message):
    """Print debug message only if debug mode is enabled"""
    if DEBUG_MODE:
        print(f"DEBUG: {message}")

def describe():
    """Agent description for orchestrator discovery"""
    return {
        "name": "confluence_converter",
        "description": "Extracts Confluence pages and converts them to LLM-optimized text with embedded image/table processing using OCR",
        "capabilities": ["extract_confluence_content", "convert_html_to_text", "process_table_images", "ocr_extraction"],
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Confluence page URL (e.g., https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title)"
                },
                "email": {
                    "type": "string", 
                    "description": "Confluence account email (optional if CONFLUENCE_EMAIL env var is set)"
                },
                "api_token": {
                    "type": "string",
                    "description": "Confluence API token (optional if CONFLUENCE_API_TOKEN env var is set)"
                },
                "debug": {
                    "type": "boolean",
                    "description": "Enable debug output with detailed processing information",
                    "default": False
                }
            },
            "required": ["url"]
        }
    }

def test_auth(base_url, email, token):
    """Test authentication by getting user info"""
    api_url = f"{base_url}/wiki/rest/api/user/current"
    
    auth_string = f"{email}:{token}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            debug_print(f"Authentication successful. User: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            debug_print(f"Authentication failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        debug_print(f"Auth test error: {e}")
        return False

def get_confluence_content(base_url, page_id, email, token):
    """Fetch content from Confluence page via API"""
    api_url = f"{base_url}/wiki/rest/api/content/{page_id}?expand=body.storage"
    
    # Create basic auth string
    auth_string = f"{email}:{token}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json'
    }
    
    debug_print(f"Fetching: {api_url}")
    
    try:
        response = requests.get(api_url, headers=headers)
        debug_print(f"Response status: {response.status_code}")
        
        if response.status_code == 403:
            debug_print("403 Forbidden - Possible causes:")
            debug_print("1. Page doesn't exist or was deleted")
            debug_print("2. User doesn't have permission to view this page")
            debug_print("3. Page is in a restricted space")
            debug_print("4. Invalid API token")
            debug_print(f"Response body: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching content: {e}")

def download_image(url, auth_header):
    """Download image from URL"""
    try:
        response = requests.get(url, headers={'Authorization': auth_header})
        response.raise_for_status()
        return response.content
    except:
        return None

def extract_table_from_image(image_data):
    """Extract table data from image using OCR"""
    try:
        from io import BytesIO
        image = Image.open(BytesIO(image_data))
        
        # Use OCR to extract text with better table detection
        text = pytesseract.image_to_string(image, config='--psm 6')
        
        # Clean and structure the text for LLM consumption
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) > 1:
            # Process lines to make them more LLM-friendly
            cleaned_lines = []
            for line in lines:
                # Replace multiple spaces with single separator
                cleaned_line = ' '.join(line.split())
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
            
            # Format as structured data
            if len(cleaned_lines) > 0:
                table_text = "TABLE DATA (structured for analysis):\n"
                
                # First line is likely headers
                if cleaned_lines:
                    table_text += f"Headers: {cleaned_lines[0]}\n"
                
                # Remaining lines are data rows
                for i, row in enumerate(cleaned_lines[1:], 1):
                    table_text += f"Row {i}: {row}\n"
                
                return table_text
            else:
                return "TABLE DATA:\n" + "\n".join(lines)
        else:
            return f"IMAGE CONTENT: {text}"
            
    except Exception as e:
        return f"[Unable to process image: {e}]"

def process_confluence_content(content, base_url, auth_header):
    """Process Confluence content with image extraction"""
    if 'body' not in content or 'storage' not in content['body']:
        return "No content body found"
    
    html_content = content['body']['storage']['value']
    debug_print(f"HTML content length: {len(html_content)}")
    
    # Save raw HTML for debugging
    if DEBUG_MODE:
        with open('debug_html.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        debug_print("Saved raw HTML to debug_html.html")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Debug: Show all image tags found
    images = soup.find_all('img')
    debug_print(f"Found {len(images)} image tags")
    
    # Also check for other image-related tags
    attachments = soup.find_all('ac:image')
    debug_print(f"Found {len(attachments)} ac:image tags")
    
    # Check for ri:attachment tags (Confluence specific)
    ri_attachments = soup.find_all('ri:attachment')
    debug_print(f"Found {len(ri_attachments)} ri:attachment tags")
    
    # Print all image sources found
    all_imgs = images + attachments
    for i, img in enumerate(all_imgs):
        src = img.get('src') or img.get('ri:filename') or str(img)
        debug_print(f"Image {i+1}: {src}")
    
    image_texts = []
    
    # Process regular img tags
    for i, img in enumerate(images):
        img_src = img.get('src')
        if img_src:
            # Handle relative URLs
            if not img_src.startswith('http'):
                img_src = urljoin(base_url, img_src)
            
            debug_print(f"Processing image {i+1}/{len(images)}: {img_src}")
            
            image_data = download_image(img_src, auth_header)
            if image_data:
                debug_print(f"Successfully downloaded {len(image_data)} bytes")
                table_text = extract_table_from_image(image_data)
                image_texts.append(f"\n--- IMAGE {i+1} ---\n{table_text}\n")
                img.replace_with(f"[IMAGE_{i+1}_PROCESSED_BELOW]")
            else:
                debug_print(f"Failed to download image: {img_src}")
    
    # Process Confluence-specific attachment tags
    for i, attachment in enumerate(ri_attachments):
        filename = attachment.get('ri:filename')
        if filename:
            # Construct attachment URL
            attachment_url = f"{base_url}/wiki/download/attachments/{content['id']}/{filename}"
            debug_print(f"Processing attachment {i+1}: {attachment_url}")
            
            image_data = download_image(attachment_url, auth_header)
            if image_data:
                debug_print(f"Successfully downloaded attachment {len(image_data)} bytes")
                table_text = extract_table_from_image(image_data)
                image_texts.append(f"\n--- ATTACHMENT {i+1} ---\n{table_text}\n")
    
    # Convert remaining HTML to clean text
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0
    h.single_line_break = True
    h.mark_code = False
    h.escape_all = False
    h.unicode_snob = True
    
    text_content = h.handle(str(soup))
    
    # Clean up text
    lines = text_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            line = line.replace('**', '').replace('*', '')
            line = line.replace('##', '').replace('#', '')
            line = line.replace('  ', ' ')
            cleaned_lines.append(line)
    
    clean_text = ' '.join(cleaned_lines)
    
    # Combine text and image content
    final_content = clean_text
    if image_texts:
        final_content += "\n\nEXTRACTED IMAGES AND TABLES:\n" + "".join(image_texts)
    elif DEBUG_MODE:
        final_content += "\n\nDEBUG: No images were successfully processed"
    
    return final_content

def run(params):
    """Main agent execution function"""
    global DEBUG_MODE
    DEBUG_MODE = params.get('debug', False)
    
    try:
        # Get credentials
        email = params.get('email') or os.getenv('CONFLUENCE_EMAIL')
        token = params.get('api_token') or os.getenv('CONFLUENCE_API_TOKEN')
        
        if not email:
            return {"status": "error", "message": "CONFLUENCE_EMAIL not provided in params or environment variables"}
        if not token:
            return {"status": "error", "message": "CONFLUENCE_API_TOKEN not provided in params or environment variables"}
        
        # Parse URL
        url = params['url']
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        page_id = extract_page_id_from_url(url)
        
        # Test authentication
        if DEBUG_MODE:
            debug_print("Testing authentication...")
        if not test_auth(base_url, email, token):
            return {"status": "error", "message": "Authentication failed. Please check your credentials."}
        
        # Fetch content
        content = get_confluence_content(base_url, page_id, email, token)
        
        # Create auth header for image downloads
        auth_string = f"{email}:{token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        auth_header = f'Basic {encoded_auth}'
        
        # Process content
        processed_content = process_confluence_content(content, base_url, auth_header)
        
        return {
            "status": "success",
            "title": content['title'],
            "type": content['type'],
            "status_field": content['status'],
            "content": processed_content,
            "page_id": content['id'],
            "url": url
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def extract_page_id_from_url(url):
    """Extract page ID from Confluence URL"""
    if '/pages/' in url:
        return url.split('/pages/')[-1].split('/')[0]
    elif 'pageId=' in url:
        return url.split('pageId=')[-1].split('&')[0]
    else:
        raise ValueError("Unable to extract page ID from URL. Please provide a valid Confluence page URL.")

def legacy_main():
    """Legacy CLI interface for backward compatibility"""
    parser = argparse.ArgumentParser(description='Fetch and print Confluence page content')
    parser.add_argument('url', help='Confluence page URL')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Convert to new format and run
    params = {
        'url': args.url,
        'debug': args.debug
    }
    
    result = run(params)
    
    if result['status'] == 'success':
        print(f"# {result['title']}")
        print(f"**Type:** {result['type']}")
        print(f"**Status:** {result['status_field']}")
        print()
        print(result['content'])
    else:
        print(f"Error: {result['message']}")
        sys.exit(1)

if __name__ == '__main__':
    # Check if running in agent mode (JSON input) or legacy mode (URL input)
    if len(sys.argv) >= 2 and sys.argv[1].startswith('{'):
        # Agent mode: JSON input
        try:
            params = json.loads(sys.argv[1])
            result = run(params)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}, indent=2))
            sys.exit(1)
    elif len(sys.argv) >= 2:
        # Legacy mode: URL input
        legacy_main()
    else:
        # Show usage for both modes
        print("Usage:")
        print("  Agent mode:  python confluence_reader.py '{\"url\": \"https://...\", \"debug\": true}'")
        print("  Legacy mode: python confluence_reader.py https://confluence-url --debug")
        print()
        print("Agent description:")
        desc = describe()
        print(json.dumps(desc, indent=2))
        sys.exit(1)