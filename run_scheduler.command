#!/bin/bash
set -e

cd "$(dirname "$0")"
source .venv/bin/activate
python manage.py run_audience_scheduler
