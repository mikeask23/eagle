import asyncio
import json
import os
from playwright.async_api import TimeoutError
from utils.url_filtering import is_product_catalogue_api_url
from utils.response_filtering import find_keywords_and_objects_in_response  # Only import this function
from utils.html_saving import save_html, save_html_cc
from utils.curl_cffi_request import make_curl_cffi_request
from utils.screenshot_utils import take_screenshot
from utils.api_handling import save_api_response
from utils.html_processing import find_keywords_and_objects_in_scripts, process_html_files
from urllib.parse import urlparse

async def process_responses(url, base_dir="websites"):
    """
    Loads saved API responses, analyzes keyword diversity, and saves the top responses.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    api_dir = os.path.join(base_dir, domain, "apis")
    json_dir = os.path.join(base_dir, domain, "jsons")
    os.makedirs(json_dir, exist_ok=True)

    responses = []
    # 1. Load all saved responses from the /apis directory
    for filename in os.listdir(api_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(api_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    # Attempt to load as JSON, otherwise treat as text
                    try:
                        response_content = json.load(f)
                        response_type = "json"
                    except json.JSONDecodeError:
                        f.seek(0)  # Reset file pointer
                        response_content = f.read()
                        response_type = "text"
                    responses.append((response_content, response_type))
            except Exception as e:
                print(f"Error loading response from {filepath}: {e}")

    # 2. Analyze keywords and count unique keywords for each response
    keyword_counts = []
    results = []
    for response_content, response_type in responses:
        result = find_keywords_and_objects_in_response(response_content, response_type)
        if result:
            unique_keyword_count = len(set(result["keywords_found"])) # Count unique keywords
            result["keyword_count"] = unique_keyword_count
            keyword_counts.append(unique_keyword_count)
            results.append(result)

    # 3. Find the two highest keyword counts
    if not keyword_counts:
        print("No responses found for keyword analysis.")
        return

    keyword_counts.sort(reverse=True)
    top_two_counts = sorted(list(set(keyword_counts)), reverse=True)[:2]

    # 4. Filter responses based on the top two counts
    top_responses = [
        result for result in results if result["keyword_count"] in top_two_counts
    ]

    # 5. Save the top responses
    output_path = os.path.join(json_dir, "responses.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(top_responses, f, indent=4, ensure_ascii=False)

    print(f"Processed responses, saved top responses based on keyword diversity to: {output_path}")

async def process_page(page, url, next_url_event):
    """Captures requests, filters, saves HTML, makes curl_cffi request, and handles user input."""
    print(f"Processing: {url}")
    captured_requests = []

    # Create directories
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
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

        # Stage 1: URL filtering (Keep this)
        if is_product_catalogue_api_url(request.url):
            print(f"  Request: {request.method} {request.url}")

            # Stage 2: Content-Type Filtering (Keep this)
            if "application/json" in content_type or "text/plain" in content_type or "text/html" in content_type or "application/javascript" in content_type:
                try:
                    # We will save all responses that pass URL and content-type filtering
                    if "application/json" in content_type or "text/plain" in content_type:
                        response_body = await response.json()
                    else:  # "text/html" or "application/javascript"
                        response_body = await response.text()

                    data = {
                        "url": request.url,
                        "response_body": response_body,
                    }
                    captured_requests.append(data)
                    save_api_response(response_body, request.url, api_dir)

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

        # Process API responses for keyword diversity
        await process_responses(url)  # Call after saving all responses

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