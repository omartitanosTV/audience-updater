import sqlite3

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from src.database import (
    add_audience_to_db,
    delete_audience_from_db,
    get_all_audience_runs_from_db,
    get_audience_from_db,
    get_audiences_from_db,
    set_audience_enabled_in_db,
    update_audience_in_db,
)
from src.scheduler_service import (
    initialize_missing_schedules,
    recalculate_audience_schedule,
)
from src.scheduling import (
    DEFAULT_SCHEDULE_TIMEZONE,
    calculate_next_refresh,
    describe_schedule,
    format_refresh_datetime,
)
from web.forms import AudienceForm


# Convert one SQLite row into values that are easier to display in templates
def _prepare_audience_for_display(audience):
    item = dict(audience)

    item["schedule_summary"] = describe_schedule(
        refresh_frequency=item["refresh_frequency"],
        schedule_day=item["schedule_day"],
        schedule_time=item["schedule_time"],
        once_at=item["once_at"],
    )
    item["next_refresh_display"] = format_refresh_datetime(
        item["next_refresh_at"],
        item["schedule_timezone"],
    )

    return item


# Convert one history row into a plain dictionary for the template
def _prepare_run_for_display(run):
    item = dict(run)
    item["duration_display"] = (
        f"{item['duration_seconds']:.1f}s"
        if item["duration_seconds"] is not None
        else "—"
    )
    return item


# Convert form fields into the schedule fields stored in SQLite
def _schedule_from_form(form):
    cleaned = form.cleaned_data
    frequency = cleaned["refresh_frequency"]
    schedule_time = cleaned["schedule_time"].strftime("%H:%M")
    schedule_timezone = DEFAULT_SCHEDULE_TIMEZONE
    schedule_day = None
    once_at = None

    if frequency == "weekly":
        schedule_day = cleaned["weekly_day"]
    elif frequency == "monthly":
        schedule_day = cleaned["monthly_day"]
    elif frequency == "once":
        once_at = cleaned["once_at"].isoformat(timespec="minutes")

    next_refresh_at = calculate_next_refresh(
        refresh_frequency=frequency,
        schedule_day=schedule_day,
        schedule_time=schedule_time,
        schedule_timezone=schedule_timezone,
        once_at=once_at,
    )

    return {
        "schedule_day": schedule_day,
        "schedule_time": schedule_time,
        "schedule_timezone": schedule_timezone,
        "once_at": once_at,
        "next_refresh_at": next_refresh_at,
    }


# Build initial form values from an existing SQLite audience row
def _audience_form_initial(audience):
    initial = dict(audience)
    frequency = initial.get("refresh_frequency") or "manual"

    initial["weekly_day"] = (
        initial.get("schedule_day")
        if frequency == "weekly"
        else 0
    )
    initial["monthly_day"] = (
        initial.get("schedule_day")
        if frequency == "monthly"
        else 1
    )
    initial["enabled"] = bool(initial.get("enabled"))

    return initial


# Display the main audience automation dashboard
def dashboard(request):
    # Older audiences receive the requested weekly/monthly default schedule
    # the first time this version starts.
    initialize_missing_schedules()

    audiences = [
        _prepare_audience_for_display(audience)
        for audience in get_audiences_from_db()
    ]
    recent_runs = [
        _prepare_run_for_display(run)
        for run in get_all_audience_runs_from_db(limit=8)
    ]

    summary = {
        "total": len(audiences),
        "active": sum(1 for audience in audiences if audience["enabled"]),
        "scheduled": sum(
            1
            for audience in audiences
            if audience["enabled"]
            and audience["refresh_frequency"] != "manual"
        ),
        "failed": sum(
            1
            for audience in audiences
            if audience["status"] == "failed"
        ),
    }

    return render(
        request,
        "web/dashboard.html",
        {
            "audiences": audiences,
            "recent_runs": recent_runs,
            "summary": summary,
        },
    )


