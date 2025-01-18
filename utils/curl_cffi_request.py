import os
from curl_cffi import requests

async def make_curl_cffi_request(url):
    """Makes a request using curl_cffi with browser impersonation.

    Args:
        url: The URL to make the request to.

    Returns:
        The response text or None if an error occurred.
    """
    try:
        # Use Chrome 120 impersonation
        r = requests.get(url, impersonate="chrome120")
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  Error making curl_cffi request to {url}: {e}")
        return None