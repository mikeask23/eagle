import asyncio
import json
import os
from playwright.async_api import TimeoutError
from api_handling import process_api_responses
from html_processing import save_html, save_html_cc, make_curl_cffi_request, process_html_files
from utils.screenshot_utils import take_screenshot
from urllib.parse import urlparse

async def process_page(browser, page, url, next_url_event):
    """Captures requests, filters, saves HTML, makes curl_cffi request, and handles user input."""
    print(f"Processing: {url}")

    # Create directories
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    website_dir = os.path.join("websites", domain)
    os.makedirs(website_dir, exist_ok=True)

    json_dir = os.path.join(website_dir, "jsons")
    os.makedirs(json_dir, exist_ok=True)

    # Process API responses (capture until 'n' is pressed)
    top_responses = await process_api_responses(browser, page, url, next_url_event)

    # Save the top responses to responses.json
    output_path = os.path.join(json_dir, "responses.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(top_responses, f, indent=4, ensure_ascii=False)

    print(f"Processed API responses, saved top responses to: {output_path}")

    # --- HTML processing happens AFTER API response capturing ---
    htmls_dir = os.path.join(website_dir, "htmls")
    os.makedirs(htmls_dir, exist_ok=True)

    # Save the browser-rendered HTML
    await save_html(page, url, base_dir="websites")

    # Make a request using curl_cffi and save the response
    print("\nAttempting curl_cffi request...")
    cc_response_content = await make_curl_cffi_request(url)
    
    if cc_response_content:
        try:
            await save_html_cc(cc_response_content, url, base_dir="websites")
            print("  Successfully saved curl_cffi response")
        except Exception as e:
            print(f"  Error saving curl_cffi response: {str(e)}")
    else:
        print("  No valid response from curl_cffi request")

    # Process both HTML files to extract JSON data
    process_html_files(url, base_dir="websites")

    # Signal that processing for this URL is
    print("  URL processing complete.")