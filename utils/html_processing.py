import json
import os
import re
from json_repair import repair_json
from bs4 import BeautifulSoup

def extract_and_repair_json(html_content, output_dir, cc_html_path=None):
    """
    Extracts <script> elements from HTML, finds potential JSON content,
    repairs it using json_repair, scores it, and saves the top 2 to files.
    Processes both normal and curl_cffi HTML if provided.
    """

    def process_html(html, is_cc=False):
        soup = BeautifulSoup(html, 'html.parser')
        script_tags = soup.find_all('script')

        # Keywords for scoring
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
                # Score based on keyword presence
                score = sum(keyword.lower() in script_content.lower() for keyword in all_keywords)

                json_like_pattern = re.compile(r"\{.*\}", re.DOTALL)
                for match in json_like_pattern.findall(script_content):
                    try:
                        repaired = repair_json(match, return_objects=True)
                        if repaired:
                            results.append({
                                "repaired_json": repaired,
                                "score": score
                            })
                    except Exception as e:
                        print(f"  Error repairing JSON: {e}")

        # Sort by score and take top 2
        results.sort(key=lambda x: x["score"], reverse=True)
        top_results = results[:2]

        # Save top results to a single file based on is_cc
        filename = "extracted_data_cc.json" if is_cc else "extracted_data.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(top_results, f, indent=4, ensure_ascii=False)  # Save the list of top results
        print(f"  Top 2 repaired JSON objects {'(CC)' if is_cc else ''} saved to: {filepath}")

    # Process the normal HTML
    process_html(html_content)

    # Process the curl_cffi HTML if provided
    if cc_html_path and os.path.exists(cc_html_path):
        with open(cc_html_path, "r", encoding="utf-8") as f:
            cc_html_content = f.read()
        process_html(cc_html_content, is_cc=True)