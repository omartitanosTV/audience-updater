import sqlite3
from pathlib import Path


# Resolve the database from the project root so the app works regardless
# of the current terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "audiences.db"


# Open a connection to the SQLite database
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


# Return the existing columns for one SQLite table
def _get_table_columns(connection, table_name):
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {row["name"] for row in rows}


# Add one column only when an older database does not have it yet
def _ensure_column(connection, table_name, column_name, definition):
    columns = _get_table_columns(connection, table_name)

    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {definition}"
        )


# Create the database tables and upgrade older local databases in place
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
                enabled INTEGER NOT NULL DEFAULT 1,
                schedule_day INTEGER,
                schedule_time TEXT NOT NULL DEFAULT '22:00',
                schedule_timezone TEXT NOT NULL DEFAULT 'Europe/Madrid',
                once_at TEXT,
                next_refresh_at TEXT,
                last_scheduled_at TEXT
            )
            """
        )

        # Upgrade an existing audiences table without deleting user data.
        # These ALTERs are intentionally additive so the current database can
        # be reused when this version is copied over the existing repository.
        _ensure_column(
            connection,
            "audiences",
            "schedule_day",
            "INTEGER",
        )
        _ensure_column(
            connection,
            "audiences",
            "schedule_time",
            "TEXT NOT NULL DEFAULT '22:00'",
        )
        _ensure_column(
            connection,
            "audiences",
            "schedule_timezone",
            "TEXT NOT NULL DEFAULT 'Europe/Madrid'",
        )
        _ensure_column(
            connection,
            "audiences",
            "once_at",
            "TEXT",
        )
        _ensure_column(
            connection,
            "audiences",
            "next_refresh_at",
            "TEXT",
        )
        _ensure_column(
            connection,
            "audiences",
            "last_scheduled_at",
            "TEXT",
        )

        # Apply the requested defaults to audiences that already existed.
        cursor.execute(
            """
            UPDATE audiences
            SET schedule_day = 0
            WHERE LOWER(refresh_frequency) = 'weekly'
              AND schedule_day IS NULL
            """
        )
        cursor.execute(
            """
            UPDATE audiences
            SET schedule_day = 1
            WHERE LOWER(refresh_frequency) = 'monthly'
              AND schedule_day IS NULL
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
                trigger_source TEXT NOT NULL DEFAULT 'manual',
                FOREIGN KEY (audience_id)
                    REFERENCES audiences(id)
                    ON DELETE CASCADE
            )
            """
        )

        # Keep older history rows and add only the new trigger source column.
        _ensure_column(
            connection,
            "audience_runs",
            "trigger_source",
            "TEXT NOT NULL DEFAULT 'manual'",
        )

        connection.commit()

    finally:
        connection.close()


# Add a new audience to the database
def add_audience_to_db(
    name,
    description,
    query,
    mode,
    refresh_frequency,
    enabled=True,
    schedule_day=None,
    schedule_time="22:00",
    schedule_timezone="Europe/Madrid",
    once_at=None,
    next_refresh_at=None,
):
    create_tables()
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
                enabled,
                schedule_day,
                schedule_time,
                schedule_timezone,
                once_at,
                next_refresh_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                query,
                mode,
                refresh_frequency,
                int(enabled),
                schedule_day,
                schedule_time,
                schedule_timezone,
                once_at,
                next_refresh_at,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# Retrieve all audiences from the database
def get_audiences_from_db():
    create_tables()
    connection = get_database_connection()

    try:
        return connection.execute(
            """
            SELECT *
            FROM audiences
            ORDER BY id
            """
        ).fetchall()

    finally:
        connection.close()


# Retrieve one audience from the database by its ID
def get_audience_from_db(audience_id):
    create_tables()
    connection = get_database_connection()

    try:
        return connection.execute(
            """
            SELECT *
            FROM audiences
            WHERE id = ?
            """,
            (audience_id,),
        ).fetchone()

    finally:
        connection.close()


# Update the configuration of an existing audience
def update_audience_in_db(
    audience_id,
    name,
    description,
    query,
    mode,
    refresh_frequency,
    enabled,
    schedule_day=None,
    schedule_time="22:00",
    schedule_timezone="Europe/Madrid",
    once_at=None,
    next_refresh_at=None,
):
    create_tables()
    connection = get_database_connection()

    try:
        connection.execute(
            """
            UPDATE audiences
            SET
                name = ?,
                description = ?,
                query = ?,
                mode = ?,
                refresh_frequency = ?,
                enabled = ?,
                schedule_day = ?,
                schedule_time = ?,
                schedule_timezone = ?,
                once_at = ?,
                next_refresh_at = ?
            WHERE id = ?
            """,
            (
                name,
                description,
                query,
                mode,
                refresh_frequency,
                int(enabled),
                schedule_day,
                schedule_time,
                schedule_timezone,
                once_at,
                next_refresh_at,
                audience_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


# Delete an audience from the database by its ID
def delete_audience_from_db(audience_id):
    create_tables()
    connection = get_database_connection()

    try:
        connection.execute(
            """
            DELETE FROM audiences
            WHERE id = ?
            """,
            (audience_id,),
        )
        connection.commit()

    finally:
        connection.close()


# Enable or disable an audience without changing the rest of its settings
def set_audience_enabled_in_db(audience_id, enabled):
    create_tables()
    connection = get_database_connection()

    try:
        connection.execute(
            """
            UPDATE audiences
            SET enabled = ?
            WHERE id = ?
            """,
            (int(enabled), audience_id),
        )
        connection.commit()

    finally:
        connection.close()


# Update only the calculated next automatic refresh
def set_audience_next_refresh_in_db(
    audience_id,
    next_refresh_at,
    last_scheduled_at=None,
):
    create_tables()
    connection = get_database_connection()

    try:
        connection.execute(
            """
            UPDATE audiences
            SET
                next_refresh_at = ?,
                last_scheduled_at = COALESCE(?, last_scheduled_at)
            WHERE id = ?
            """,
            (
                next_refresh_at,
                last_scheduled_at,
                audience_id,
            ),
        )
        connection.commit()

    finally:
        connection.close()


# Retrieve audiences whose automatic schedule is due now
def get_due_audiences_from_db(now_utc_iso):
    create_tables()
    connection = get_database_connection()

    try:
        return connection.execute(
            """
            SELECT *
            FROM audiences
            WHERE enabled = 1
              AND LOWER(refresh_frequency) != 'manual'
              AND next_refresh_at IS NOT NULL
              AND next_refresh_at <= ?
            ORDER BY next_refresh_at, id
            """,
            (now_utc_iso,),
        ).fetchall()

    finally:
        connection.close()


# Update the latest status information of an audience
def update_audience_status_in_db(
    audience_id,
    status,
    last_update,
    last_count,
):
    create_tables()
    connection = get_database_connection()

    try:
        connection.execute(
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


# Keep the original function name because audience_service.py already uses it
def save_audience_run_result_to_db(
    audience_id,
    status,
    last_update,
    last_count,
):
    update_audience_status_in_db(
        audience_id=audience_id,
        status=status,
        last_update=last_update,
        last_count=last_count,
    )


# Create a new historical execution record
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
    trigger_source="manual",
):
    create_tables()
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
                error_message,
                trigger_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                trigger_source,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# Retrieve the execution history for one audience
def get_audience_runs_from_db(audience_id):
    create_tables()
    connection = get_database_connection()

    try:
        return connection.execute(
            """
            SELECT *
            FROM audience_runs
            WHERE audience_id = ?
            ORDER BY started_at DESC
            """,
            (audience_id,),
        ).fetchall()

    finally:
        connection.close()


# Retrieve all execution history with the audience name included
def get_all_audience_runs_from_db(limit=None):
    create_tables()
    connection = get_database_connection()

    try:
        query = """
            SELECT
                audience_runs.*,
                audiences.name AS audience_name
            FROM audience_runs
            INNER JOIN audiences
                ON audiences.id = audience_runs.audience_id
            ORDER BY audience_runs.started_at DESC
        """
        parameters = ()

        if limit is not None:
            query += " LIMIT ?"
            parameters = (int(limit),)

        return connection.execute(query, parameters).fetchall()

    finally:
        connection.close()
