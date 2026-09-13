import calendar
import os
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


# Default schedule values requested for automatic audience refreshes
DEFAULT_SCHEDULE_TIME = "22:00"
DEFAULT_SCHEDULE_TIMEZONE = os.getenv(
    "AUDIENCE_SCHEDULE_TIMEZONE",
    "Europe/Madrid",
)
DEFAULT_WEEKLY_DAY = 0  # Monday
DEFAULT_MONTHLY_DAY = 1


# Convert a HH:MM string into a Python time object
def parse_schedule_time(value):
    value = str(value or DEFAULT_SCHEDULE_TIME).strip()

    try:
        hour, minute = value.split(":", 1)
        return time(hour=int(hour), minute=int(minute))
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid schedule time '{value}'. Expected HH:MM."
        )


# Convert a datetime into the UTC ISO format stored in SQLite
def to_utc_iso(value):
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


# Parse a stored ISO datetime and always return an aware UTC datetime
def parse_utc_iso(value):
    if not value:
        return None

    parsed = datetime.fromisoformat(str(value))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


# Parse an HTML datetime-local value in the selected audience timezone
def parse_local_datetime(value, timezone_name):
    if not value:
        return None

    parsed = datetime.fromisoformat(str(value))
    timezone_info = ZoneInfo(timezone_name or DEFAULT_SCHEDULE_TIMEZONE)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone_info)
    else:
        parsed = parsed.astimezone(timezone_info)

    return parsed


# Calculate the next time an audience should refresh automatically
def calculate_next_refresh(
    refresh_frequency,
    schedule_day=None,
    schedule_time=DEFAULT_SCHEDULE_TIME,
    schedule_timezone=DEFAULT_SCHEDULE_TIMEZONE,
    once_at=None,
    now=None,
):
    frequency = str(refresh_frequency or "manual").lower().strip()

    # Manual audiences never receive an automatic next refresh
    if frequency == "manual":
        return None

    timezone_info = ZoneInfo(
        schedule_timezone or DEFAULT_SCHEDULE_TIMEZONE
    )

    now_utc = now or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)

    now_local = now_utc.astimezone(timezone_info)
    target_time = parse_schedule_time(schedule_time)

    # One-time schedules are useful for controlled tests before enabling
    # weekly or monthly production schedules.
    if frequency == "once":
        local_once = parse_local_datetime(
            once_at,
            schedule_timezone or DEFAULT_SCHEDULE_TIMEZONE,
        )
        return to_utc_iso(local_once) if local_once else None

    if frequency == "weekly":
        weekday = (
            DEFAULT_WEEKLY_DAY
            if schedule_day is None
            else int(schedule_day)
        )

        if weekday < 0 or weekday > 6:
            raise ValueError("Weekly schedule day must be between 0 and 6.")

        days_ahead = (weekday - now_local.weekday()) % 7
        candidate_date = now_local.date() + timedelta(days=days_ahead)
        candidate = datetime.combine(
            candidate_date,
            target_time,
            tzinfo=timezone_info,
        )

        if candidate <= now_local:
            candidate += timedelta(days=7)

        return to_utc_iso(candidate)

    if frequency == "monthly":
        day = (
            DEFAULT_MONTHLY_DAY
            if schedule_day is None
            else int(schedule_day)
        )

        if day < 1 or day > 31:
            raise ValueError("Monthly schedule day must be between 1 and 31.")

        year = now_local.year
        month = now_local.month

        def monthly_candidate(candidate_year, candidate_month):
            last_day = calendar.monthrange(
                candidate_year,
                candidate_month,
            )[1]
            safe_day = min(day, last_day)

            return datetime(
                candidate_year,
                candidate_month,
                safe_day,
                target_time.hour,
                target_time.minute,
                tzinfo=timezone_info,
            )

        candidate = monthly_candidate(year, month)

        if candidate <= now_local:
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

            candidate = monthly_candidate(year, month)

        return to_utc_iso(candidate)

    raise ValueError(
        f"Unsupported refresh frequency: {refresh_frequency}"
    )


# Convert a stored UTC schedule into a readable local value for the UI
def format_refresh_datetime(value, schedule_timezone=DEFAULT_SCHEDULE_TIMEZONE):
    parsed = parse_utc_iso(value)

    if parsed is None:
        return "—"

    timezone_info = ZoneInfo(
        schedule_timezone or DEFAULT_SCHEDULE_TIMEZONE
    )

    local_value = parsed.astimezone(timezone_info)
    return local_value.strftime("%Y-%m-%d %H:%M")


# Create a short human-readable description of an audience schedule
def describe_schedule(
    refresh_frequency,
    schedule_day=None,
    schedule_time=DEFAULT_SCHEDULE_TIME,
    once_at=None,
):
    frequency = str(refresh_frequency or "manual").lower().strip()

    if frequency == "manual":
        return "Manual"

    if frequency == "weekly":
        weekday = (
            DEFAULT_WEEKLY_DAY
            if schedule_day is None
            else int(schedule_day)
        )
        weekday_name = calendar.day_name[weekday]
        return f"Weekly · {weekday_name} {schedule_time}"

    if frequency == "monthly":
        day = (
            DEFAULT_MONTHLY_DAY
            if schedule_day is None
            else int(schedule_day)
        )
        return f"Monthly · Day {day} {schedule_time}"

    if frequency == "once":
        if not once_at:
            return "One-time · not scheduled"
        local_once = datetime.fromisoformat(str(once_at))
        return f"One-time · {local_once.strftime('%Y-%m-%d %H:%M')}"

    return str(refresh_frequency)
