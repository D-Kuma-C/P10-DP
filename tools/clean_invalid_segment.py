
INPUT_SEGMENTS = r"C:\Git\P10-DP\data\geolife_trajectory_segments0518_151834.csv"
OUTPUT_SEGMENTS = r"C:\Git\P10-DP\data\geolife_segments_cleaned.csv"

INVALID_IDS_FILE = r"C:\Git\P10-DP\data\geo_invalid_ids.txt"

def load_invalid_ids():
    invalid_ids = set()

    with open(INVALID_IDS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                invalid_ids.add(int(line))
            except ValueError:
                continue

    print(f"Loaded {len(invalid_ids)} invalid trajectory IDs")

    return invalid_ids

def clean_segment_file(invalid_ids):

    kept_lines = 0
    removed_lines = 0

    with open(INPUT_SEGMENTS, "r", encoding="utf-8") as fin, \
         open(OUTPUT_SEGMENTS, "w", encoding="utf-8") as fout:

        # preserve header
        header = fin.readline()
        fout.write(header)
        counter = 0
        for line in fin:

            if (counter % 100 == 0):
                print("Status:", counter)
            line = line.strip()

            if not line:
                continue

            parts = line.split(",")

            if len(parts) < 3:
                continue

            try:
                traj_id = int(parts[0])

            except ValueError:
                continue

            if traj_id not in invalid_ids:

                fout.write(line + "\n")
                kept_lines += 1

            else:
                removed_lines += 1
            
            counter += 1

    print("\n========== SEGMENT SUMMARY ==========")
    print("Kept segment rows    :", kept_lines)
    print("Removed segment rows :", removed_lines)

invalid_ids = load_invalid_ids()

clean_segment_file(invalid_ids)