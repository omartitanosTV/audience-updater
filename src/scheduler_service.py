from datetime import datetime, timezone

from src.database import (
    get_audience_from_db,
    get_audiences_from_db,
    get_due_audiences_from_db,
    set_audience_next_refresh_in_db,
)
from src.scheduling import (
    calculate_next_refresh,
    to_utc_iso,
)


# Build the next automatic refresh from one stored audience configuration
def calculate_next_refresh_for_audience(audience, now=None):
    return calculate_next_refresh(
        refresh_frequency=audience["refresh_frequency"],
        schedule_day=audience["schedule_day"],
        schedule_time=audience["schedule_time"],
        schedule_timezone=audience["schedule_timezone"],
        once_at=audience["once_at"],
        now=now,
    )


# Populate next_refresh_at for older audiences that do not have it yet
def initialize_missing_schedules(now=None):
    now_utc = now or datetime.now(timezone.utc)

    for audience in get_audiences_from_db():
        frequency = str(audience["refresh_frequency"] or "manual").lower()

        if frequency == "manual" or audience["next_refresh_at"]:
            continue

        next_refresh_at = calculate_next_refresh_for_audience(
            audience,
            now=now_utc,
        )

        set_audience_next_refresh_in_db(
            audience_id=audience["id"],
            next_refresh_at=next_refresh_at,
        )


# Recalculate one audience after its schedule is created or edited
def recalculate_audience_schedule(audience_id, now=None):
    audience = get_audience_from_db(audience_id)

    if audience is None:
        raise ValueError(
            f"Audience with ID {audience_id} was not found in the database."
        )

    next_refresh_at = calculate_next_refresh_for_audience(
        audience,
        now=now,
    )

    set_audience_next_refresh_in_db(
        audience_id=audience_id,
        next_refresh_at=next_refresh_at,
    )

    return next_refresh_at


# Claim due schedules before execution so the same run is not picked twice
def claim_due_audience_ids(now=None):
    now_utc = now or datetime.now(timezone.utc)
    now_iso = to_utc_iso(now_utc)

    initialize_missing_schedules(now=now_utc)

    due_audiences = get_due_audiences_from_db(now_iso)
    claimed_ids = []

    for audience in due_audiences:
        frequency = str(audience["refresh_frequency"] or "manual").lower()

        # A one-time schedule should not be picked again after this claim.
        if frequency == "once":
            next_refresh_at = None
        else:
            # Calculate from the current time. Because the current due time is
            # already in the past, weekly/monthly automatically advance to the
            # following occurrence.
            next_refresh_at = calculate_next_refresh_for_audience(
                audience,
                now=now_utc,
            )

        set_audience_next_refresh_in_db(
            audience_id=audience["id"],
            next_refresh_at=next_refresh_at,
            last_scheduled_at=now_iso,
        )

        claimed_ids.append(audience["id"])

    return claimed_ids


# Execute all due audiences sequentially.
# This is the simple local scheduler used for controlled testing.
def run_due_audiences(now=None):
    audience_ids = claim_due_audience_ids(now=now)
    results = []

    for audience_id in audience_ids:
        try:
            # Import the external-service flow only when an audience is due.
            from src.audience_service import run_audience_from_db

            result = run_audience_from_db(
                audience_id,
                trigger_source="scheduled",
            )
            results.append(
                {
                    "audience_id": audience_id,
                    "status": "success",
                    "segment_count": result.get("segment_count"),
                }
            )
        except Exception as error:
            # The audience service already records the failed run in history.
            # Keep the scheduler alive so another audience can still execute.
            results.append(
                {
                    "audience_id": audience_id,
                    "status": "failed",
                    "error": str(error),
                }
            )

    return results
