import sys
from pathlib import Path


# Allow this learning/test script to be run directly with `python src/main.py`.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from src.springserve_client import authenticate
from src.audience_builder import build_audience_from_query
from src.audience_updater import (
    ensure_segment,
    update_audience,
)

# Define the query file
query_file = "queries/sports_titan_os_es.sql"

# Build the audience from the Snowflake query
valid_ifas, invalid_ifas, total_rows = build_audience_from_query(
    query_file=query_file
)

# Print the audience information
print(f"Audience size: {total_rows:,}")
print(f"Valid IFAs: {len(valid_ifas):,}")
print(f"Invalid IFAs: {len(invalid_ifas):,}")

# Check if there are any valid IFAs
if len(valid_ifas) == 0:
    raise ValueError(
        "Audience has 0 valid IFAs. SpringServe will not be updated."
    )

# Define the output CSV file
output_path = Path("sports_titan_os_es.csv")

# Authenticate with SpringServe and get a valid token
token = authenticate()

# Confirm that authentication worked
print("SpringServe authentication successful")

# Check whether a token was actually returned
# bool(token) will be True if the token is not empty
print(f"Token received: {bool(token)}")

segment = ensure_segment(
    name="Test - Sports - Titan OS (ES)",
    description="Sports audience for Titan OS devices in Spain."
)

print("Segment ready")
print(segment)

# Select the mode for updating the audience
mode = "replace"

# Update the audience using the selected mode
updated_segment = update_audience(
    segment=segment,
    valid_ifas=valid_ifas,
    output_path=output_path,
    mode=mode
)