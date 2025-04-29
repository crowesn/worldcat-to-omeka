import requests
import json

# 🔹 CONFIGURATION: Set your API keys and endpoints
WORLDCAT_API_KEY = "THE WORLDCAT API KEY!"
OMEKA_API_KEY = "My Omeka Classic API"
OMEKA_URL = "https://archivovenezuela.com/api/items"

# Function to fetch metadata from WorldCat
def fetch_worldcat_data(oclc_number):
    url = f"https://www.worldcat.org/webservices/catalog/content/{oclc_number}?wskey={WORLDCAT_API_KEY}&format=json"
    response = requests.get(url)
   
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error fetching OCLC {oclc_number}: {response.status_code}")
        return None

# Function to convert WorldCat data to Omeka Dublin Core format
def convert_to_omeka_metadata(worldcat_data):
    metadata = {
        "public": True,
        "featured": False,
        "element_texts": [
            {"element": {"name": "Title"}, "text": worldcat_data.get("title", "Unknown Title")},
            {"element": {"name": "Creator"}, "text": worldcat_data.get("author", "Unknown Author")},
            {"element": {"name": "Publisher"}, "text": worldcat_data.get("publisher", "Unknown Publisher")},
            {"element": {"name": "Date"}, "text": worldcat_data.get("publishDate", "Unknown Date")},
            {"element": {"name": "Description"}, "text": worldcat_data.get("summary", "No description available.")},
            {"element": {"name": "Identifier"}, "text": f"OCLC: {worldcat_data.get('oclcNumber', 'N/A')}"}
        ]
    }
    return metadata

# Function to post metadata to Omeka Classic
def post_to_omeka(omeka_data):
    headers = {"Content-Type": "application/json"}
    params = {"key": MY_OMEKA_API_KEY}
    response = requests.post(OMEKA_URL, headers=headers, params=params, data=json.dumps(omeka_data))

    if response.status_code == 201:
        print("✅ Successfully added item to Omeka!")
    else:
        print(f"❌ Error adding item to Omeka: {response.status_code} - {response.text}")

# Batch processing function
def batch_import(oclc_numbers):
    for oclc in oclc_numbers:
        print(f"🔍 Fetching WorldCat data for OCLC: {oclc}")
        worldcat_data = fetch_worldcat_data(oclc)
       
        if worldcat_data:
            print(f"🔄 Converting metadata for OCLC: {oclc}")
            omeka_data = convert_to_omeka_metadata(worldcat_data)
           
            print(f"🚀 Posting item to Omeka for OCLC: {oclc}")
            post_to_omeka(omeka_data)
        else:
            print(f"⚠️ Skipping OCLC: {oclc}, data not found.")

# 🔹 List of OCLC Numbers to Import
oclc_numbers_list = ["1234567", "7654321", "11223344"]  # Replace with actual OCLC numbers

# Run the batch import
batch_import(oclc_numbers_list)
