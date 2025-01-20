import asyncio
import json
import re
from urllib.parse import urlparse
import json_repair

def is_product_catalogue_api_url(url):
    """
    Filters URLs to identify potential product catalogue API endpoints.
    """
    positive_keywords = [
        "api", "search", "products", "items", "product-search", "productsearch",
        "catalogue", "catalog", "list", "browse", "query", "filter",
        "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10",
        "graphql",
        "page", "start", "offset", "limit", "sz", "pagesize",
        "sale", "clearance", "deals", "discount", "outlet",
        "cgid", "collections", "demandware.store", "mobify",
        "category", "categories", "id", "ids", "sku", "skus",
        "inventory", "stock", "availability", "options", "variants",
        "attributes", "recommendations", "orchestra", "getdeals", "zgw"
    ]

    negative_keywords = [
        "assets", "google-analytics", "analytics", "ga.", "collect", "v1/b", "v1/p",
        "v1/t", "v1/i", "v1/a", "track", "event", "metrics", "pxl", "pixel",
        "t.gif", "tr.gif", "log", "data", "doubleclick", "adservice", "ads",
        "pubads", "gampad", "pagead", "syndication", "securepubads", "adx",
        "adnxs", "appnexus", "criteo", "rubicon", "openx", "pubmatic",
        "indexexchange", "amazon-adsystem", "media.net", "yieldmo",
        "taboola", "outbrain", "connect.facebook", "platform.twitter",
        "api.instagram", "api.pinterest", "api.linkedin", "googletagmanager",
        "gtm.", "segment", "tealium", "ensighten", "optimizely",
        "visualwebsiteoptimizer", "segment", "tealium", "mparticle",
        "cdn.example.com/api", "assets.example.com/api", "maps.googleapis.com",
        "geolocation", "places", "directions", "graph.facebook.com",
        "api.twitter.com", "upload", "geolocation", "maps", "places",
        "directions"
    ]

    # Check for negative keywords first (more efficient)
    for neg_keyword in negative_keywords:
        if neg_keyword.lower() in url.lower():
            return False  # Definitely not a product API

    # Then check for positive keywords
    for keyword in positive_keywords:
        if keyword.lower() in url.lower():
            return True

    return False  # Doesn't match positive or negative criteria

def find_keywords_and_objects_in_response(response_content, response_type="json"):
    """
    Analyzes response content for keywords and extracts JSON objects.
    """
    product_identifiers = [
        "id", "sku", "upc", "ean", "gtin", "mpn", "asin",
        "product_id", "item_id", "productId", "itemId"
    ]
    pricing_keywords = [
        "price", "sale_price", "original_price", "list_price",
        "msrp", "discount", "currency"
    ]
    product_attributes = [
        "name", "title", "description", "short_description",
        "brand", "category", "image", "url", "color", "size",
        "dimensions", "weight"
    ]
    all_keywords = product_identifiers + pricing_keywords + product_attributes

    # Convert response to text for processing
    if response_type == "json":
        try:
            if not isinstance(response_content, str):
                response_text = json.dumps(response_content)
            else:
                response_text = response_content
        except Exception as e:
            print(f"Error converting JSON response: {e}")
            return None
    else:
        response_text = response_content

    # Find keywords
    keywords_found = [
        keyword for keyword in all_keywords if keyword.lower() in response_text.lower()
    ]

    # Find JSON objects
    potential_json_objects = []
    if response_type == "json":
        try:
            if isinstance(response_content, str):
                json_obj = json.loads(response_content)
            else:
                json_obj = response_content
            potential_json_objects.append(json.dumps(json_obj))
        except Exception as e:
            print(f"Error processing JSON response: {e}")

    for match in re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text):
        if match not in potential_json_objects:
            potential_json_objects.append(match)

    repaired_json_objects = []
    for obj_str in potential_json_objects:
        try:
            repaired = json_repair.repair_json(obj_str, return_objects=True)
            if repaired:
                repaired_json_objects.append(repaired)
        except Exception as e:
            print(f"Error repairing JSON object: {e}")
            continue

    score = len(keywords_found)

    return {
        "response_content": response_text,
        "keywords_found": keywords_found,
        "json_objects": repaired_json_objects,
        "score": score
    }

async def process_api_responses(browser, page, url, next_url_event):
    """
    Monitors, filters, and processes API responses until next_url_event is set.
    Returns the top responses based on keyword diversity.
    """
    captured_responses = []

    async def handle_response(response):
        nonlocal captured_responses
        request = response.request
        content_type = response.headers.get("content-type", "").lower()

        if is_product_catalogue_api_url(request.url):
            async def process_body():
                nonlocal captured_responses
                try:
                    if response.status >= 300 and response.status < 400:
                        print(f"    Skipping processing of redirect response: {request.url}")
                        return

                    response_body = None
                    if "application/json" in content_type or "text/plain" in content_type:
                        try:
                            response_body = await response.json()
                        except json.JSONDecodeError:
                            text_content = await response.text()
                            if text_content.strip():
                                try:
                                    response_body = json.loads(json_repair.repair_json(text_content))
                                except json.JSONDecodeError:
                                    print(f"    Could not parse or repair JSON from: {request.url}")
                                    return
                            else:
                                return
                    elif "text/html" in content_type or "application/javascript" in content_type:
                        response_body = await response.text()

                    if response_body is not None:
                        result = find_keywords_and_objects_in_response(response_body,
                                                                        "json" if isinstance(response_body, (dict, list)) else "text")
                        if result:
                            result["url"] = request.url
                            captured_responses.append(result)

                except Exception as e:
                    print(f"    Error processing response: {e} - URL: {request.url}")

            # Await the process_body coroutine
            await process_body()

    page.on("response", handle_response)
    await page.set_viewport_size({"width": 1280, "height": 1120})
    await page.evaluate("document.body.style.zoom = '70%'")

    try:
        await page.goto(url, timeout=60000)

        # Wait until next_url_event is set
        await next_url_event.wait()

    except TimeoutError:
        print(f"  Timeout navigating to {url}. Proceeding anyway.")
    except Exception as e:
        print(f"  Error processing {url}: {e}")

    # Remove the response handler from the page object
    page.remove_listener("response", handle_response)

    # Find the two highest unique keyword counts
    keyword_counts = set()
    for result in captured_responses:
        unique_keyword_count = len(set(result["keywords_found"]))
        result["keyword_count"] = unique_keyword_count
        keyword_counts.add(unique_keyword_count)

    top_two_counts = sorted(keyword_counts, reverse=True)[:2]

    # Capture all responses with keyword counts in the top two unique counts
    top_responses = [
        result for result in captured_responses if result["keyword_count"] in top_two_counts
    ]

    return top_responses