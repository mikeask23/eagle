import json

def is_product_data_response(response_content, response_type="json"):
    """
    Analyzes the response body to confirm if it contains product data (Stage 2).
    """
    try:
        if response_type == "json":
            data = json.loads(response_content)
        elif response_type == "text":  # Handle as text
            data = response_content
        else:
            return False  # Unsupported response type

        # --- Keywords/Patterns to look for in the response ---

        # Most Important Indicators:
        product_identifiers = [
            "id",  # Common product identifier
            "sku",  # Stock Keeping Unit
            "upc",  # Universal Product Code
            "ean",  # International Article Number
            "gtin",  # Global Trade Item Number
            "mpn",  # Manufacturer Part Number
            "asin",  # Amazon Standard Identification Number (for Amazon APIs)
            "product_id",
            "item_id",
            "productId",
            "itemId"
        ]

        pricing_keywords = [
            "price",
            "sale_price",
            "original_price",
            "list_price",
            "msrp",
            "discount",
            "currency"
        ]

        product_attributes = [
            "name",
            "title",
            "description",
            "short_description",
            "brand",
            "category",
            "image",
            "url",
            "color",
            "size",
            "dimensions",
            "weight"
        ]

        # --- Scoring for Response Body Analysis ---
        score = 0

        # Check for product identifiers (High Weight)
        if isinstance(data, dict):
            for identifier in product_identifiers:
                if identifier.lower() in str(data).lower():
                    score += 3
        elif isinstance(data, str):
            for identifier in product_identifiers:
                if identifier.lower() in data.lower():
                    score += 3

        # Check for pricing keywords (High Weight)
        if isinstance(data, dict):
            for keyword in pricing_keywords:
                if keyword.lower() in str(data).lower():
                    score += 2
        elif isinstance(data, str):
            for keyword in pricing_keywords:
                if keyword.lower() in data.lower():
                    score += 2

        # Check for product attributes (Medium Weight)
        if isinstance(data, dict):
            for attribute in product_attributes:
                if attribute.lower() in str(data).lower():
                    score += 1
        elif isinstance(data, str):
            for attribute in product_attributes:
                if attribute.lower() in data.lower():
                    score += 1

        # --- Check for nested structures that often indicate lists of products ---
        # (Adapt these to common patterns you observe in API responses)
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    # If a list contains dictionaries, it could be a list of products
                    score += 1.5
                    if any(identifier.lower() in str(value[0]).lower() for identifier in product_identifiers):
                        score += 2
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            score += 1.5
            if any(identifier.lower() in str(data[0]).lower() for identifier in product_identifiers):
                score += 2

        # --- Threshold for Positive Identification ---
        threshold = 4  # Adjust based on testing

        return score >= threshold

    except (json.JSONDecodeError, TypeError, ValueError):
        # Handle cases where the response is not valid JSON or XML
        return False
    except Exception as e:
        print(f"Error during response body analysis: {e}")
        return False