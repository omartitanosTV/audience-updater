import os

import requests
from dotenv import load_dotenv

load_dotenv()

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
        if len(segments) < 50:
            break

        # Otherwise, move to the next page
        page += 1

    # Return all segments from all pages
    return all_segments