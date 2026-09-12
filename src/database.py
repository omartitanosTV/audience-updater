import sqlite3
from pathlib import Path


# Define the path to the SQLite database
DATABASE_PATH = Path("data/audiences.db")


# This function opens a connection to the SQLite database
def get_database_connection():
    # Make sure the data directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Open the database connection
    connection = sqlite3.connect(DATABASE_PATH)

    # Return rows as dictionary-like objects
    connection.row_factory = sqlite3.Row

    # Enable foreign key support in SQLite
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# This function creates the database tables if they do not already exist
def create_tables():
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        # ---------------------------------------------------------------------
        # AUDIENCES
        # Stores the current configuration of each audience
        # ---------------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                query TEXT NOT NULL,
                mode TEXT NOT NULL,
                refresh_frequency TEXT NOT NULL,
                status TEXT,
                last_update TEXT,
                last_count INTEGER,
                enabled INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        # ---------------------------------------------------------------------
        # AUDIENCE RUNS
        # Stores the history of every audience execution
        # ---------------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audience_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audience_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                total_rows INTEGER,
                valid_ifas INTEGER,
                invalid_ifas INTEGER,
                segment_count INTEGER,
                duration_seconds REAL,
                error_message TEXT,
                FOREIGN KEY (audience_id)
                    REFERENCES audiences(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


# This function adds a new audience to the database
def add_audience_to_db(
    name,
    description,
    query,
    mode,
    refresh_frequency,
    enabled=True,
):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO audiences (
                name,
                description,
                query,
                mode,
                refresh_frequency,
                enabled
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                query,
                mode,
                refresh_frequency,
                int(enabled),
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# This function retrieves all audiences from the database
def get_audiences_from_db():
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM audiences
            ORDER BY id
            """
        )

        audiences = cursor.fetchall()

        return audiences

    finally:
        connection.close()


# This function retrieves one audience from the database by its ID
def get_audience_from_db(audience_id):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM audiences
            WHERE id = ?
            """,
            (audience_id,),
        )

        audience = cursor.fetchone()

        return audience

    finally:
        connection.close()


# This function updates the configuration of an existing audience
def update_audience_in_db(
    audience_id,
    name,
    description,
    query,
    mode,
    refresh_frequency,
    enabled,
):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE audiences
            SET
                name = ?,
                description = ?,
                query = ?,
                mode = ?,
                refresh_frequency = ?,
                enabled = ?
            WHERE id = ?
            """,
            (
                name,
                description,
                query,
                mode,
                refresh_frequency,
                int(enabled),
                audience_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


# This function deletes an audience from the database by its ID
def delete_audience_from_db(audience_id):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM audiences
            WHERE id = ?
            """,
            (audience_id,),
        )

        connection.commit()

    finally:
        connection.close()


# This function updates the latest status information of an audience
def update_audience_status_in_db(
    audience_id,
    status,
    last_update,
    last_count,
):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE audiences
            SET
                status = ?,
                last_update = ?,
                last_count = ?
            WHERE id = ?
            """,
            (
                status,
                last_update,
                last_count,
                audience_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


# This function updates the latest execution result of an audience
#
# We keep this function because audience_service.py is already using it.
def save_audience_run_result_to_db(
    audience_id,
    status,
    last_update,
    last_count,
):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE audiences
            SET
                status = ?,
                last_update = ?,
                last_count = ?
            WHERE id = ?
            """,
            (
                status,
                last_update,
                last_count,
                audience_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


# -------------------------------------------------------------------------
# EXECUTION HISTORY
# -------------------------------------------------------------------------


# This function creates a new historical execution record
def add_audience_run_to_db(
    audience_id,
    started_at,
    finished_at,
    status,
    total_rows=None,
    valid_ifas=None,
    invalid_ifas=None,
    segment_count=None,
    duration_seconds=None,
    error_message=None,
):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO audience_runs (
                audience_id,
                started_at,
                finished_at,
                status,
                total_rows,
                valid_ifas,
                invalid_ifas,
                segment_count,
                duration_seconds,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audience_id,
                started_at,
                finished_at,
                status,
                total_rows,
                valid_ifas,
                invalid_ifas,
                segment_count,
                duration_seconds,
                error_message,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# This function retrieves the execution history for one audience
def get_audience_runs_from_db(audience_id):
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM audience_runs
            WHERE audience_id = ?
            ORDER BY started_at DESC
            """,
            (audience_id,),
        )

        runs = cursor.fetchall()

        return runs

    finally:
        connection.close()


# This function retrieves all execution history
def get_all_audience_runs_from_db():
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                audience_runs.*,
                audiences.name AS audience_name
            FROM audience_runs
            INNER JOIN audiences
                ON audiences.id = audience_runs.audience_id
            ORDER BY audience_runs.started_at DESC
            """
        )

        runs = cursor.fetchall()

        return runs

    finally:
        connection.close()