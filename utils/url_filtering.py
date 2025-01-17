import re

def is_product_catalogue_api_url(url):
    """
    Filters URLs to identify potential product catalogue API endpoints (Stage 1).
    """
    core_keywords = [
        "api",
        "search",
        "products",
        "items",
        "product-search",
        "productsearch"
    ]
    supplementary_keywords = [
        "catalogue",
        "catalog",
        "list",
        "browse",
        "query",
        "filter",
        "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10",
        "graphql"
    ]
    pagination_keywords = [
        "page",
        "start",
        "offset",
        "limit",
        "sz",
        "pagesize"
    ]
    sale_keywords = [
        "sale",
        "clearance",
        "deals",
        "discount",
        "outlet"
    ]
    platform_keywords = [
        "cgid",
        "collections",
        "demandware.store",
        "mobify"
    ]
    other_keywords = [
        "category",
        "categories",
        "id",
        "ids",
        "sku",
        "skus",
        "inventory",
        "stock",
        "availability",
        "options",
        "variants",
        "attributes",
        "recommendations",
        "orchestra",
        "getdeals",
        "zgw"
    ]
    all_keywords = core_keywords + supplementary_keywords + pagination_keywords + sale_keywords + platform_keywords + other_keywords
    api_version_pattern = r"v\d+"
    score = 0

    for keyword in core_keywords:
        if keyword.lower() in url.lower():
            score += 3

    for keyword in supplementary_keywords:
        if keyword.lower() in url.lower():
            score += 2

    for keyword in pagination_keywords:
        if keyword.lower() in url.lower():
            score += 1.5

    for keyword in sale_keywords:
        if keyword.lower() in url.lower():
            score += 1.5

    for keyword in platform_keywords:
        if keyword.lower() in url.lower():
            score += 1

    for keyword in other_keywords:
        if keyword.lower() in url.lower():
            score += 0.5

    if re.search(api_version_pattern, url, re.IGNORECASE):
        score += 1.5

    # Combinations
    if ("api" in url.lower() or "search" in url.lower() or "products" in url.lower()) and ("page" in url.lower() or "start" in url.lower() or "offset" in url.lower()):
        score += 3
    if "api" in url.lower() and "search" in url.lower() and "products" in url.lower():
        score += 3
    if "sale" in url.lower() and ("api" in url.lower() or "search" in url.lower() or "products" in url.lower()):
        score += 2

    # Slightly lower threshold for the initial filter
    threshold = 4

    return score >= threshold