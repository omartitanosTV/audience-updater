import uuid
from pathlib import Path
from snowflake_client import run_query
from springserve_client import authenticate, replace_segment_ifas
from audience_updater import ensure_segment, wait_for_segment_upload


query_path = Path("queries/sports_titan_os_es.sql")

query = query_path.read_text()

results = run_query(query)

# Create an empty list to store the IFAs
ifas = []

# Go through every row returned by Snowflake
for row in results:

    # Take the first value from the row
    ifa = row[0]

    # Only keep it if it is not None
    if ifa is not None:
        ifas.append(ifa)
        
# Create a set to remove duplicate IFAs
unique_ifas = set(ifas)

# Convert it back to a list
unique_ifas = list(unique_ifas)

# Create a list to store invalid IFAs
valid_ifas = []
invalid_ifas = []


# Validate every unique IFA
for ifa in unique_ifas:
    try:
        uuid.UUID(ifa)
        valid_ifas.append(ifa)
    except (ValueError, TypeError):
        invalid_ifas.append(ifa)


for ifa in valid_ifas[:5]:
    print(ifa)
    
# Create the output file
output_path = Path("sports_titan_os_es.csv")

# Write one IFA per line
with open(output_path, "w") as file:
    for ifa in valid_ifas:
        file.write(ifa + "\n")
        
        
print(f"Audience size: {len(results):,}")
print(f"Valid IFAs: {len(valid_ifas):,}")
print(f"Invalid IFAs: {len(invalid_ifas):,}")
print(f"File created: {output_path}")

# Check if there are any valid IFAs
if len(valid_ifas) == 0:
    raise ValueError(
        "Audience has 0 valid IFAs. SpringServe will not be updated."
    )

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


# Replace the segment IFAs using the generated CSV
replace_response = replace_segment_ifas(
    segment_id=segment["id"],
    file_path=output_path
)

print("Segment IFAs replaced successfully")
print(replace_response)

# Wait until SpringServe finishes processing the uploaded IFAs
updated_segment = wait_for_segment_upload(segment["id"])

print("Upload completed")
print(f"Final segment count: {updated_segment['segment_count']}")