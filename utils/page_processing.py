import asyncio
import json
import os
from playwright.async_api import TimeoutError
from utils.url_filtering import is_product_catalogue_api_url
from utils.response_filtering import is_product_data_response
from utils.html_saving import save_html, save_html_cc
from utils.curl_cffi_request import make_curl_cffi_request
from utils.screenshot_utils import take_screenshot
from utils.api_handling import save_api_response
from utils.html_processing import find_keywords_and_objects_in_scripts, process_html_files
from urllib.parse import urlparse

async def process_page(page, url, next_url_event):
    """Captures requests, filters, saves HTML, makes curl_cffi request, and handles user input."""
    print(f"Processing: {url}")
    captured_requests = []

    # Create a directory for this website if it doesn't exist
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")  # Replace : to avoid issues with Windows paths
    website_dir = os.path.join("websites", domain)
    os.makedirs(website_dir, exist_ok=True)

    htmls_dir = os.path.join(website_dir, "htmls")
    os.makedirs(htmls_dir, exist_ok=True)

    json_dir = os.path.join(website_dir, "jsons")
    os.makedirs(json_dir, exist_ok=True)

    api_dir = os.path.join(website_dir, "apis")
    os.makedirs(api_dir, exist_ok=True)

    async def handle_response(response):
        request = response.request
        content_type = response.headers.get("content-type", "").lower()

        # Stage 1: URL filtering
        if is_product_catalogue_api_url(request.url):
            print(f"  Request: {request.method} {request.url}")
            try:
                # Stage 2: Response body filtering
                if "application/json" in content_type or "text/plain" in content_type:
                    response_body = await response.json()
                    print(f"    Response body received successfully.")
                    if is_product_data_response(json.dumps(response_body), "json"):
                        data = {
                            "url": request.url,
                            "response_body": response_body,
                        }
                        captured_requests.append(data)
                        save_api_response(response_body, request.url, api_dir)
                elif "text/html" in content_type or "application/javascript" in content_type:
                    response_body = await response.text()
                    print(f"    Response body received as text.")
                    if is_product_data_response(response_body, "text"):
                        data = {
                            "url": request.url,
                            "response_body": response_body,
                        }
                        captured_requests.append(data)
                        save_api_response(response_body, request.url, api_dir)
                else:
                    print(f"    Unsupported content type: {content_type}")
            except Exception as e:
                print(f"    Error processing response: {e}")

    page.on("response", handle_response)
    await page.set_viewport_size({"width": 1280, "height": 1120})
    await page.evaluate("document.body.style.zoom = '70%'")

    try:
        await page.goto(url, timeout=60000)

        # Save the browser-rendered HTML
        await save_html(page, url)

        # Make a request using curl_cffi and save the response
        cc_response = await make_curl_cffi_request(url)
        if cc_response:
            await save_html_cc(cc_response, url)

        # Process both HTML files to extract JSON data
        process_html_files(url)

        # Wait for user input to move to next URL
        print("  Waiting for 'n' key to proceed to the next URL...")
        if next_url_event:
            await next_url_event.wait()

    except TimeoutError:
        print(f"  Timeout navigating to {url}. Proceeding anyway.")
    except Exception as e:
        print(f"  Error processing {url}: {e}")

    # Clear the event for the next URL
    if next_url_event:
        next_url_event.clear()