# html_saving.py
import os
import aiofiles
from urllib.parse import urlparse

def ensure_directory(path):
    """Ensures the directory exists, creates it if it doesn't."""
    if not os.path.exists(path):
        os.makedirs(path)

async def save_html(page, url, base_dir="websites"):
    """Saves the browser-rendered HTML content of the current page.

    Args:
        page: The Playwright Page object
        url: The URL of the page being saved
        base_dir: Base directory for all saved files
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    
    # Create directory structure: websites/{domain}/htmls/
    html_dir = os.path.join(base_dir, domain, "htmls")
    ensure_directory(html_dir)
    
    # Save as browser.html
    filepath = os.path.join(html_dir, "browser.html")
    
    html_content = await page.content()
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(html_content)
    print(f"  Browser HTML saved to: {filepath}")
    return filepath

async def save_html_cc(content, url, base_dir="websites"):
    """Saves the curl_cffi HTML content.

    Args:
        content: The HTML content from curl_cffi response
        url: The URL of the page being saved
        base_dir: Base directory for all saved files
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    
    # Create directory structure: websites/{domain}/htmls/
    html_dir = os.path.join(base_dir, domain, "htmls")
    ensure_directory(html_dir)
    
    # Save as cc.html
    filepath = os.path.join(html_dir, "cc.html")
    
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(content)
    print(f"  Curl_cffi HTML saved to: {filepath}")
    return filepath