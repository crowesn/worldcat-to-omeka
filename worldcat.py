import requests
import json
import time

# CREDENTIALS
WORLDCAT_API_KEY = "my_oclc_api_key"
OMEKA_API_KEY = "my_omeka_api_key"
OMEKA_URL = "https://archivovenezuela.con/api/items"
LIST_IDS = ["1234567", "7654321"]  # Add multiple WorldCat list IDs
BATCH_SIZE = 50  # Number of records to fetch per request
OMEKA_COLLECTION_ID = 2  # Set to your desired Omeka collection ID (or None)

MAX_RETRIES = 3  # Number of times to retry failed requests
LOG_FILE = "import_log.txt"  # Log file for errors

def log_error(message):
    """Log errors to a file."""
    with open(LOG_FILE, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def request_with_retries(url, headers=None, params=None, method="GET", data=None, files=None):
    """Handle retries for API requests."""
    for attempt in range(MAX_RETRIES):
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, json=data, files=files, timeout=10)

            if response.status_code in [200, 201]:
                return response
            else:
                log_error(f"API Error ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            log_error(f"Request failed (Attempt {attempt + 1}): {e}")
        time.sleep(2)  # Wait before retrying
    return None  # Return None after max retries

def check_omeka_duplicate(title):
    """Check if an item with the same title already exists in Omeka."""
    params = {"key": OMEKA_API_KEY, "search": title}
    response = request_with_retries(OMEKA_URL, params=params)

    if response and response.status_code == 200:
        items = response.json()
        return len(items) > 0  # Return True if an item with the same title exists
    return False

def get_worldcat_list(list_id):
    """Fetch items from a WorldCat list and handle pagination."""
    book_list = []
    start_index = 1

    while True:
        url = f"https://www.worldcat.org/webservices/catalog/content/lists/{list_id}?wskey={WORLDCAT_API_KEY}&start={start_index}&count={BATCH_SIZE}"
        response = request_with_retries(url)

        if not response or response.status_code != 200:
            print(f"Skipping WorldCat List {list_id} due to errors.")
            break

        data = response.json()
        items = data.get("entries", [])

        if not items:
            break  # No more items to process

        for item in items:
            metadata = {
                "title": item.get("title", "Unknown Title"),
                "creator": ", ".join(item.get("authors", ["Unknown Author"])),
                "publisher": item.get("publisher", "Unknown Publisher"),
                "date": item.get("date", "Unknown Date"),
                "language": item.get("language", "Unknown Language"),
                "description": item.get("summary", "No description available"),
                "subject": ", ".join(item.get("subjects", ["No Subject"])),
                "type": item.get("format", "Unknown Type"),
                "format": item.get("physicalFormat", "Unknown Format"),
                "relation": item.get("relatedItems", "No Relation"),
                "source": f"OCLC {item.get('oclcNumber', 'No Source')}",
                "contributor": ", ".join(item.get("contributors", ["No Contributor"])),
                "rights": item.get("rights", "No Rights Information"),
                "alternative_title": item.get("alternativeTitle", "No Alternative Title"),
                "cover_image": item.get("coverImage", None)  # Store cover image URL if available
            }
            book_list.append(metadata)

        start_index += BATCH_SIZE  # Move to the next batch
        time.sleep(1)  # Prevent API rate limits

    return book_list

def upload_to_omeka(metadata):
    """Upload a book record to Omeka Classic, including file attachments."""
    if check_omeka_duplicate(metadata["title"]):
        print(f"Skipping duplicate: {metadata['title']}")
        return

    item_data = {
        "public": True,
        "collection": OMEKA_COLLECTION_ID,  # Assign to specific Omeka collection
        "element_texts": [
            {"element": {"name": "Title"}, "text": metadata["title"]},
            {"element": {"name": "Creator"}, "text": metadata["creator"]},
            {"element": {"name": "Publisher"}, "text": metadata["publisher"]},
            {"element": {"name": "Date"}, "text": metadata["date"]},
            {"element": {"name": "Language"}, "text": metadata["language"]},
            {"element": {"name": "Description"}, "text": metadata["description"]},
            {"element": {"name": "Subject"}, "text": metadata["subject"]},
            {"element": {"name": "Type"}, "text": metadata["type"]},
            {"element": {"name": "Format"}, "text": metadata["format"]},
            {"element": {"name": "Relation"}, "text": metadata["relation"]},
            {"element": {"name": "Source"}, "text": metadata["source"]},
            {"element": {"name": "Contributor"}, "text": metadata["contributor"]},
            {"element": {"name": "Rights"}, "text": metadata["rights"]},
            {"element": {"name": "Alternative Title"}, "text": metadata["alternative_title"]},
        ],
    }

    response = request_with_retries(OMEKA_URL, method="POST", data=item_data, params={"key": OMEKA_API_KEY})

    if response and response.status_code == 201:
        item_id = response.json()["id"]
        print(f"Uploaded: {metadata['title']} (Omeka ID: {item_id})")

        # Upload cover image if available
        if metadata["cover_image"]:
            upload_cover_image_to_omeka(item_id, metadata["cover_image"])
    else:
        print(f"Failed to upload {metadata['title']}")

def upload_cover_image_to_omeka(item_id, image_url):
    """Upload a cover image to an existing Omeka item."""
    image_response = requests.get(image_url, stream=True)

    if image_response.status_code == 200:
        files = {"file": (image_url.split("/")[-1], image_response.raw, "image/jpeg")}
        response = request_with_retries(f"{OMEKA_URL}/{item_id}/files", method="POST", files=files, params={"key": OMEKA_API_KEY})

        if response and response.status_code == 201:
            print(f"Cover image uploaded for item {item_id}")
        else:
            print(f"Failed to upload cover image for item {item_id}")
    else:
        print(f"Could not retrieve cover image from {image_url}")

def main():
    """Process multiple WorldCat lists and upload items to Omeka."""
    for list_id in LIST_IDS:
        print(f"Processing WorldCat List: {list_id}")
        books = get_worldcat_list(list_id)

        if books:
            for book in books:
                upload_to_omeka(book)

        print(f"Finished processing List {list_id}\n")

if __name__ == "__main__":
    main()
