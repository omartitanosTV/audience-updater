import time
from springserve_client import get_segments, create_segment, get_segment_by_id



def ensure_segment(name, description):
    # Get all existing SpringServe segments
    segments = get_segments()

    # Look for an existing segment with the same name
    for segment in segments:
        if segment["name"] == name:
            return segment

    # If the segment does not exist, create it
    return create_segment(
        name=name,
        description=description
    )
    

def wait_for_segment_upload(segment_id, timeout_seconds=300, check_every=10):
    # Record when the waiting period starts
    start_time = time.time()

    while True:
        # Get the latest segment status from SpringServe
        segment = get_segment_by_id(segment_id)

        upload_status = segment["upload_status"]
        segment_count = segment["segment_count"]

        print(
            f"Upload status: {upload_status} | "
            f"Segment count: {segment_count}"
        )

        # Stop waiting when SpringServe finishes processing
        if upload_status == "complete":
            return segment

        # Stop with an error if the maximum waiting time is reached
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(
                "SpringServe upload did not complete within the expected time."
            )

        # Wait before checking again
        time.sleep(check_every)