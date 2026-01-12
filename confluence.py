"""
Confluence Integration Module

Fetch content from Confluence pages for automated auditing.
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def fetch_page_content(page_url):
    """
    Fetch content from a Confluence page URL.
    
    Args:
        page_url (str): Full Confluence page URL
                       e.g., https://yourcompany.atlassian.net/wiki/spaces/ARCH/pages/123456/Design+Doc
    
    Returns:
        tuple: (page_title, page_content_text, success_status)
               Returns (None, error_message, False) on failure
    """
    try:
        # Get Confluence credentials from environment
        confluence_email = os.getenv('CONFLUENCE_EMAIL')
        confluence_api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if not confluence_email or not confluence_api_token:
            return None, "❌ Confluence credentials not configured. Please set CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN in .env file.", False
        
        # Parse the page ID from URL
        # Format: https://domain.atlassian.net/wiki/spaces/SPACE/pages/PAGEID/Title
        if '/pages/' not in page_url:
            return None, "❌ Invalid Confluence URL format. Expected: .../pages/PAGE_ID/...", False
        
        # Extract base URL and page ID
        parts = page_url.split('/pages/')
        if len(parts) < 2:
            return None, "❌ Could not extract page ID from URL", False
        
        base_url = parts[0].split('/wiki')[0]  # Get domain part
        page_id = parts[1].split('/')[0]  # Get page ID (first part after /pages/)
        
        # Construct API endpoint
        api_url = f"{base_url}/wiki/rest/api/content/{page_id}?expand=body.storage,version,space"
        
        # Make API request
        response = requests.get(
            api_url,
            auth=(confluence_email, confluence_api_token),
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 401:
            return None, "❌ Authentication failed. Please check your CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN.", False
        elif response.status_code == 404:
            return None, f"❌ Page not found. Please verify the URL and ensure you have access to page ID: {page_id}", False
        elif response.status_code != 200:
            return None, f"❌ Error fetching page (HTTP {response.status_code}): {response.text}", False
        
        # Parse response
        data = response.json()
        page_title = data.get('title', 'Untitled')
        html_content = data.get('body', {}).get('storage', {}).get('value', '')
        
        if not html_content:
            return None, "❌ Page content is empty", False
        
        # Convert HTML to plain text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not text.strip():
            return None, "❌ Could not extract text content from page", False
        
        return page_title, text, True
        
    except requests.exceptions.RequestException as e:
        return None, f"❌ Network error: {str(e)}", False
    except Exception as e:
        return None, f"❌ Error: {str(e)}", False


def validate_confluence_config():
    """
    Check if Confluence credentials are configured.
    
    Returns:
        tuple: (is_configured, message)
    """
    confluence_email = os.getenv('CONFLUENCE_EMAIL')
    confluence_api_token = os.getenv('CONFLUENCE_API_TOKEN')
    
    if not confluence_email or not confluence_api_token:
        return False, "Confluence integration not configured. Set CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN in .env file."
    
    return True, "Confluence integration configured"


if __name__ == "__main__":
    # Test the Confluence integration
    print("=" * 80)
    print("Confluence Integration Test")
    print("=" * 80)
    
    # Check configuration
    is_configured, msg = validate_confluence_config()
    print(f"\nConfiguration: {msg}")
    
    if is_configured:
        test_url = input("\nEnter a Confluence page URL to test: ").strip()
        
        if test_url:
            print("\nFetching page content...")
            title, content, success = fetch_page_content(test_url)
            
            if success:
                print(f"\n✅ Success!")
                print(f"\nPage Title: {title}")
                print(f"\nContent Preview (first 500 chars):\n{content[:500]}...")
                print(f"\nTotal content length: {len(content)} characters")
            else:
                print(f"\n{content}")  # Error message
    else:
        print("\n⚠️ Please configure Confluence credentials in your .env file:")
        print("   CONFLUENCE_EMAIL=your-email@company.com")
        print("   CONFLUENCE_API_TOKEN=your-api-token")
