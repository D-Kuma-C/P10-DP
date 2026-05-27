from pathlib import Path

FILE_PATH = r"C:\Users\Trailblaze\Documents\GitHub\P10-DP\data\tdrive\tdrive_files-all0515_105317_p-3_d-0.05_t-15min_start-20080202_end-20080209.dat"   # change this

trajectory_count = 0
last_trajectory_id = None

with open(FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()

        # trajectory header lines look like:
        #0
        #12345
        if line.startswith("#"):
            trajectory_count += 1
            print("Current number", trajectory_count)
            try:
                last_trajectory_id = int(line[1:])
            except ValueError:
                pass

print(f"Total trajectories : {trajectory_count}")
print(f"Last trajectory ID : {last_trajectory_id}")