# Create a new audience configuration
def audience_create(request):
    form = AudienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        schedule = _schedule_from_form(form)
        cleaned = form.cleaned_data

        try:
            audience_id = add_audience_to_db(
                name=cleaned["name"],
                description=cleaned["description"],
                query=cleaned["query"],
                mode=cleaned["mode"],
                refresh_frequency=cleaned["refresh_frequency"],
                enabled=cleaned["enabled"],
                **schedule,
            )
        except sqlite3.IntegrityError:
            form.add_error(
                "name",
                "An audience with this name already exists.",
            )
        else:
            messages.success(
                request,
                f"Audience #{audience_id} created successfully.",
            )
            return redirect("web:dashboard")

    return render(
        request,
        "web/audience_form.html",
        {
            "form": form,
            "page_title": "New audience",
            "submit_label": "Create audience",
        },
    )


# Edit one existing audience configuration
def audience_edit(request, audience_id):
    audience = get_audience_from_db(audience_id)

    if audience is None:
        messages.error(request, "Audience not found.")
        return redirect("web:dashboard")

    if request.method == "POST":
        form = AudienceForm(request.POST)
    else:
        form = AudienceForm(
            initial=_audience_form_initial(audience)
        )

    if request.method == "POST" and form.is_valid():
        schedule = _schedule_from_form(form)
        cleaned = form.cleaned_data

        try:
            update_audience_in_db(
                audience_id=audience_id,
                name=cleaned["name"],
                description=cleaned["description"],
                query=cleaned["query"],
                mode=cleaned["mode"],
                refresh_frequency=cleaned["refresh_frequency"],
                enabled=cleaned["enabled"],
                **schedule,
            )
        except sqlite3.IntegrityError:
            form.add_error(
                "name",
                "An audience with this name already exists.",
            )
        else:
            messages.success(request, "Audience updated successfully.")
            return redirect("web:dashboard")

    return render(
        request,
        "web/audience_form.html",
        {
            "form": form,
            "page_title": "Edit audience",
            "submit_label": "Save changes",
            "audience": audience,
        },
    )


# Refresh one audience immediately from the dashboard
@require_POST
def refresh_audience(request, audience_id):
    audience = get_audience_from_db(audience_id)

    if audience is None:
        messages.error(request, "Audience not found.")
        return redirect("web:dashboard")

    # The standalone project defaults to synchronous execution because it is
    # easier to understand and test. The future integrated project can switch
    # this flag on and reuse the Celery task already included in web/tasks.py.
    if getattr(settings, "AUDIENCE_ASYNC_REFRESH", False):
        from web.tasks import refresh_audience_task

        refresh_audience_task.delay(audience_id, "manual")
        messages.success(
            request,
            f"Refresh queued for {audience['name']}.",
        )
        return redirect("web:dashboard")

    try:
        # Import the heavy Snowflake/SpringServe flow only when a refresh is
        # actually requested. This keeps normal dashboard startup lightweight.
        from src.audience_service import run_audience_from_db

        result = run_audience_from_db(
            audience_id,
            trigger_source="manual",
        )
    except Exception as error:
        messages.error(
            request,
            f"Refresh failed: {error}",
        )
    else:
        messages.success(
            request,
            f"Refresh completed. Segment count: "
            f"{result.get('segment_count', 'unknown')}",
        )

    return redirect("web:dashboard")


# Enable or disable one audience
@require_POST
def toggle_audience(request, audience_id):
    audience = get_audience_from_db(audience_id)

    if audience is None:
        messages.error(request, "Audience not found.")
        return redirect("web:dashboard")

    new_enabled = not bool(audience["enabled"])
    set_audience_enabled_in_db(audience_id, new_enabled)

    # Re-enabling a recurring audience should calculate a fresh future slot
    # instead of immediately executing a schedule that expired while disabled.
    if new_enabled and str(audience["refresh_frequency"]).lower() in {"weekly", "monthly"}:
        recalculate_audience_schedule(audience_id)

    messages.success(
        request,
        "Audience enabled." if new_enabled else "Audience disabled.",
    )
    return redirect("web:dashboard")


# Delete one audience and its execution history
@require_POST
def audience_delete(request, audience_id):
    audience = get_audience_from_db(audience_id)

    if audience is None:
        messages.error(request, "Audience not found.")
        return redirect("web:dashboard")

    audience_name = audience["name"]
    delete_audience_from_db(audience_id)
    messages.success(request, f"{audience_name} deleted.")

    return redirect("web:dashboard")


# Display the complete execution history
def history(request):
    runs = [
        _prepare_run_for_display(run)
        for run in get_all_audience_runs_from_db()
    ]

    return render(
        request,
        "web/history.html",
        {"runs": runs},
    )
