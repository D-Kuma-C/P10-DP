import datetime
import math
import csv
import json
import requests

with open("../config.json") as f:
    CONFIG = json.load(f)

# MAP MATCHING Params

ENABLE_MAP_MATCHING = CONFIG["map_matching"]["enable"]
OSRM_URL = CONFIG["map_matching"]["OSRM_url"]
MAX_MATCH_POINTS = CONFIG["map_matching"]["max_match_points"]

# Parameters

START_LINE = CONFIG["processing_parameters"]["start_index"]
END_LINE = CONFIG["processing_parameters"]["end_index"]

INCLUDE_TIME = CONFIG["processing_parameters"]["include_time"]

MIN_LON = CONFIG["dataset"]["porto"]["bounds"]["min_lon"]
MAX_LON = CONFIG["dataset"]["porto"]["bounds"]["max_lon"]

MIN_LAT = CONFIG["dataset"]["porto"]["bounds"]["min_lat"]
MAX_LAT = CONFIG["dataset"]["porto"]["bounds"]["max_lat"]


MIN_POINTS = CONFIG["processing_parameters"]["min_points"]
MAX_TIME = CONFIG["processing_parameters"]["max_time"]
MAX_DISTANCE = CONFIG["processing_parameters"]["max_distance"]
MIN_DISTANCE = CONFIG["processing_parameters"]["min_distance"]

MIN_TRAJECTORY_DISTANCE = CONFIG["processing_parameters"]["min_trajectory_distance"]

MAX_SPEED = CONFIG["processing_parameters"]["max_speed"]

# Porto specific
START_DATE = datetime.datetime.strptime("2013-01-07", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2014-06-30", "%Y-%m-%d")
POINT_INTERVAL = 15 # 15 seconds between points


time_tag = "_time" if INCLUDE_TIME else ""
mapmatch_tag = "-raw" if not ENABLE_MAP_MATCHING else ""

current_time = datetime.datetime.now().strftime("%m%d_%H%M%S")

output_name = (
    f"{mapmatch_tag}"
    f"{time_tag}"
    f"_lines-{END_LINE-START_LINE}"
    f"{current_time}"
    f"_p-{MIN_POINTS}"
    f"_d-{MAX_DISTANCE}"
    f"_s-{MAX_SPEED}"
    f"_t-{int(MAX_TIME/60)}min"
    f"_start-{START_DATE.strftime('%Y%m%d')}"
    f"_end-{END_DATE.strftime('%Y%m%d')}"
    f".dat"
)



INPUT_FILE = CONFIG["dataset"]["porto"]["input_location"]
OUTPUT_FILE = CONFIG["dataset"]["porto"]["output_location"] + output_name
TRAJECTORY_SEGMENTS_FILE = CONFIG["dataset"]["porto"]["segment_file_location"] + current_time + ".csv"



node_registry = {}
edge_registry = {}
edge_lookup = {}

next_edge_id = 0


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
                    "annotations": "true",
                    "radiuses": ";".join(["20"] * len(points))
                },
                timeout=5
            )
        data = response.json()
    except Exception as e:
        print("OSRM request failed:", e)
        return None

    if "matchings" not in data or not data["matchings"]:
        return None

    matching = data["matchings"][0]
    geometry = matching["geometry"]["coordinates"]

    tracepoints = data["tracepoints"]
    legs = matching["legs"]

    return geometry, tracepoints, legs


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
    all_segment_ids = []

    pairs = list(zip(points, timestamps)) if timestamps else [(p, None) for p in points]

    chunks = [pairs[i:i+MAX_MATCH_POINTS] for i in range(0, len(pairs), MAX_MATCH_POINTS)]

    for chunk in chunks:
        pts = [p for p, _ in chunk]
        ts  = [t for _, t in chunk] if timestamps else None
        result = map_match_osrm(pts, ts)

        if not result:
            continue

        geometry, tracepoints, legs = result

        
        trajectory_edge_ids = extract_segments_from_legs(legs)
        all_segment_ids.extend(trajectory_edge_ids)

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

    return result, all_segment_ids

def extract_segments_from_legs(legs):
    global next_edge_id

    trajectory_edge_ids = []

    for leg in legs:

        if "annotation" not in leg:
            continue

        annotation = leg["annotation"]

        if "nodes" not in annotation:
            continue

        nodes = annotation["nodes"]

        for i in range(len(nodes) - 1):

            start_node = nodes[i]
            end_node = nodes[i + 1]

            edge_key = (start_node, end_node)

            # Reuse existing edge
            if edge_key in edge_lookup:
                edge_id = edge_lookup[edge_key]

            else:
                edge_id = next_edge_id
                next_edge_id += 1

                edge_lookup[edge_key] = edge_id

                edge_registry[edge_id] = {
                    "start_node": start_node,
                    "end_node": end_node,
                    "length": None
                }

            trajectory_edge_ids.append(edge_id)

    return trajectory_edge_ids

def route_osrm(points):

    if len(points) < 2:
        return None

    coords = ";".join([f"{lon},{lat}" for lon, lat in points])

    try:
        response = requests.get(
            f"http://localhost:5000/route/v1/driving/{coords}",
            params={
                "overview": "full",
                "geometries": "geojson",
                "annotations": "true",
                "steps": "false"
            },
            timeout=5
        )

        data = response.json()

    except:
        return None

    if "routes" not in data or not data["routes"]:
        return None

    return data["routes"][0]


# Main

def load_data():
    traj_id = 0

    with open(INPUT_FILE, newline='', encoding="utf-8") as csvfile, open(OUTPUT_FILE, "w") as out:
        reader = csv.DictReader(csvfile)
        with open(TRAJECTORY_SEGMENTS_FILE, "w") as traj_segments_out:
        
            traj_segments_out.write("traj_id,order,segment_id\n")
            

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

                trajectory_points = []
                timestamps = []

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

                    if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
                        continue           
                    
                    trajectory_points.append(coord)
                    
                    if INCLUDE_TIME:
                        ts = compute_timestamp(timestamp, point_count)
                        timestamps.append(ts)
                        
                    prev_point = current_point
                    point_count += 1

                

                if ENABLE_MAP_MATCHING:
                    matched_result = process_with_map_matching(
                        trajectory_points,
                        timestamps if INCLUDE_TIME else None
                    )

                    if not matched_result:
                        continue
                    
                    matched, segment_ids = matched_result

                    if not matched or len(trajectory_points) < MIN_POINTS:
                        continue

                    if not is_meaningful_trip(trajectory_points):
                        continue

                    
                    #trajectory = [f"{lon},{lat}" for lon, lat in matched]
                    write_trajectory2(out, matched, traj_id)

                    for order, seg_id in enumerate(segment_ids):
                        traj_segments_out.write(f"{traj_id},{order},{seg_id}\n")

                    traj_id += 1
                else:
                    write_trajectory(out, trajectory_points, traj_id)
                    traj_id += 1


    print("Finished converting to file:", OUTPUT_FILE)


load_data()

