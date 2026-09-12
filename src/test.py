from audience_service import run_audience_from_db


# Run the audience stored in the database
updated_segment = run_audience_from_db(
    audience_id=1
)

print("Audience executed successfully")
print(f"Final segment count: {updated_segment['segment_count']}")