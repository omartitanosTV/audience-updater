import os
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv


# Load variables from the .env file
load_dotenv()


def load_private_key():
    # Read the private key path from .env
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

    # Stop with a clear error if the variable is missing
    if not key_path:
        raise ValueError("SNOWFLAKE_PRIVATE_KEY_PATH is not configured")

    # Convert the path into a Path object
    path = Path(key_path).expanduser()

    # Check that the private key file exists
    if not path.is_file():
        raise FileNotFoundError(
            f"Private key not found: {path}"
        )

    # Read the private key passphrase, if one exists
    passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")

    # Open and load the private key
    with open(path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase.encode() if passphrase else None,
        )

    # Convert the key into the format required by Snowflake
    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_connection():
    # Open a connection to Snowflake
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),

        # Use the private key for authentication
        private_key=load_private_key(),
    )


def run_query(query):
    # Open the connection
    connection = get_connection()

    try:
        # Create a cursor to send queries to Snowflake
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query)

        # Return all result rows
        return cursor.fetchall()

    finally:
        # Close the connection even if an error occurs
        connection.close()