import time
from datetime import datetime, timezone
from pathlib import Path

from src.audience_builder import build_audience_from_sql
from src.audience_updater import ensure_segment, update_audience
from src.database import (
    add_audience_run_to_db,
    get_audience_from_db,
    save_audience_run_result_to_db,
)


# Return a consistent UTC timestamp for status and history records
def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Run one audience using the configuration stored in the database
def run_audience_from_db(audience_id, trigger_source="manual"):
    # Get the audience configuration from the database
    audience = get_audience_from_db(audience_id)

    # Stop if the audience does not exist
    if audience is None:
        raise ValueError(
            f"Audience with ID {audience_id} was not found in the database."
        )

    # Stop if the audience is disabled
    if audience["enabled"] == 0:
        raise ValueError(
            f"Audience with ID {audience_id} is disabled."
        )

    # Read the audience configuration
    name = audience["name"]
    description = audience["description"]
    query = audience["query"]
    mode = audience["mode"]

    # Store the previous successful count so a failed run does not erase it
    previous_count = audience["last_count"]

    # Define the generated CSV path for this audience
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / "data" / f"audience_{audience_id}.csv"

    # Record when the execution started
    started_at = _utc_timestamp()

    # Start a timer to measure execution duration
    timer_start = time.perf_counter()

    # These values will be filled during execution
    total_rows = None
    valid_ifas_count = None
    invalid_ifas_count = None
    segment_count = None

    # Mark the audience as running while Snowflake and SpringServe are working
    save_audience_run_result_to_db(
        audience_id=audience_id,
        status="running",
        last_update=audience["last_update"],
        last_count=previous_count,
    )

    try:
        # ------------------------------------------------------------------
        # 1. BUILD AUDIENCE FROM SNOWFLAKE
        # ------------------------------------------------------------------
        valid_ifas, invalid_ifas, total_rows = build_audience_from_sql(
            query=query
        )

        valid_ifas_count = len(valid_ifas)
        invalid_ifas_count = len(invalid_ifas)

        print(f"Audience size: {total_rows:,}")
        print(f"Valid IFAs: {valid_ifas_count:,}")
        print(f"Invalid IFAs: {invalid_ifas_count:,}")

        # Stop if there are no valid IFAs
        if valid_ifas_count == 0:
            raise ValueError(
                "Audience has 0 valid IFAs. SpringServe will not be updated."
            )

        # ------------------------------------------------------------------
        # 2. FIND OR CREATE SPRINGSERVE SEGMENT
        # ------------------------------------------------------------------
        segment = ensure_segment(
            name=name,
            description=description,
        )

        # ------------------------------------------------------------------
        # 3. UPDATE SPRINGSERVE
        # ------------------------------------------------------------------
        updated_segment = update_audience(
            segment=segment,
            valid_ifas=valid_ifas,
            output_path=output_path,
            mode=mode,
        )

        segment_count = updated_segment["segment_count"]

        # ------------------------------------------------------------------
        # 4. EXECUTION FINISHED SUCCESSFULLY
        # ------------------------------------------------------------------
        finished_at = _utc_timestamp()
        duration_seconds = time.perf_counter() - timer_start

        # Update the latest status stored in audiences
        save_audience_run_result_to_db(
            audience_id=audience_id,
            status="success",
            last_update=finished_at,
            last_count=segment_count,
        )

        # Save this execution in the historical table
        add_audience_run_to_db(
            audience_id=audience_id,
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            total_rows=total_rows,
            valid_ifas=valid_ifas_count,
            invalid_ifas=invalid_ifas_count,
            segment_count=segment_count,
            duration_seconds=round(duration_seconds, 2),
            error_message=None,
            trigger_source=trigger_source,
        )

        return updated_segment

    except Exception as error:
        # ------------------------------------------------------------------
        # EXECUTION FAILED
        # ------------------------------------------------------------------
        finished_at = _utc_timestamp()
        duration_seconds = time.perf_counter() - timer_start

        # Keep the previous successful segment count when a refresh fails
        save_audience_run_result_to_db(
            audience_id=audience_id,
            status="failed",
            last_update=finished_at,
            last_count=previous_count,
        )

        # Save the failed execution in history
        add_audience_run_to_db(
            audience_id=audience_id,
            started_at=started_at,
            finished_at=finished_at,
            status="failed",
            total_rows=total_rows,
            valid_ifas=valid_ifas_count,
            invalid_ifas=invalid_ifas_count,
            segment_count=segment_count,
            duration_seconds=round(duration_seconds, 2),
            error_message=str(error),
            trigger_source=trigger_source,
        )

        # Raise the original error again so Django/Celery can report it
        raise
