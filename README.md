# Audience Automation

Standalone Django application for creating, refreshing and scheduling SpringServe audiences from Snowflake.

This version deliberately keeps the original backend structure (`src/`) and adds the web/scheduling layers around it. It also adopts the visual language and Celery integration pattern used by the larger Audience Tool so the feature can be integrated there later.

## Core flow

```text
Django dashboard / scheduler
          ↓
run_audience_from_db(audience_id)
          ↓
Snowflake → IFA validation → SpringServe → execution history
```

The same `run_audience_from_db()` function is used for both manual and scheduled refreshes.

## Default schedules

- Manual: no automatic refresh.
- Weekly: Monday at 22:00.
- Monthly: day 1 at 22:00.
- One-time test: choose an exact date/time. Intended for the first 2–3 controlled tests.
- Default timezone: `Europe/Madrid`.

## Important: upgrade the current repository, do not replace runtime data

This release ZIP intentionally does **not** contain `.env`, `.git`, `.venv` or `data/audiences.db`.

When applying it to the existing repository, keep your current:

```text
.env
data/audiences.db
```

The first time the new code reads the existing database it adds the new schedule columns without deleting the existing audiences or run history.

## Local setup

From the project folder:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Simplest automatic scheduling test

For the first controlled test you do **not** need Redis or Celery.

1. Edit 2–3 audiences in the web UI.
2. Set `Frequency = One-time test`.
3. Give them times a few minutes apart today.
4. Keep the scheduler running in a second terminal:

```bash
source .venv/bin/activate
python manage.py run_audience_scheduler
```

The scheduler checks every 30 seconds and runs due audiences through the same `run_audience_from_db()` service.

After the test succeeds, edit those audiences to `Weekly` or `Monthly`.

## Celery / future integrated setup

The project also contains the Celery pattern used by the larger Audience Tool:

```text
Celery Beat
    ↓ every minute
find due audiences
    ↓
Celery worker task per audience
    ↓
run_audience_from_db(audience_id)
```

Start Redis locally:

```bash
docker compose -f docker-compose.scheduler.yml up -d
```

Then, in separate terminals:

```bash
celery -A audience_updater_web worker -l info
```

```bash
celery -A audience_updater_web beat -l info
```

If you also want dashboard `Refresh now` actions to be queued instead of blocking the browser request, set:

```text
AUDIENCE_ASYNC_REFRESH=true
```

For the learning setup, leave it `false`.

## Main files

```text
src/
├── audience_builder.py       Snowflake results → validated IFAs
├── audience_service.py       Runs one complete audience refresh
├── audience_updater.py       Replace / append SpringServe logic
├── database.py               Audience configuration + run history
├── scheduler_service.py      Decides which audience is due
├── scheduling.py             Weekly/monthly/one-time date calculation
├── snowflake_client.py       Snowflake connection
└── springserve_client.py     SpringServe API client

web/
├── forms.py                  Create/edit form and validation
├── views.py                  Django page/action functions
├── urls.py                   Web routes
├── tasks.py                  Celery adapters
├── management/commands/
│   └── run_audience_scheduler.py
├── templates/web/            Django HTML
└── static/web/               Titan OS-style CSS/JS
```

See `docs/WHAT_CHANGED.md` for the learning-oriented explanation of what was kept, modified and added.
