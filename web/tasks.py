from celery import shared_task

from src.audience_service import run_audience_from_db
from src.scheduler_service import claim_due_audience_ids


@shared_task(bind=True, acks_late=True, reject_on_worker_lost=True)
def refresh_audience_task(self, audience_id, trigger_source="scheduled"):
    """Run one audience outside the Django request process."""

    result = run_audience_from_db(
        audience_id,
        trigger_source=trigger_source,
    )

    return {
        "audience_id": audience_id,
        "segment_count": result.get("segment_count"),
        "status": "success",
    }


@shared_task
def dispatch_due_audiences_task():
    """Find due schedules and queue one worker task per audience."""

    audience_ids = claim_due_audience_ids()

    for audience_id in audience_ids:
        refresh_audience_task.delay(
            audience_id,
            "scheduled",
        )

    return {
        "queued": audience_ids,
        "count": len(audience_ids),
    }
