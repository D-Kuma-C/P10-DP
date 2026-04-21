import datetime
import math
import csv
import json

START_LINE = 0
END_LINE = 1000

START_DATE = datetime.datetime.strptime("2013-01-07", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2014-06-30", "%Y-%m-%d")

INCLUDE_TIME = False

MIN_POINTS = 3
MAX_TIME = 15 * 60
MAX_DISTANCE = 0.05 # 5 kilometer
MIN_DISTANCE = 0.0001 # 10 m

POINT_INTERVAL = 15 # 15 seconds between points

MAX_SPEED = 40

time_tag = "_time" if INCLUDE_TIME else ""

output_name = (
    f"{time_tag}"
    f"_lines-{END_LINE-START_LINE}"
    f"_p-{MIN_POINTS}"
    f"_d-{MAX_DISTANCE}"
    f"_s-{MAX_SPEED}"
    f"_t-{int(MAX_TIME/60)}min"
    f"_start-{START_DATE.strftime('%Y%m%d')}"
    f"_end-{END_DATE.strftime('%Y%m%d')}"
    f".dat"
)

INPUT_FILE = r"C:\p10-data\Porto\train.csv"
OUTPUT_FILE = r"C:\Git\P10-DP\Porto\porto" + output_name

# Helper functions

def compute_speed(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]

    distance = math.hypot(dx, dy) * 111000 # 1 degree ~= 111000 meters

    return distance / POINT_INTERVAL

def is_unrealistic_speed(p1, p2):
    return compute_speed(p1, p2) > MAX_SPEED

def measure_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) > MAX_DISTANCE

def write_trajectory(f,trajectory, traj_id):
    trajectory_string = ";".join(trajectory) + ";"

    f.write(f"#{traj_id}\n")
    f.write(f">0:{trajectory_string}\n")

def is_noise(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < MIN_DISTANCE

def compute_timestamp(start_timestamp, point_count):
    return datetime.datetime.fromtimestamp(start_timestamp + (point_count * POINT_INTERVAL))


# Main

def load_data():
    traj_id = 0

    with open(INPUT_FILE, newline='', encoding="utf-8") as csvfile, open(OUTPUT_FILE, "w") as out:
        reader = csv.DictReader(csvfile)

        for row_index, row in enumerate(reader):

            if row_index < START_LINE:
                continue
            if row_index >= END_LINE:
                break

            print("Converting row:", row_index)

            if row["MISSING_DATA"] == "True":
                continue

            try:
                polyline = json.loads(row["POLYLINE"])
            except:
                continue

            if not polyline or len(polyline) < MIN_POINTS:
                continue

            trajectory = []
            prev_point = None
            point_count = 0
            timestamp = int(row["TIMESTAMP"])

            for coord in polyline:
                lon, lat = coord
                current_point = (lon, lat)

                if prev_point and is_noise(prev_point, current_point):
                    point_count += 1
                    continue

                if prev_point and is_unrealistic_speed(prev_point, current_point):
                    point_count += 1
                    continue
                
                if INCLUDE_TIME:
                    ts = compute_timestamp(timestamp, point_count)
                    trajectory.append(f"{lon},{lat},{ts}")
                else:
                    trajectory.append(f"{lon},{lat}")
                prev_point = current_point
                point_count += 1

            if len(trajectory) >= MIN_POINTS:
                write_trajectory(out, trajectory, traj_id)
                traj_id += 1

    print("Finished converting to file:", OUTPUT_FILE)


load_data()

