import os
import json
from curl_cffi import requests
from urllib.parse import urlparse
from utils.html_saving import save_html_cc

async def make_curl_cffi_request(url, output_dir="websites"):
    """Makes a request using curl_cffi with browser impersonation and saves the response.

    Args:
        url: The URL to make the request to.
        output_dir: The base directory to save the response to.

    Returns:
        The response object or None if an error occurred.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    website_dir = os.path.join(output_dir, domain)
    htmls_dir = os.path.join(website_dir, "htmls")
    os.makedirs(htmls_dir, exist_ok=True)

    try:
        # Use a specific impersonate version
        r = requests.get(url, impersonate="chrome110")
        r.raise_for_status()

        # Save the curl_cffi response using the new function
        await save_html_cc(r.text, url, htmls_dir)

        return r
    except requests.RequestsError as e:
        print(f"  Error making curl_cffi request to {url}: {e}")
        return None
    except Exception as e:
        print(f"  An unexpected error occurred during curl_cffi request: {e}")
        return None