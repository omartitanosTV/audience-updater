import uuid
from pathlib import Path

from snowflake_client import run_query


# This function runs an audience query from a SQL file
def build_audience_from_query(query_file):
    # Convert the query file path into a Path object
    query_path = Path(query_file)

    # Read the SQL query from the file
    query = query_path.read_text()

    # Build the audience using the SQL query
    return build_audience_from_sql(query)


# This function runs an audience SQL query directly
def build_audience_from_sql(query):
    # Run the query in Snowflake
    results = run_query(query)

    # Validate and prepare the IFAs returned by Snowflake
    return prepare_ifas(results)


# This function removes duplicate IFAs and separates valid and invalid IFAs
def prepare_ifas(results):
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

    # Create lists to store valid and invalid IFAs
    valid_ifas = []
    invalid_ifas = []

    # Validate every unique IFA
    for ifa in unique_ifas:
        try:
            uuid.UUID(ifa)
            valid_ifas.append(ifa)
        except (ValueError, TypeError):
            invalid_ifas.append(ifa)

    # Return the audience data
    return valid_ifas, invalid_ifas, len(results)