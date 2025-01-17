import os
from urllib.parse import urlparse
import asyncio

async def take_screenshot(page, url, base_dir="websites"):
    """Takes a screenshot of the current page and saves it with a unique name.

    Args:
        page: The Playwright Page object.
        url: The URL of the page being captured.
        base_dir: The base directory to save the screenshots to.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    website_dir = os.path.join(base_dir, domain)
    screenshots_dir = os.path.join(website_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    # Sanitize the URL path for the filename
    filename_base = "".join(c if c.isalnum() or c in "._-" else "_" for c in parsed_url.path.strip("/"))
    if not filename_base or filename_base == "/":
        filename_base = "index"

    # Find a unique filename
    i = 1
    while True:
        filename = f"{filename_base}_{i}.png"
        filepath = os.path.join(screenshots_dir, filename)
        if not os.path.exists(filepath):
            break
        i += 1

    try:
        await page.screenshot(path=filepath)
        print(f"  Screenshot saved to: {filepath}")
    except Exception as e:
        print(f"  Error taking screenshot: {e}")