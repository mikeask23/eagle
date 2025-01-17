import json
import os
from urllib.parse import urlparse

def save_api_response(response_body, url, output_dir):
    """Saves an API response to a JSON file.

    Args:
        response_body: The response body content (either JSON or text).
        url: The URL of the API request.
        output_dir: The directory to save the API responses to.
    """
    parsed_url = urlparse(url)

    # Sanitize the URL path for the filename
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in parsed_url.path.strip("/"))
    if not filename or filename == "/":
        filename = "index"
    filename += ".json"  # Use .json extension for API responses

    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        if isinstance(response_body, str):
            # Try to parse as JSON if it's a string
            try:
                json_data = json.loads(response_body)
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                print(f"  Could not parse response as JSON. Saving as raw text.")
                f.write(response_body)
        else:
            json.dump(response_body, f, indent=4, ensure_ascii=False)
    print(f"  API response saved to: {filepath}")