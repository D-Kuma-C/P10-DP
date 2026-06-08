from pathlib import Path
from datetime import datetime

INPUT_DATASET = r"C:\Git\P10-DP\data\geolife_time_users--all_0518_151834_p-3_d-0.05_s-40_t-15min_start-20070401_end-20111101.dat"
OUTPUT_DATASET = r"C:\Git\P10-DP\data\geo_time_valid.dat"
INVALID_IDS_FILE = r"C:\Git\P10-DP\data\geo_invalid_ids.txt"

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

trajectory_count = 0
last_trajectory_id = None
invalid_trajectories = 0
invalid_ids = []

total_trajectories = 0
valid_trajectories = 0
invalid_trajectories = 0

current_traj_id = None

def timestamps_are_valid(points):

    timestamps = []

    for point in points:

        parts = point.split(",")

        
        if len(parts) < 3:
            return False

        timestamp_str = ",".join(parts[2:]).strip()

        try:
            ts = datetime.strptime(timestamp_str, TIME_FORMAT)
            timestamps.append(ts)

        except:
            return False

    for i in range(1, len(timestamps)):

        if timestamps[i] < timestamps[i - 1]:
            return False

    return True


with open(INPUT_DATASET, "r", encoding="utf-8", errors="ignore") as fin, \
     open(OUTPUT_DATASET, "w", encoding="utf-8") as fout:

    current_header = None
    current_body = None

    for line in fin:

        line = line.strip()

        # trajectory header
        if line.startswith("#"):

            # process previous trajectory
            if current_header and current_body:

                total_trajectories += 1
                if (total_trajectories % 100 == 0):
                    print("Current number:", total_trajectories)
                traj_id = int(current_header[1:])

                content = current_body[3:]
                points = [p for p in content.split(";") if p]

                if timestamps_are_valid(points):

                    fout.write(current_header + "\n")
                    fout.write(current_body + "\n")

                    valid_trajectories += 1

                else:
                    invalid_trajectories += 1
                    invalid_ids.append(traj_id)

            current_header = line
            current_body = None

        elif line.startswith(">0:"):
            current_body = line

    # final trajectory
    if current_header and current_body:

        total_trajectories += 1

        traj_id = int(current_header[1:])

        content = current_body[3:]
        points = [p for p in content.split(";") if p]

        if timestamps_are_valid(points):

            fout.write(current_header + "\n")
            fout.write(current_body + "\n")

            valid_trajectories += 1

        else:
            invalid_trajectories += 1
            invalid_ids.append(traj_id)


# write invalid ids
with open(INVALID_IDS_FILE, "w") as f:
    for traj_id in invalid_ids:
        f.write(str(traj_id) + "\n")


print("\n========== SUMMARY ==========")
print("Total trajectories :", total_trajectories)
print("Valid trajectories :", valid_trajectories)
print("Invalid trajectories :", invalid_trajectories)

print("\nSaved cleaned dataset to:")
print(OUTPUT_DATASET)

print("\nSaved invalid IDs to:")
print(INVALID_IDS_FILE)