import os
import aiofiles
from urllib.parse import urlparse

async def save_html(page, url, output_dir):
    """Saves the full HTML content of the current page to a file.

    Args:
        page: The Playwright Page object.
        url: The URL of the page being saved.
        output_dir: The directory to save the HTML files to.
    """
    parsed_url = urlparse(url)
    url_path = parsed_url.path.strip("/")
    if url_path == "" or url_path == "/":
        url_path = "index"  # Default filename for root path

    # Sanitize the path for filename
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in url_path)
    if not filename.endswith(".html"):
        filename += ".html"

    filepath = os.path.join(output_dir, filename)

    html_content = await page.content()
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(html_content)
    print(f"  HTML saved to: {filepath}")

async def save_html_cc(content, url, output_dir):
    """Saves the HTML content from curl_cffi request to a file.

    Args:
        content: The HTML content from the curl_cffi response.
        url: The URL of the page being saved.
        output_dir: The directory to save the HTML files to.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    url_path = parsed_url.path.strip("/")
    if url_path == "" or url_path == "/":
        url_path = "index"  # Default filename for root path

    # Sanitize the path for filename
    filename = f"{domain}_cc.html"  # Name format: domain_cc.html

    filepath = os.path.join(output_dir, filename)

    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(content)
    print(f"  curl_cffi HTML saved to: {filepath}")