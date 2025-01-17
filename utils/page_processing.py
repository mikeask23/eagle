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
from utils.html_processing import extract_and_repair_json
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
                        save_api_response(response_body, request.url, api_dir)  # Save to api_dir
                elif "text/html" in content_type or "application/javascript" in content_type:
                    response_body = await response.text()
                    print(f"    Response body received as text.")
                    if is_product_data_response(response_body, "text"):
                        data = {
                            "url": request.url,
                            "response_body": response_body,
                        }
                        captured_requests.append(data)
                        save_api_response(response_body, request.url, api_dir)  # Save to api_dir
                else:
                    print(f"    Unsupported content type: {content_type}")

            except Exception as e:
                print(f"    Error processing response: {e}")

    page.on("response", handle_response)
    await page.set_viewport_size({"width": 1280, "height": 1120})
    await page.evaluate("document.body.style.zoom = '70%'")

    try:
        await page.goto(url, timeout=60000)

        # Save the full HTML content after page is loaded
        html_filename = url.split('//')[1].replace('/', '_') + ".html"
        await save_html(page, url, htmls_dir)  # Save to htmls_dir

        # Make a request using curl_cffi and save the response (in the background)
        cc_response = await make_curl_cffi_request(url, website_dir)

        # Construct path for the curl_cffi HTML file
        cc_html_filename = f"{domain}_cc.html"
        cc_html_path = os.path.join(htmls_dir, cc_html_filename)

        # Extract and repair JSON from HTML
        html_path = os.path.join(htmls_dir, html_filename)
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Extract and repair JSON from both HTML files
            extract_and_repair_json(html_content, json_dir, cc_html_path)

        # Wait for the user to signal for the next URL
        print("  Waiting for 'n' key to proceed to the next URL...")
        await next_url_event.wait()

    except TimeoutError:
        print(f"  Timeout navigating to {url}. Proceeding anyway.")
    except Exception as e:
        print(f"  Error navigating to {url}: {e}")
    finally:
        page.remove_listener("response", handle_response)

        # Save captured requests to JSON file (in api_dir)
        output_file_path = os.path.join(api_dir, "captured_requests.json")
        with open(output_file_path, "w") as f:
            json.dump(captured_requests, f, indent=2)
        print(f"Captured requests for {url} saved to {output_file_path}")