import datetime
import math
import csv
import json
import os
import requests

START_USER_INDEX = 0
END_USER_INDEX = 10

START_DATE = datetime.datetime.strptime("2007-04-01", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2011-11-01", "%Y-%m-%d")

MAX_MATCH_POINTS = 100  # OSRM limit
OSRM_URL = "http://localhost:5000/match/v1/driving"

ENABLE_MAP_MATCHING = True
INCLUDE_TIME = False

MIN_POINTS = 3
MAX_TIME = 15 * 60
MAX_DISTANCE = 0.05 # 5 kilometer
MIN_DISTANCE = 0.0005 # 10 m

MIN_TRAJECTORY_DISTANCE = 0.01

MAX_SPEED = 40 # m/s roughly equal to 140 km/t

MIN_LON, MAX_LON = 115.7, 117.4
MIN_LAT, MAX_LAT = 39.4, 41.6

time_tag = "_time" if INCLUDE_TIME else ""

output_name = (
    f"{time_tag}"
    f"_users-{END_USER_INDEX-START_USER_INDEX}"
    f"_p-{MIN_POINTS}"
    f"_d-{MAX_DISTANCE}"
    f"_s-{MAX_SPEED}"
    f"_t-{int(MAX_TIME/60)}min"
    f"_start-{START_DATE.strftime('%Y%m%d')}"
    f"_end-{END_DATE.strftime('%Y%m%d')}"
    f".dat"
)

INPUT_FOLDER = r"C:\p10-data\Geolife Trajectories 1.3\Data"
#OUTPUT_FILE = r"C:\Git\P10-DP\geolife\geolife_" + output_name

OUTPUT_FILE = r"C:\Git\P10-DP\geolife\test.dat"

# Helper functions

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def compute_speed(p1, p2, dt):
    dist = distance(p1, p2) * 111000
    return dist / dt if dt > 0 else 0

def is_noise(p1, p2):
    return distance(p1, p2) < MIN_DISTANCE

def write_trajectory(f, traj, traj_id):
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

def is_meaningful_trip(points):
    if not points:
        return False

    start = points[0]
    end = points[-1]

    return distance(start, end) > MIN_TRAJECTORY_DISTANCE


def chunk_trajectory(traj, size=MAX_MATCH_POINTS):
    for i in range(0, len(traj), size):
        yield traj[i:i+size]


def finalize_trajectory(out, points, times, traj_id):
    if len(points) < MIN_POINTS:
        return traj_id
    
    if not is_meaningful_trip(points):
        return traj_id
    
    if ENABLE_MAP_MATCHING:
        matched = process_with_map_matching(
            points,
            times if INCLUDE_TIME else None
        )
    else:
        if INCLUDE_TIME:
            matched = [(lon, lat, t) for (lon, lat), t in zip(points, times)]
        else:
            matched = points
    
    if matched:
        write_trajectory(out, matched, traj_id)
        return traj_id + 1
    
    return traj_id
        


# MAP MATCHING FUNCTIONS

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
                    "tidy": "true",
                    "radiuses": ";".join(["50"] * len(points))
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

    if any(tp is None for tp in tracepoints):
        return None

    if any(tp is None for tp in tracepoints):
        return None

    return geometry, tracepoints


# Assign timestamps to points and interpolate timestamps for new points
def interpolate_timestamps(geometry, tracepoints, original_times):
    result_times = [None] * len(geometry)

    # Map each valid tracepoint to its timestamp
    time_idx = 0
    for tp in tracepoints:
        if tp is None:
            continue
        result_times[tp["waypoint_index"]] = original_times[time_idx]
        time_idx += 1

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

    with open(OUTPUT_FILE, "w") as out:

        for index, user in enumerate(os.listdir(INPUT_FOLDER)):
            if index < START_USER_INDEX:
                continue
            if index >= END_USER_INDEX:
                break

            print("Converting trajectories for user:", user)
            traj_folder = os.path.join(INPUT_FOLDER, user, "Trajectory")

            if not os.path.exists(traj_folder):
                print(f"couldn't find path: {traj_folder}")
                continue
            
            

            for file in os.listdir(traj_folder):
                if not file.endswith(".plt"):
                    print("wrong file")
                    continue

                file_path = os.path.join(traj_folder, file)

                lines = []


                with open(file_path) as f:
                    lines = f.readlines()

                lines = lines[6:]

                trajectory_points = []
                trajectory_times = []
                prev_point = None
                prev_time = None

                for line in lines:
                    parts = line.strip().split(",")

                    if len(parts) < 7:
                        print("how the fuck did this happen?")
                        continue

                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                        timestamp = datetime.datetime.strptime(parts[5] + " " + parts[6],"%Y-%m-%d %H:%M:%S")
                    except:
                        continue

                    if not(START_DATE <= timestamp <= END_DATE):
                        continue
                    
                    if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
                        continue

                    current_point = (lon, lat)

                    if prev_point and is_noise(prev_point, current_point):
                        continue

                    if prev_point and prev_time:
                        dt = (timestamp - prev_time).total_seconds()
                        if dt > 0 and compute_speed(prev_point, current_point, dt) > MAX_SPEED:
                            continue

                    if (prev_time and (timestamp - prev_time).total_seconds() > MAX_TIME) or \
                        (prev_point and (distance(prev_point, current_point) > MAX_DISTANCE)):
                        
                        traj_id = finalize_trajectory(
                            out,
                            trajectory_points,
                            trajectory_times,
                            traj_id
                        )

                        trajectory_points = [(lon, lat)]
                        trajectory_times = [timestamp]

                    if INCLUDE_TIME:
                        trajectory_points.append((lon, lat))
                        trajectory_times.append(timestamp)
                    else:
                        trajectory_points.append((lon, lat))

                    prev_point = current_point
                    prev_time = timestamp

                traj_id = finalize_trajectory(
                    out,
                    trajectory_points,
                    trajectory_times,
                    traj_id
                )
                
    print("Finished converting, saved to:", OUTPUT_FILE)

load_data()
