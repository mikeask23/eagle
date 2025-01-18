# html_processing.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json_repair
import json
import os

def find_keywords_and_objects_in_scripts(html_content, output_path, source_type="browser"):
    """
    Processes HTML content to find script elements, keywords, and JSON objects.
    
    Args:
        html_content: The HTML content as string
        output_path: Path to save the JSON
        source_type: Either "browser" or "cc" to identify the source
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tags = soup.find_all('script')

    # Keywords for identifying important data
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

    results = []
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content:
            keywords_found = [
                keyword
                for keyword in all_keywords
                if keyword.lower() in script_content.lower()
            ]

            # Find outermost {} objects
            potential_json_objects = []
            for match in re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", script_content):
                potential_json_objects.append(match)

            repaired_json_objects = []
            for obj_str in potential_json_objects:
                try:
                    repaired = json_repair.repair_json(obj_str, return_objects=True)
                    repaired_json_objects.append(repaired)
                except Exception as e:
                    print(f"Error repairing JSON: {e}")
                    continue

            if keywords_found or repaired_json_objects:
                results.append({
                    "script_content": script_content,
                    "keywords_found": keywords_found,
                    "json_objects": repaired_json_objects
                })

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(results, outfile, indent=4, ensure_ascii=False)

def process_html_files(url, base_dir="websites"):
    """
    Process both HTML files (browser and cc) for a given URL
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    
    # Create jsons directory
    website_dir = os.path.join(base_dir, domain)
    json_dir = os.path.join(website_dir, "jsons")
    html_dir = os.path.join(website_dir, "htmls")
    
    # Process browser HTML
    browser_html_path = os.path.join(html_dir, "browser.html")
    if os.path.exists(browser_html_path):
        with open(browser_html_path, "r", encoding="utf-8") as f:
            browser_html = f.read()
        browser_json_path = os.path.join(json_dir, "browser.json")
        os.makedirs(json_dir, exist_ok=True)
        find_keywords_and_objects_in_scripts(browser_html, browser_json_path, "browser")
        print(f"Processed browser HTML to: {browser_json_path}")
    
    # Process curl_cffi HTML
    cc_html_path = os.path.join(html_dir, "cc.html")
    if os.path.exists(cc_html_path):
        with open(cc_html_path, "r", encoding="utf-8") as f:
            cc_html = f.read()
        cc_json_path = os.path.join(json_dir, "cc.json")
        os.makedirs(json_dir, exist_ok=True)
        find_keywords_and_objects_in_scripts(cc_html, cc_json_path, "cc")
        print(f"Processed curl_cffi HTML to: {cc_json_path}")