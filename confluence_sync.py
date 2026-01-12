"""
Confluence Space Sync Module

Fetch multiple pages from a Confluence space with optional label filtering.
Supports bulk ingestion of ADRs, standards, and policies into FAISS.
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import config

load_dotenv()


def validate_confluence_config():
    """
    Validate Confluence credentials are configured.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    email = os.getenv('CONFLUENCE_EMAIL')
    token = os.getenv('CONFLUENCE_API_TOKEN')
    base_url = os.getenv('CONFLUENCE_BASE_URL')
    
    if not email or not token:
        return False, "CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN must be set in .env"
    
    if not base_url:
        return False, "CONFLUENCE_BASE_URL must be set in .env (e.g., https://yourcompany.atlassian.net/wiki)"
    
    return True, ""


def fetch_space_pages(space_key=None, labels=None, max_pages=100):
    """
    Fetch all pages from a Confluence space with optional label filtering.
    
    Args:
        space_key (str): Confluence space key (e.g., 'ARCH'). If None, uses config.CONFLUENCE_SPACE_KEY
        labels (list): List of labels to filter pages. If None, uses config.CONFLUENCE_LABELS
        max_pages (int): Maximum number of pages to fetch (default 100)
        
    Returns:
        tuple: (success, pages, error_message)
            - success (bool): Whether the operation succeeded
            - pages (list): List of dicts with 'title' and 'content' keys
            - error_message (str): Error message if failed
    """
    # Validate configuration
    is_valid, error_msg = validate_confluence_config()
    if not is_valid:
        return False, [], error_msg
    
    # Use config values if not provided
    if space_key is None:
        space_key = config.CONFLUENCE_SPACE_KEY
    if labels is None:
        labels = config.CONFLUENCE_LABELS
    
    if not space_key:
        return False, [], "No Confluence space key configured. Set CONFLUENCE_SPACE_KEY in config.env"
    
    # Get credentials
    email = os.getenv('CONFLUENCE_EMAIL')
    token = os.getenv('CONFLUENCE_API_TOKEN')
    base_url = os.getenv('CONFLUENCE_BASE_URL').rstrip('/')
    
    # Build CQL query
    cql_parts = [f'space="{space_key}"', 'type=page']
    
    # Add label filtering if specified
    if labels:
        label_conditions = ' AND '.join([f'label="{label}"' for label in labels])
        cql_parts.append(f'({label_conditions})')
    
    cql_query = ' AND '.join(cql_parts)
    
    # API endpoint for CQL search
    search_url = f"{base_url}/rest/api/content/search"
    
    all_pages = []
    start = 0
    limit = 25  # Confluence API limit per request
    
    try:
        while len(all_pages) < max_pages:
            # Make API request
            params = {
                'cql': cql_query,
                'start': start,
                'limit': limit,
                'expand': 'body.storage,version'
            }
            
            response = requests.get(
                search_url,
                params=params,
                auth=(email, token),
                timeout=30
            )
            
            if response.status_code == 401:
                return False, [], "Authentication failed. Check CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN"
            elif response.status_code == 404:
                return False, [], f"Space '{space_key}' not found or not accessible"
            elif response.status_code != 200:
                return False, [], f"Confluence API error: {response.status_code} - {response.text}"
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                break  # No more pages
            
            # Process each page
            for page in results:
                title = page.get('title', 'Untitled')
                html_content = page.get('body', {}).get('storage', {}).get('value', '')
                
                # Convert HTML to plain text
                text_content = _html_to_text(html_content)
                
                all_pages.append({
                    'title': title,
                    'content': text_content,
                    'id': page.get('id', ''),
                    'version': page.get('version', {}).get('number', 1)
                })
                
                if len(all_pages) >= max_pages:
                    break
            
            # Check if there are more pages
            if data.get('size', 0) < limit:
                break  # Last page reached
            
            start += limit
        
        return True, all_pages, ""
        
    except requests.exceptions.Timeout:
        return False, [], "Request timeout. Check your network connection and Confluence URL."
    except requests.exceptions.RequestException as e:
        return False, [], f"Network error: {str(e)}"
    except Exception as e:
        return False, [], f"Unexpected error: {str(e)}"


def _html_to_text(html_content):
    """
    Convert Confluence HTML to plain text.
    
    Args:
        html_content (str): HTML content from Confluence
        
    Returns:
        str: Plain text content
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'meta', 'link']):
        element.decompose()
    
    # Get text
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up extra whitespace
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]
    
    return '\n'.join(lines)


def get_sync_summary():
    """
    Get a summary of what would be synced based on current config.
    
    Returns:
        str: Human-readable summary
    """
    space_key = config.CONFLUENCE_SPACE_KEY
    labels = config.CONFLUENCE_LABELS
    
    if not space_key:
        return "⚠️ No Confluence space configured"
    
    summary = f"📂 Space: **{space_key}**"
    
    if labels:
        summary += f"\n🏷️ Labels: {', '.join(labels)}"
    else:
        summary += "\n🏷️ Labels: All pages (no filter)"
    
    return summary
