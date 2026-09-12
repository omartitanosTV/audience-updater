from audience_updater import append_new_ifas
from springserve_client import get_segment_ifas

segment_id = 133353

current_ifas = get_segment_ifas(segment_id)

valid_ifas = [
    current_ifas[0],
    current_ifas[1],
    "22222222-2222-4222-8222-222222222222",
]

updated_segment = append_new_ifas(
    segment_id=segment_id,
    valid_ifas=valid_ifas,
    output_path="src/test_append.csv"
)

print(f"Final segment count: {updated_segment['segment_count']}")