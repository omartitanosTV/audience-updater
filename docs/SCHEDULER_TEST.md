# Controlled scheduling test with 2–3 audiences

The goal is to prove automatic execution before enabling weekly/monthly schedules.

## Test plan

Choose 2–3 audiences whose result you can recognise in SpringServe.

For each audience:

1. Open `Edit`.
2. Keep the current SQL and replace/append mode.
3. Set `Frequency` to `One-time test`.
4. Choose a time today a few minutes in the future.
5. Space the audiences apart (for example, 5 minutes) because local scheduled runs execute sequentially.

Then start the scheduler in a second terminal:

```bash
cd ~/audience-updater
source .venv/bin/activate
python manage.py run_audience_scheduler
```

Keep the Django server in its own terminal:

```bash
python manage.py runserver
```

## What to verify

After each scheduled time:

- The scheduler terminal says the audience executed.
- SpringServe shows the expected audience count.
- Dashboard status becomes `Success` or `Failed`.
- `Run History` shows `Trigger = Scheduled`.
- `Valid IFAs`, `Segment count` and duration are populated.
- For a one-time schedule, `Next refresh` becomes empty after it is claimed.

## After the test

Edit each test audience:

- Weekly → Monday → 22:00, or
- Monthly → day 1 → 22:00.

You can change the day/time per audience when needed.
