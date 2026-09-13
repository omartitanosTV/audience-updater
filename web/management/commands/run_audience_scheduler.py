import time

from django.core.management.base import BaseCommand

from src.scheduler_service import run_due_audiences


class Command(BaseCommand):
    help = (
        "Run the simple local audience scheduler. "
        "This is intended for controlled local testing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=30,
            help="Seconds between schedule checks. Default: 30.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Check due audiences once and exit.",
        )

    def handle(self, *args, **options):
        interval = max(5, int(options["interval"]))

        self.stdout.write(
            self.style.SUCCESS(
                "Audience scheduler started. Press CONTROL-C to stop."
            )
        )

        while True:
            results = run_due_audiences()

            for result in results:
                audience_id = result["audience_id"]
                status = result["status"]

                if status == "success":
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Audience {audience_id}: scheduled refresh completed."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Audience {audience_id}: {result.get('error')}"
                        )
                    )

            if options["once"]:
                return

            time.sleep(interval)
