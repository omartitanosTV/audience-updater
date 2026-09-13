import sys
from pathlib import Path


# Allow this learning/test script to be run directly with `python src/test.py`.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from src.audience_service import run_audience_from_db


audience_id = 1

result = run_audience_from_db(audience_id)

print("Audience updated successfully")
print(result)