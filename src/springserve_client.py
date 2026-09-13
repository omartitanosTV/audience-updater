import os

import requests
from dotenv import load_dotenv


load_dotenv()

# Reuse one HTTP session across SpringServe requests
SESSION = requests.Session()


class SpringServeAPIError(RuntimeError):
    """Raised when SpringServe returns an unexpected or failed response."""


# Read the SpringServe base URL and stop early if it is missing
def _get_base_url():
    base_url = os.getenv("SPRINGSERVE_BASE_URL")

    if not base_url:
        raise ValueError("SPRINGSERVE_BASE_URL is not configured")

    return base_url.rstrip("/")


# Raise a more useful error than requests' default HTTP message
def _raise_for_status(response, label):
    if response.ok:
        return

    response_body = response.text[:2000]
    message = f"{label}: HTTP {response.status_code}"

    if response_body:
        message += f" — {response_body}"

    raise SpringServeAPIError(message)


# Convert a SpringServe response to JSON with a clear error if it is not JSON
def _response_json(response):
    try:
        return response.json()
    except ValueError as error:
        raise SpringServeAPIError(
            "SpringServe returned a non-JSON response."
        ) from error


# Authenticate with SpringServe and return a valid token
def authenticate():
    # Read SpringServe credentials from .env
    email = os.getenv("SPRINGSERVE_EMAIL")
    password = os.getenv("SPRINGSERVE_PASSWORD")

    # Stop if any required setting is missing
    if not email or not password:
        raise ValueError(
            "SpringServe credentials are not fully configured"
        )

    # Send login credentials to SpringServe
    response = SESSION.post(
        f"{_get_base_url()}/auth",
        json={
            "email": email,
            "password": password,
        },
        headers={
            "Accept": "application/json"
        },
        timeout=60,
    )

    _raise_for_status(response, "SpringServe authentication failed")

    # Extract the authentication token
    data = _response_json(response)
    token = data.get("token") if isinstance(data, dict) else None

    if not token:
        raise SpringServeAPIError(
            "SpringServe returned no authentication token"
        )

    return str(token)


# Send an authenticated request and retry authentication once after HTTP 401
def _request(method, endpoint, *, params=None, json=None, timeout=60):
    token = authenticate()

    for attempt in range(2):
        response = SESSION.request(
            method,
            f"{_get_base_url()}/{endpoint.lstrip('/')}",
            headers={
                "Authorization": token,
                "Accept": "application/json",
            },
            params=params,
            json=json,
            timeout=timeout,
        )

        if response.status_code == 401 and attempt == 0:
            token = authenticate()
            continue

        _raise_for_status(
            response,
            f"SpringServe {method.upper()} {endpoint} failed",
        )
        return response

    raise SpringServeAPIError("SpringServe authentication retry failed")


# Extract a list from the response shapes SpringServe commonly returns
def _extract_collection(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("segments", "objects", "results", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

    raise SpringServeAPIError(
        "SpringServe returned an unexpected collection response."
    )


# Get all segments from SpringServe
def get_segments():
    all_segments = []
    seen_ids = set()
    page = 1
    per_page = 50

    while True:
        response = _request(
            "GET",
            "/segments",
            params={
                "page": page,
                "per": per_page,
            },
            timeout=60,
        )

        segments = _extract_collection(_response_json(response))

        if not segments:
            break

        added_this_page = 0

        for segment in segments:
            segment_id = str(segment.get("id"))

            if segment_id in seen_ids:
                continue

            seen_ids.add(segment_id)
            all_segments.append(segment)
            added_this_page += 1

        # A short page, or a page with no new IDs, means pagination is done
        if len(segments) < per_page or added_this_page == 0:
            break

        page += 1

        # Defensive guard against an API pagination loop
        if page > 1000:
            raise SpringServeAPIError(
                "SpringServe pagination did not terminate."
            )

    return all_segments


# Create a new device-ID segment in SpringServe
def create_segment(name, description):
    response = _request(
        "POST",
        "/segments",
        json={
            "name": name,
            "description": description or "",
            "active": True,
            "segment_type": "list",
            "segment_list_type": "device_id",
        },
        timeout=60,
    )

    data = _response_json(response)

    if not isinstance(data, dict) or not data.get("id"):
        raise SpringServeAPIError(
            "SpringServe created the segment but returned no segment ID."
        )

    return data


# Upload a CSV to a SpringServe segment using replace or append
def _upload_segment_file(segment_id, file_path, action):
    token = authenticate()

    for attempt in range(2):
        with open(file_path, "rb") as file:
            response = SESSION.post(
                f"{_get_base_url()}/segments/{segment_id}/items/{action}",
                headers={
                    "Authorization": token,
                    "Accept": "application/json",
                },
                files={
                    "csv_file": file
                },
                timeout=900,
            )

        if response.status_code == 401 and attempt == 0:
            token = authenticate()
            continue

        _raise_for_status(
            response,
            f"SpringServe segment upload ({action}) failed",
        )
        return _response_json(response)

    raise SpringServeAPIError("SpringServe upload authentication retry failed")


# Replace the IFAs in an existing segment with the contents of a CSV file
def replace_segment_ifas(segment_id, file_path):
    return _upload_segment_file(
        segment_id=segment_id,
        file_path=file_path,
        action="file_bulk_replace",
    )


# Retrieve one specific segment by ID
def get_segment_by_id(segment_id):
    response = _request(
        "GET",
        f"/segments/{segment_id}",
        timeout=60,
    )

    data = _response_json(response)

    if not isinstance(data, dict):
        raise SpringServeAPIError(
            "SpringServe returned an invalid segment response."
        )

    return data


# Retrieve all IFAs from one SpringServe segment
def get_segment_ifas(segment_id):
    # Important: this endpoint has previously returned an empty list when
    # pagination parameters were supplied, so the request intentionally has
    # no page/per parameters.
    response = _request(
        "GET",
        f"/segments/{segment_id}/items",
        timeout=900,
    )

    items = _extract_collection(_response_json(response))
    all_ifas = []

    for item in items:
        value = item.get("item") if isinstance(item, dict) else None

        if value:
            all_ifas.append(value)

    return all_ifas


# Append new IFAs to an existing segment from a CSV file
def append_segment_ifas(segment_id, file_path):
    return _upload_segment_file(
        segment_id=segment_id,
        file_path=file_path,
        action="file_bulk_create",
    )
