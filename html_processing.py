import os
import aiofiles
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import json_repair
import json
from collections import defaultdict
from curl_cffi import requests

def ensure_directory(path):
    """Ensures the directory exists, creates it if it doesn't."""
    if not os.path.exists(path):
        os.makedirs(path)

async def save_html(page, url, base_dir="websites"):
    """Saves the browser-rendered HTML content of the current page."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    html_dir = os.path.join(base_dir, domain, "htmls")
    ensure_directory(html_dir)
    filepath = os.path.join(html_dir, "browser.html")
    html_content = await page.content()
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(html_content)
    print(f"  Browser HTML saved to: {filepath}")
    return filepath

async def save_html_cc(content, url, base_dir="websites"):
    """Saves the curl_cffi HTML content."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    html_dir = os.path.join(base_dir, domain, "htmls")
    ensure_directory(html_dir)
    filepath = os.path.join(html_dir, "cc.html")
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(content)
    print(f"  Curl_cffi HTML saved to: {filepath}")
    return filepath

async def make_curl_cffi_request(url):
    """Makes a request using curl_cffi with browser impersonation."""
    print(f"Making curl_cffi request to: {url}")
    try:
        # Make request with just impersonation
        response = requests.get(url, impersonate="chrome120")
        
        # Get text directly without awaiting
        text = response.text
        
        if not text:
            print("  Warning: Empty response text received")
            return None
            
        return text
        
    except Exception as e:
        print(f"  Error making curl_cffi request to {url}: {e}")
        return None

def find_keywords_and_objects_in_scripts(html_content, output_path, source_type="browser"):
    """
    Processes HTML content to find script elements, keywords, and JSON objects.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tags = soup.find_all('script')

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

    results_by_keywords = defaultdict(list)
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content:
            keywords_found = [
                keyword for keyword in all_keywords if keyword.lower() in script_content.lower()
            ]

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
                result = {
                    "script_content": script_content,
                    "keywords_found": keywords_found,
                    "json_objects": repaired_json_objects
                }
                results_by_keywords[len(keywords_found)].append(result)

    keyword_counts = sorted(results_by_keywords.keys(), reverse=True)
    top_two_counts = keyword_counts[:2] if len(keyword_counts) >= 2 else keyword_counts

    filtered_results = []
    for count in top_two_counts:
        filtered_results.extend(results_by_keywords[count])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(filtered_results, outfile, indent=4, ensure_ascii=False)

def process_html_files(url, base_dir="websites"):
    """
    Process both HTML files (browser and cc) for a given URL
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_")
    website_dir = os.path.join(base_dir, domain)
    json_dir = os.path.join(website_dir, "jsons")
    html_dir = os.path.join(website_dir, "htmls")

    browser_html_path = os.path.join(html_dir, "browser.html")
    if os.path.exists(browser_html_path):
        with open(browser_html_path, "r", encoding="utf-8") as f:
            browser_html = f.read()
        browser_json_path = os.path.join(json_dir, "browser.json")
        os.makedirs(json_dir, exist_ok=True)
        find_keywords_and_objects_in_scripts(browser_html, browser_json_path, "browser")
        print(f"Processed browser HTML to: {browser_json_path}")

    cc_html_path = os.path.join(html_dir, "cc.html")
    if os.path.exists(cc_html_path):
        with open(cc_html_path, "r", encoding="utf-8") as f:
            cc_html = f.read()
        cc_json_path = os.path.join(json_dir, "cc.json")
        os.makedirs(json_dir, exist_ok=True)
        find_keywords_and_objects_in_scripts(cc_html, cc_json_path, "cc")
        print(f"Processed curl_cffi HTML to: {cc_json_path}")