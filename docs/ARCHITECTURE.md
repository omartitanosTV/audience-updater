# Audience Automation architecture

```text
                              ┌─────────────────────────┐
                              │ Django web interface    │
                              │ Refresh / CRUD / config │
                              └────────────┬────────────┘
                                           │
                              manual       │
                                           ▼
┌──────────────────┐           ┌──────────────────────────┐
│ Local scheduler  │──────────▶│ run_audience_from_db(id) │
│ or Celery Beat   │ scheduled │ audience_service.py      │
└──────────────────┘           └────────────┬─────────────┘
                                           │
                      ┌────────────────────┼────────────────────┐
                      ▼                    ▼                    ▼
                 Snowflake            SpringServe        SQLite history
```

## Separation of responsibilities

`web/` is the interface layer.

`src/scheduling.py` decides *when* a refresh should happen.

`src/scheduler_service.py` decides *which* configured audience is due.

`src/audience_service.py` decides *how* an audience is refreshed.

This is intentional: future integration into the larger Audience Tool should mostly replace/merge the interface and scheduler adapters, not the business flow.
