# What changed and why

This file is written as a learning map: it separates the code that already existed from the code added in this version.

## 1. Kept from the original Audience Updater

These responsibilities remain the same:

- `src/audience_builder.py`: runs the Snowflake SQL and validates/deduplicates IFAs.
- `src/audience_service.py`: central business flow for one audience.
- `src/audience_updater.py`: decides between SpringServe replace and append.
- `src/snowflake_client.py`: Snowflake connection.
- `src/springserve_client.py`: SpringServe connection.
- `src/database.py`: SQLite audience configuration and run history.

The most important rule is still:

```python
run_audience_from_db(audience_id)
```

Django and the scheduler both call that function instead of duplicating the Snowflake/SpringServe logic.

## 2. Existing files modified

### `src/database.py`

Still uses the same SQLite database. New columns were added for scheduling:

- `schedule_day`
- `schedule_time`
- `schedule_timezone`
- `once_at`
- `next_refresh_at`
- `last_scheduled_at`

`audience_runs` now also stores `trigger_source` (`manual` or `scheduled`).

The database upgrade is additive: old rows are kept. Weekly rows default to Monday; monthly rows default to day 1.

### `src/audience_service.py`

Still performs the same four business steps:

1. Snowflake query.
2. IFA validation.
3. Find/create SpringServe segment.
4. Replace/append and save history.

New additions:

- `status="running"` while a refresh is executing.
- `trigger_source` stored in history.
- UTC timestamps for consistent scheduling/history.

### `src/springserve_client.py`

The public functions used by the original project are preserved (`get_segments`, `create_segment`, `replace_segment_ifas`, etc.).

The HTTP handling was hardened using patterns already present in the larger Audience Tool:

- clearer SpringServe HTTP errors;
- one authentication retry after HTTP 401;
- reusable `requests.Session`;
- safer JSON/collection validation;
- longer upload timeout.

### `src/audience_updater.py`

A no-change append is now treated as a success. Previously, if there were zero new IFAs, the function returned `None`, which could later fail when `audience_service.py` expected a segment dictionary.

## 3. New core scheduling files

### `src/scheduling.py`

Pure scheduling calculations. It knows how to calculate:

- next Monday at 22:00;
- next day 1 at 22:00;
- any custom weekly/monthly day/time;
- a one-time test date/time.

It does **not** know anything about Snowflake or SpringServe.

### `src/scheduler_service.py`

Connects schedules to the existing audience service:

```text
is an audience due?
      ↓ yes
claim its next schedule
      ↓
run_audience_from_db(id)
```

This separation makes it possible to use a simple local scheduler now and Celery later without changing the audience business logic.

## 4. New Django files

### `web/forms.py`

Defines and validates the create/edit audience form.

This is standard Django form logic, but it still saves to the existing custom SQLite functions rather than replacing the backend with Django ORM models.

### `web/templates/web/*`

The UI now has:

- Dashboard.
- New/Edit Audience.
- Run History.
- Refresh now.
- Enable/Disable.
- Delete.
- Weekly/Monthly/One-time scheduling.

### `web/static/web/app.css`

Uses the same visual language as `AudienceTool_V2_42_0_RELEASE`:

- Poppins;
- dark Titan OS shell;
- left navigation rail;
- Titan red accent;
- same panel/input/table/button treatment.

It is a smaller stylesheet because this standalone project does not need the hundreds of selectors for PCA, Builder, Media Plan, etc.

## 5. Scheduler adapters

### `web/management/commands/run_audience_scheduler.py`

Simple scheduler for the first controlled local test.

```bash
python manage.py run_audience_scheduler
```

It intentionally avoids Redis/Celery so the first 2–3 scheduled audiences are easy to understand and debug.

### `web/tasks.py` and `audience_updater_web/celery.py`

Celery adapter following the architecture already used by the larger Audience Tool.

It exists now so future integration is straightforward, but the core schedule logic remains in `src/scheduler_service.py`.

## 6. Structural change: `src` is now a Python package

`src/__init__.py` was added and imports use `from src...`.

Why: Django imports the backend from the project root. Explicit package imports are less ambiguous than relying on the terminal's current directory.

For manual `src/test.py` testing, run:

```bash
python -m src.test
```

instead of:

```bash
python src/test.py
```

The test code itself remains visible in `src/test.py`.

## 7. What was deliberately NOT copied from the larger Audience Tool

The standalone project does not import its complete architecture, models, API endpoints, PCA code, async job registry, monitoring stack or hundreds of frontend functions.

That would make this project harder to understand and would create unnecessary coupling.

Only patterns that directly help Audience Automation were reused.
