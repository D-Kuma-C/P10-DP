# t-drive eks:
# 1,2008-02-02 15:36:08,116.51172,39.92123
# 1,2008-02-02 15:46:08,116.51135,39.93883

# output eks:
# #1:
# >0:116.51172,39.92123;116.51135,39.93883;

import os
import datetime
import math
import requests
import math
import json

with open("../config.json") as f:
    CONFIG = json.load(f)

# MAP MATCHING Params

ENABLE_MAP_MATCHING = CONFIG["map_matching"]["enable"]
OSRM_URL = CONFIG["map_matching"]["OSRM_url"]
MAX_MATCH_POINTS = CONFIG["map_matching"]["max_match_points"]

# Parameters
START_FILE_INDEX = CONFIG["processing_parameters"]["start_index"]
END_FILE_INDEX = CONFIG["processing_parameters"]["end_index"]

INCLUDE_TIME = CONFIG["processing_parameters"]["include_time"]

MIN_LON = CONFIG["dataset"]["tdrive"]["bounds"]["min_lon"]
MAX_LON = CONFIG["dataset"]["tdrive"]["bounds"]["max_lon"]

MIN_LAT = CONFIG["dataset"]["tdrive"]["bounds"]["min_lat"]
MAX_LAT = CONFIG["dataset"]["tdrive"]["bounds"]["max_lat"]


MIN_POINTS = CONFIG["processing_parameters"]["min_points"]
MAX_TIME = CONFIG["processing_parameters"]["max_time"]
MAX_DISTANCE = CONFIG["processing_parameters"]["max_distance"]
MIN_DISTANCE = CONFIG["processing_parameters"]["min_distance"]

MIN_TRAJECTORY_DISTANCE = CONFIG["processing_parameters"]["min_trajectory_distance"]

MAX_SPEED = CONFIG["processing_parameters"]["max_speed"]

START_DATE = datetime.datetime.strptime("2008-02-02", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2008-02-09", "%Y-%m-%d")

node_registry = {}
edge_registry = {}
edge_lookup = {}

next_edge_id = 0


# Output File 

time_tag = "_time" if INCLUDE_TIME else ""
mapmatch_tag = "-raw" if not ENABLE_MAP_MATCHING else ""
file_tag = "all" if not START_FILE_INDEX or not END_FILE_INDEX else f"{END_FILE_INDEX-START_FILE_INDEX}"
current_time = datetime.datetime.now().strftime("%m%d_%H%M%S")

output_name = (
    f"{mapmatch_tag}"
    f"{time_tag}"
    f"_files-{file_tag}"
    f"{current_time}"
    f"_p-{MIN_POINTS}"
    f"_d-{MAX_DISTANCE}"
    f"_t-{int(MAX_TIME/60)}min"
    f"_start-{START_DATE.strftime('%Y%m%d')}"
    f"_end-{END_DATE.strftime('%Y%m%d')}"
    f".dat"
)


INPUT_FOLDER = CONFIG["dataset"]["tdrive"]["input_location"]
OUTPUT_FILE = CONFIG["dataset"]["tdrive"]["output_location"] + output_name
TRAJECTORY_SEGMENTS_FILE = CONFIG["dataset"]["tdrive"]["segment_file_location"] + current_time + ".csv"


# HELPER FUNCTIONS

def load_files(start, end):
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".txt")]
    files.sort(key=lambda x: int(x.split(".")[0]))

    if not start:
        start = 0
    if not end:
        end = 10357

    with open(OUTPUT_FILE, "w") as out_f:

        os.makedirs(os.path.dirname(TRAJECTORY_SEGMENTS_FILE), exist_ok=True)

        with open(TRAJECTORY_SEGMENTS_FILE, "w") as traj_segments_out:
            traj_segments_out.write("traj_id,order,segment_id\n")

            traj_id = 0

            for index in range(start, end):
                print("Converting file number: ", index)
                if index < len(files):
                    traj_id = load_data(files[index], traj_id, out_f, traj_segments_out)


        
def is_noise(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < MIN_DISTANCE

def is_unrealistic_speed(p1, p2, t1, t2):
    dt = (t2 - t1).total_seconds()
    if dt <= 0:
        return True

    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]

    distance = math.hypot(dx, dy) * 111000

    speed = distance / dt

    return speed > MAX_SPEED   

def distance(p1, p2):
    return math.hypot(float(p1[0]) - float(p2[0]), float(p1[1]) - float(p2[1]))

def is_meaningful_trip(points):
    if not points:
        return False

    start = points[0]
    end = points[-1]

    return distance(start, end) > MIN_TRAJECTORY_DISTANCE

def measure_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) > MAX_DISTANCE

def write_trajectory(out, traj, traj_id):
    out.write(f"#{traj_id}\n")

    parts = []
    for item in traj:
        if INCLUDE_TIME:
            lon, lat, t = item
            parts.append(f"{lon},{lat},{t.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            lon, lat = item
            parts.append(f"{lon},{lat}")

    out.write(">0:" + ";".join(parts) + ";\n")

def finalize_trajectory(out, segments_out, points, times, traj_id):
    if len(points) < MIN_POINTS:
        return traj_id
    
    if not is_meaningful_trip(points):
        return traj_id
    
    if ENABLE_MAP_MATCHING:
        matched_result = process_with_map_matching(
            points,
            times if INCLUDE_TIME else None
        )

        if not matched_result:
            return traj_id

        matched, segment_ids = matched_result

    else:
        segment_ids = []
        if INCLUDE_TIME:
            matched = [(lon, lat, t) for (lon, lat), t in zip(points, times)]
        else:
            matched = points
    
    if matched:
        write_trajectory(out, matched, traj_id)

        for order, seg_id in enumerate(segment_ids):
            segments_out.write(f"{traj_id},{order},{seg_id}\n")

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

# MAIN
def load_data(file, traj_id, out_f, traj_segments_out):

    file_path = os.path.join(INPUT_FOLDER, file)

    with open(file_path, "r") as out:
        lines = out.readlines()


        if (len(lines) == 0):
            return traj_id

        trajectory_points = []
        trajectory_times = []
        prev_point = None
        prev_timestamp = None
        
        for line in lines:
            point = line.strip().split(',')

            try:
                timestamp = datetime.datetime.strptime(point[1], "%Y-%m-%d %H:%M:%S")
                lon = float(point[2])
                lat = float(point[3])
            except:
                continue
            

            if not (START_DATE <= timestamp <= END_DATE):
                continue

            if lon == 0.0 or lat == 0.0:
                continue
            
            if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
                continue
            
            current_point = (lon, lat)

            if prev_point and is_noise(prev_point, current_point):
                continue
            
            if prev_point == current_point:
                continue

            
            if prev_timestamp and (timestamp - prev_timestamp).total_seconds() > MAX_TIME:
                traj_id = finalize_trajectory(
                    out_f,
                    traj_segments_out,
                    trajectory_points,
                    trajectory_times,
                    traj_id
                )

                trajectory_points = []
                trajectory_times = []


            
            if prev_point and prev_timestamp:
                if is_unrealistic_speed(prev_point, current_point, prev_timestamp, timestamp):
                    continue
            
            if (INCLUDE_TIME):
                trajectory_points.append((lon, lat))
                trajectory_times.append(timestamp)
            else:
                trajectory_points.append((lon, lat))
                
            prev_point = current_point
            prev_timestamp = timestamp
        
        traj_id = finalize_trajectory(
            out_f,
            traj_segments_out,
            trajectory_points,
            trajectory_times,
            traj_id
        )

    return traj_id


load_files(START_FILE_INDEX, END_FILE_INDEX)