import json
import re
import json_repair
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse

def is_product_data_response(response_content, response_type="json"):
    """
    Analyzes the response body to confirm if it contains product data (Stage 2).
    """
    try:
        if response_type == "json":
            data = json.loads(response_content) if isinstance(response_content, str) else response_content
        elif response_type == "text":  # Handle as text
            data = response_content
        else:
            return False  # Unsupported response type

        result = find_keywords_and_objects_in_response(response_content, response_type)
        return result["score"] >= 4  # Same threshold as original

    except Exception as e:
        print(f"Error during response body analysis: {e}")
        return False

def find_keywords_and_objects_in_response(response_content, response_type="json"):
    """
    Analyzes response content for keywords and extracts JSON objects, similar to HTML processing.
    
    Args:
        response_content: The response content as string or JSON
        response_type: Either "json" or "text"
    
    Returns:
        dict containing keywords found and JSON objects
    """
    # Keywords lists (same as in HTML processing)
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
            # If it's already JSON, convert to string for consistent processing
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
        keyword
        for keyword in all_keywords
        if keyword.lower() in response_text.lower()
    ]

    # Find JSON objects
    potential_json_objects = []
    
    # If response is already JSON, add it as is
    if response_type == "json":
        try:
            if isinstance(response_content, str):
                json_obj = json.loads(response_content)
            else:
                json_obj = response_content
            potential_json_objects.append(json.dumps(json_obj))
        except Exception as e:
            print(f"Error processing JSON response: {e}")
    
    # Find additional JSON-like objects in the text
    for match in re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text):
        if match not in potential_json_objects:
            potential_json_objects.append(match)

    # Repair and validate JSON objects
    repaired_json_objects = []
    for obj_str in potential_json_objects:
        try:
            repaired = json_repair.repair_json(obj_str, return_objects=True)
            if repaired:
                repaired_json_objects.append(repaired)
        except Exception as e:
            print(f"Error repairing JSON object: {e}")
            continue

    # Calculate score based on keywords found
    score = len(keywords_found)

    return {
        "response_content": response_text,
        "keywords_found": keywords_found,
        "json_objects": repaired_json_objects,
        "score": score
    }

def process_responses(responses, url, base_dir="website"):
    """
    Process multiple API responses and save results
    
    Args:
        responses: List of tuples (response_content, response_type)
        url: Original URL for directory structure
        base_dir: Base directory for saving results
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    
    # Create responses directory
    json_dir = os.path.join(base_dir, domain, "jsons")
    os.makedirs(json_dir, exist_ok=True)
    
    # Process all responses
    results = []
    for response_content, response_type in responses:
        result = find_keywords_and_objects_in_response(response_content, response_type)
        if result:
            results.append(result)
    
    # Sort by score and take top 2
    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:2]
    
    # Save results
    output_path = os.path.join(json_dir, "responses.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(top_results, f, indent=4, ensure_ascii=False)
    
    print(f"Processed {len(responses)} responses, saved top {len(top_results)} to: {output_path}")