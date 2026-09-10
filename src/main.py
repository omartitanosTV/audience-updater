import uuid
from pathlib import Path
from snowflake_client import run_query
from springserve_client import authenticate, get_segments

'''
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
invalid_ifas = []

# Validate every unique IFA
for ifa in unique_ifas:
    try:
        uuid.UUID(ifa)
    except (ValueError, TypeError):
        invalid_ifas.append(ifa)


for ifa in unique_ifas[:5]:
    print(ifa)
    
# Create the output file
output_path = Path("sports_titan_os_es.csv")

# Write one IFA per line
with open(output_path, "w") as file:
    for ifa in unique_ifas:
        file.write(ifa + "\n")
        
        
print(f"Audience size: {len(results):,}")
print(f"Unique IFAs: {len(unique_ifas):,}")
print(f"Invalid IFAs: {len(invalid_ifas):,}")
print(f"File created: {output_path}")
'''

# Authenticate with SpringServe and get a valid token
token = authenticate()

# Confirm that authentication worked
print("SpringServe authentication successful")

# Check whether a token was actually returned
# bool(token) will be True if the token is not empty
print(f"Token received: {bool(token)}")


# Get all SpringServe segments
# The get_segments() function should handle pagination internally
segments = get_segments()

# Confirm that the segments request worked
print("Segments request successful")

# Show the Python type returned by the API
# In this case, we expect a list
print(type(segments))

# Show the total number of segments retrieved
print(f"Number of segments: {len(segments)}")

# Only continue if the list is not empty
if segments:

    # Show the first segment so we can inspect its structure
    print("First segment:")

    # Print the first dictionary in the segments list
    print(segments[0])