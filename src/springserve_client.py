import os

import requests
from dotenv import load_dotenv

load_dotenv()

# Authenticate with SpringServe and return a valid token.
def authenticate():
    # Read SpringServe credentials from .env
    email = os.getenv("SPRINGSERVE_EMAIL")
    password = os.getenv("SPRINGSERVE_PASSWORD")
    base_url = os.getenv("SPRINGSERVE_BASE_URL")

    # Stop if any required setting is missing
    if not email or not password or not base_url:
        raise ValueError("SpringServe credentials are not fully configured")

    # Send login credentials to SpringServe
    response = requests.post(
        f"{base_url}/auth",
        json={
            "email": email,
            "password": password,
        },
        headers={
            "Accept": "application/json"
        },
        timeout=60,
    )

    # Raise an error if SpringServe returns 4xx or 5xx
    response.raise_for_status()

    # Convert the JSON response into a Python dictionary
    data = response.json()

    # Extract the authentication token
    token = data.get("token")

    if not token:
        raise ValueError("SpringServe returned no authentication token")

    return token
    
# Get all segments from SpringServe, returning a list of segment dictionaries.
def get_segments():
    # Get a valid authentication token
    token = authenticate()

    # Read the SpringServe base URL from .env
    base_url = os.getenv("SPRINGSERVE_BASE_URL")

    # Store all segments from all pages
    all_segments = []

    # Start from the first page
    page = 1
    
    # Declare the number of segments per page (50 is the maximum allowed by SpringServe)
    per_page = 50

    while True:
        # Request one page of segments
        response = requests.get(
            f"{base_url}/segments",
            headers={
                "Authorization": token,
                "Accept": "application/json",
            },
            params={
                "page": page,
                "per": per_page,
            },
            timeout=60,
        )

        # Raise an error if SpringServe returns 4xx or 5xx
        response.raise_for_status()

        # Convert the current page response into Python data
        segments = response.json()

        # Add this page's segments to the full list
        all_segments.extend(segments)

        # If this page has fewer than 50 segments,
        # it means we reached the last page
        if len(segments) < per_page:
            break

        # Otherwise, move to the next page
        page += 1

    # Return all segments from all pages
    return all_segments

# Create a new segment in SpringServe, returning the created segment's data as a Python dictionary.
def create_segment(name, description):
    # Get a valid authentication token
    token = authenticate()

    # Read the SpringServe base URL from .env
    base_url = os.getenv("SPRINGSERVE_BASE_URL")

    # Build the segment configuration
    payload = {
        "name": name,
        "description": description,
        "segment_type": "list",
        "segment_list_type": "device_id",
    }

    # Send the request to create the segment
    response = requests.post(
        f"{base_url}/segments",
        headers={
            "Authorization": token,
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
    )

    # Stop if SpringServe returns an HTTP error
    response.raise_for_status()

    # Return the created segment
    return response.json()


# When segments exist, SpringServe requires a description to be provided when creating a new segment. 
# This function replaces the IFAs in an existing segment with the contents of a CSV file.
def replace_segment_ifas(segment_id, file_path):
    # Get a valid authentication token
    token = authenticate()

    # Read the SpringServe base URL from .env
    base_url = os.getenv("SPRINGSERVE_BASE_URL")

    # Open the CSV file in binary mode
    with open(file_path, "rb") as file:

        # Send the CSV file to SpringServe
        response = requests.post(
            f"{base_url}/segments/{segment_id}/items/file_bulk_replace",
            headers={
                "Authorization": token,
                "Accept": "application/json",
            },
            files={
                "csv_file": file
            },
            timeout=300,
        )

    # Stop if SpringServe returns an HTTP error
    response.raise_for_status()

    # Return SpringServe's response
    return response.json()


# This function retrieves a specific segment from SpringServe by its ID, 
# returning the segment's data as a Python dictionary. 
# We will use this function to confirm that the segment's IFAs were successfully replaced.
def get_segment_by_id(segment_id):
    # Get a valid authentication token
    token = authenticate()

    # Read the SpringServe base URL from .env
    base_url = os.getenv("SPRINGSERVE_BASE_URL")

    # Request one specific segment by ID
    response = requests.get(
        f"{base_url}/segments/{segment_id}",
        headers={
            "Authorization": token,
            "Accept": "application/json",
        },
        timeout=60,
    )

    # Stop if SpringServe returns an HTTP error
    response.raise_for_status()

    # Return the segment as Python data
    return response.json()