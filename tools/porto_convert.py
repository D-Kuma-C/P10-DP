import datetime
import math
import csv
import json
import requests

# MAP MATCHING Params

ENABLE_MAP_MATCHING = True
OSRM_URL = "http://localhost:5000/match/v1/driving"
MAX_MATCH_POINTS = 100  # OSRM limit

# Parameters

START_LINE = 0
END_LINE = 20000

START_DATE = datetime.datetime.strptime("2013-01-07", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2014-06-30", "%Y-%m-%d")

INCLUDE_TIME = True

MIN_POINTS = 3
MAX_TIME = 15 * 60
MAX_DISTANCE = 0.05 # 5 kilometer
MIN_DISTANCE = 0.0001 # 10 m

MIN_TRAJECTORY_DISTANCE = 0.01

POINT_INTERVAL = 15 # 15 seconds between points

MAX_SPEED = 40

time_tag = "_time" if INCLUDE_TIME else ""
line_tag = f"_lines-{END_LINE-START_LINE}" if START_LINE and END_LINE else "_lines-all"
mapmatch_tag = "-raw" if not ENABLE_MAP_MATCHING else ""

output_name = (
    f"{mapmatch_tag}"
    f"{time_tag}"
    f"{line_tag}"
    f"_p-{MIN_POINTS}"
    f"_d-{MAX_DISTANCE}"
    f"_s-{MAX_SPEED}"
    f"_t-{int(MAX_TIME/60)}min"
    f"_start-{START_DATE.strftime('%Y%m%d')}"
    f"_end-{END_DATE.strftime('%Y%m%d')}"
    f".dat"
)

INPUT_FILE = r"C:\P10-Datasets\Porto\train.csv"
OUTPUT_FILE = r"C:\Users\Trailblaze\Documents\GitHub\P10-DP\Porto\porto" + output_name


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

def write_trajectory2(f, traj, traj_id):
    f.write(f"#{traj_id}\n")

    parts = []
    for item in traj:
        if INCLUDE_TIME:
            lon, lat, t = item
            parts.append(f"{lon},{lat},{t.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            lon, lat = item
            parts.append(f"{lon},{lat}")

    f.write(">0:" + ";".join(parts) + ";\n")

def is_noise(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < MIN_DISTANCE

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def is_meaningful_trip(trajectory):
    if len(trajectory) < 2:
        return False

    total_length = 0

    for i in range(1, len(trajectory)):
        total_length += distance(trajectory[i-1], trajectory[i])

    return total_length > MIN_TRAJECTORY_DISTANCE

def compute_timestamp(start_timestamp, point_count):
    return datetime.datetime.fromtimestamp(start_timestamp + (point_count * POINT_INTERVAL))

def chunk_trajectory(traj, size=MAX_MATCH_POINTS):
    for i in range(0, len(traj), size):
        yield traj[i:i+size]


# Map match raw data
def map_match_osrm(points, timestamps=None):
    if len(points) < 2:
        return None

    coords = ";".join([f"{lon},{lat}" for lon, lat in points])

    try:
        response = requests.get(
                OSRM_URL + "/" + coords,
                params={
                    "geometries": "geojson",
                    "overview": "full",
                    "steps": "false",
                    "radiuses": ";".join(["20"] * len(points))
                },
                timeout=5
            )
        data = response.json()
    except:
        return None

    if "matchings" not in data or not data["matchings"]:
        return None

    matching = data["matchings"][0]
    geometry = matching["geometry"]["coordinates"]
    tracepoints = data["tracepoints"]

    return geometry, tracepoints


# Assign timestamps to points and interpolate timestamps for new points
def interpolate_timestamps(geometry, tracepoints, original_times):
    result_times = [None] * len(geometry)

    # Map each valid tracepoint to its timestamp
    for i, tp in enumerate(tracepoints):
        if tp is None:
            continue

        if i >= len(original_times):
            continue

        geom_idx = tp["waypoint_index"]

        if geom_idx < 0 or geom_idx >= len(result_times):
            continue

        result_times[geom_idx] = original_times[i]

    # Interpolate missing timestamps
    last_known = None

    for i in range(len(result_times)):
        if result_times[i] is not None:
            if last_known is not None:
                t1 = result_times[last_known]
                t2 = result_times[i]
                gap = i - last_known

                for j in range(1, gap):
                    ratio = j / gap
                    result_times[last_known + j] = t1 + (t2 - t1) * ratio

            last_known = i

    # Include that last valid timestamp
    last_valid = None
    for i in range(len(result_times)):
        if result_times[i] is None:
            if last_valid is not None:
                result_times[i] = last_valid
        else:
            last_valid = result_times[i]

    return result_times


# Divide dataset into chunks and process each chunk
def process_with_map_matching(points, timestamps=None):
    all_geometry = []
    all_times = []

    pairs = list(zip(points, timestamps)) if timestamps else [(p, None) for p in points]

    chunks = [pairs[i:i+MAX_MATCH_POINTS] for i in range(0, len(pairs), MAX_MATCH_POINTS)]

    for chunk in chunks:
        pts = [p for p, _ in chunk]
        ts  = [t for _, t in chunk] if timestamps else None
        result = map_match_osrm(pts, ts)

        if not result:
            continue

        geometry, tracepoints = result

        

        # Interpolate timestamps if needed
        if ts:
            new_times = interpolate_timestamps(
                geometry,
                tracepoints,
                ts
            )
        else:
            new_times = [None] * len(geometry)

        # Avoid duplicate joins between chunks
        if all_geometry and geometry:
            geometry = geometry[1:]
            new_times = new_times[1:]

        all_geometry.extend(geometry)
        
        all_times.extend(new_times)

    if not all_geometry:
        return None

    # Final structure
    result = []
    for i in range(len(all_geometry)):
        lon, lat = all_geometry[i]
        if timestamps:
            result.append((lon, lat, all_times[i]))
        else:
            result.append((lon, lat))

    return result

# Main

def load_data():
    traj_id = 0

    with open(INPUT_FILE, newline='', encoding="utf-8") as csvfile, open(OUTPUT_FILE, "w") as out:
        reader = csv.DictReader(csvfile)

        for row_index, row in enumerate(reader):

            if row_index < START_LINE:
                continue
            if END_LINE and (row_index >= END_LINE):
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

            trajectory_points = []
            prev_point = None
            point_count = 0
            timestamp = int(row["TIMESTAMP"])
            timestamps = []

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
                    timestamps.append(ts)
                    trajectory_points.append(coord)
                else:
                    trajectory_points.append(coord)
                    
                prev_point = current_point
                point_count += 1


            if ENABLE_MAP_MATCHING:
                matched = process_with_map_matching(
                    trajectory_points,
                    timestamps if INCLUDE_TIME else None
                )

                if (matched and len(trajectory_points) >= MIN_POINTS) and is_meaningful_trip(trajectory_points):
                    #trajectory = [f"{lon},{lat}" for lon, lat in matched]
                    write_trajectory2(out, matched, traj_id)
                    traj_id += 1
            else:
                write_trajectory(out, trajectory_points, traj_id)
                traj_id += 1

    print("Finished converting to file:", OUTPUT_FILE)


load_data()

