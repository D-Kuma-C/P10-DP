import random
from pathlib import Path

TRAJECTORY_FILE = Path(r"C:\Git\P10-DP\data\Porto\porto_time_lines-all_0511_154535_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630.dat")
SEGMENT_FILE = Path(r"C:\Git\P10-DP\data\Porto\porto_trajectory_segments0511_154535.csv")


NUMBER_OF_TRAJECTORIES = 5
RANDOM_SEED = 42


OUTPUT_TRAJECTORY_FILE = Path(r"C:\Git\P10-DP\output\subset_trajectories.dat")
OUTPUT_SEGMENT_FILE = Path(r"C:\Git\P10-DP\output\subset_segments.csv")

# =========================
# SELECT RANDOM TRAJECTORY IDS
# =========================

def get_all_trajectory_ids(dat_file):
    trajectory_ids = []

    with open(dat_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line.startswith("#"):
                traj_id = int(line[1:])
                trajectory_ids.append(traj_id)

    return trajectory_ids


all_ids = get_all_trajectory_ids(TRAJECTORY_FILE)

if NUMBER_OF_TRAJECTORIES > len(all_ids):
    raise ValueError(
        f"Requested {NUMBER_OF_TRAJECTORIES} trajectories but only {len(all_ids)} exist"
    )

random.seed(RANDOM_SEED)
selected_ids = sorted(random.sample(all_ids, NUMBER_OF_TRAJECTORIES))

selected_id_set = set(selected_ids)

print("Selected trajectory IDs:")
print(selected_ids)

# =========================
# FILTER TRAJECTORY FILE
# =========================


def filter_trajectory_file(input_file, output_file, selected_ids):
    write_block = False

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        current_id = None

        for line in infile:
            stripped = line.strip()

            if stripped.startswith("#"):
                current_id = int(stripped[1:])
                write_block = current_id in selected_ids

            if write_block:
                outfile.write(line)


filter_trajectory_file(
    TRAJECTORY_FILE,
    OUTPUT_TRAJECTORY_FILE,
    selected_id_set
)

# =========================
# FILTER SEGMENT FILE
# =========================


def filter_segment_file(input_file, output_file, selected_ids):
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        header = infile.readline()
        outfile.write(header)

        for line in infile:
            parts = line.strip().split(",")

            if len(parts) < 3:
                continue

            traj_id = int(parts[0])

            if traj_id in selected_ids:
                outfile.write(line)


filter_segment_file(
    SEGMENT_FILE,
    OUTPUT_SEGMENT_FILE,
    selected_id_set
)

print()
print("Finished generating subset files")
print(f"Trajectory file: {OUTPUT_TRAJECTORY_FILE}")
print(f"Segment file: {OUTPUT_SEGMENT_FILE}")
