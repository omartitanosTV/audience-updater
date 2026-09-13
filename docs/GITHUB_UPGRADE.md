# Applying this version to the existing GitHub repository

This release is meant to **evolve** the existing `audience-updater` repository, not replace its history.

Recommended approach:

```bash
cd ~/audience-updater
git checkout -b feature/audience-automation-web
```

Keep the existing runtime files:

```text
.env
data/audiences.db
```

Then copy the files from this release over the repository and review the diff:

```bash
git status
git diff
```

The expected change shape is mostly:

```text
modified: audience_updater_web/settings.py
modified: audience_updater_web/urls.py
modified: src/audience_service.py
modified: src/audience_updater.py
modified: src/database.py
modified: src/springserve_client.py
modified: web/views.py
modified: web/urls.py
new:      src/scheduling.py
new:      src/scheduler_service.py
new:      web/forms.py
new:      web/tasks.py
new:      web/templates/web/*
new:      web/static/web/*
new:      web/management/commands/run_audience_scheduler.py
new:      audience_updater_web/celery.py
```

After installing the updated requirements:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
```

Then run the controlled 2–3 audience scheduling test in `docs/SCHEDULER_TEST.md` before merging the branch into `main`.
