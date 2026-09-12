import time
from springserve_client import (
    get_segment_ifas,
    get_segments,
    create_segment,
    get_segment_by_id,
    append_segment_ifas,
    replace_segment_ifas
)
from pathlib import Path



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
        
        
# This function compares the current IFAs in SpringServe with the valid IFAs from Snowflake
def get_new_ifas(current_ifas, valid_ifas):
    # Convert both lists to sets
    springserve_ifas = set(current_ifas)
    snowflake_ifas = set(valid_ifas)

    # Keep only IFAs that exist in Snowflake
    # but do not exist yet in SpringServe
    new_ifas = snowflake_ifas - springserve_ifas

    # Convert the result back to a list
    new_ifas = list(new_ifas)

    return new_ifas

# This function appends new IFAs to an existing SpringServe segment
def append_new_ifas(segment_id, valid_ifas, output_path):
    # Get the IFAs that already exist in SpringServe
    current_ifas = get_segment_ifas(segment_id)

    # Keep only IFAs that are new
    new_ifas = get_new_ifas(
        current_ifas=current_ifas,
        valid_ifas=valid_ifas
    )

    print(f"New IFAs to append: {len(new_ifas):,}")

    # If there are no new IFAs, do nothing
    if len(new_ifas) == 0:
        print("No new IFAs to append")
        return None

    # Convert the output path into a Path object
    output_path = Path(output_path)

    # Create a fixed backup path for the current audience
    backup_path = output_path.with_name(
        f"{output_path.stem}_backup{output_path.suffix}"
    )

    # Save the current SpringServe audience as backup
    with open(backup_path, "w") as file:
        for ifa in current_ifas:
            file.write(ifa + "\n")

    print(f"Current audience backed up: {backup_path}")

    # Create a fixed path for the temporary append CSV
    append_path = output_path.with_name(
        f"{output_path.stem}_append{output_path.suffix}"
    )

    # Create a CSV containing only the new IFAs
    with open(append_path, "w") as file:
        for ifa in new_ifas:
            file.write(ifa + "\n")

    # Append only the new IFAs to SpringServe
    append_segment_ifas(
        segment_id=segment_id,
        file_path=append_path
    )

    # Wait until SpringServe finishes processing the uploaded IFAs
    updated_segment = wait_for_segment_upload(segment_id)

    print("Append completed")
    print(f"Final segment count: {updated_segment['segment_count']}")

    return updated_segment
    


# This function compares the current IFAs in SpringServe with the valid IFAs from Snowflake
def get_replace_changes(current_ifas, valid_ifas):
    # Convert both lists to sets
    springserve_ifas = set(current_ifas)
    snowflake_ifas = set(valid_ifas)

    # IFAs that are in Snowflake but not currently in SpringServe
    added_ifas = snowflake_ifas - springserve_ifas

    # IFAs that are currently in SpringServe but no longer in Snowflake
    removed_ifas = springserve_ifas - snowflake_ifas

    return list(added_ifas), list(removed_ifas)


# This function replaces the current IFAs in SpringServe with the valid IFAs from Snowflake
def replace_ifas_with_summary(segment_id, valid_ifas, output_path):
    # Get the IFAs currently stored in SpringServe
    current_ifas = get_segment_ifas(segment_id)
    
    # Create a backup of the current SpringServe audience
    # Get the path to the output CSV file
    output_path = Path(output_path)

    # Create a fixed backup path for the current audience
    backup_path = output_path.with_name(
        f"{output_path.stem}_backup{output_path.suffix}"
    )

    # Save the current SpringServe audience as backup
    with open(backup_path, "w") as file:
        for ifa in current_ifas:
            file.write(ifa + "\n")

    print(f"Current audience backed up: {backup_path}")

    # Calculate which IFAs will be added and removed
    added_ifas, removed_ifas = get_replace_changes(
        current_ifas=current_ifas,
        valid_ifas=valid_ifas
    )

    print(f"Current IFAs: {len(current_ifas):,}")
    print(f"New audience IFAs: {len(valid_ifas):,}")
    print(f"IFAs added: {len(added_ifas):,}")
    print(f"IFAs removed: {len(removed_ifas):,}")

    # Create the CSV with the full new audience
    with open(output_path, "w") as file:
        for ifa in valid_ifas:
            file.write(ifa + "\n")

    # Replace the current SpringServe segment with the new audience
    replace_segment_ifas(
        segment_id=segment_id,
        file_path=output_path
    )

    
    # Wait until SpringServe finishes processing the uploaded IFAs
    updated_segment = wait_for_segment_upload(segment_id)

    print("Replace completed")
    print(f"Final segment count: {updated_segment['segment_count']}")

    return updated_segment


# This function updates a SpringServe audience using the selected update mode
def update_audience(segment, valid_ifas, output_path, mode):
    # Check if the audience should be replaced
    if mode == "replace":
        return replace_ifas_with_summary(
            segment_id=segment["id"],
            valid_ifas=valid_ifas,
            output_path=output_path
        )

    # Check if the audience should be appended
    elif mode == "append":
        return append_new_ifas(
            segment_id=segment["id"],
            valid_ifas=valid_ifas,
            output_path=output_path
        )

    # Stop if the update mode is not supported
    else:
        raise ValueError(
            f"Unsupported update mode: {mode}"
        )