import datetime
import math
import csv
import json
import requests

# MAP MATCHING Params

OSRM_URL = "http://localhost:5000/route/v1/driving"
MAX_MATCH_POINTS = 100  # OSRM limit

START_ID = 0
END_ID = 2000

INPUT_FILE = r"C:\Git\P10-DP\Porto\porto_20k.dat-eps1.0-iteration0.dat"
OUTPUT_FILE = r"C:\Git\P10-DP\output\test.dat"

def write_trajectory(trajectory, traj_id):
    trajectory_string = ";".join(trajectory) + ";"

    with open(OUTPUT_FILE, "a") as out:
        out.write(f"#{traj_id}\n")
        out.write(f">0:{trajectory_string}\n")

def haversine(p1, p2):
    import math
    R = 6371000
    lon1, lat1 = map(math.radians, p1)
    lon2, lat2 = map(math.radians, p2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def is_valid_trip(traj):
    if len(traj) < 2:
        return False

    total = sum(
        haversine(traj[i], traj[i+1])
        for i in range(len(traj)-1)
    )

    return total < 10000


# Map match raw data
def route_osrm(points):
    if len(points) < 2:
        return None

    coords = ";".join([f"{lon},{lat}" for lon, lat in points])

    try:
        response = requests.get(
            f"{OSRM_URL}/{coords}",
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "false"
            },
            timeout=5
        )
        data = response.json()
    except:
        return None

    if "routes" not in data or not data["routes"]:
        return None

    geometry = data["routes"][0]["geometry"]["coordinates"]
    return geometry

def parse_input(input_file):
    trajectories = []
    current = []

    with open(input_file) as f:
        for line in f:
            line = line.strip()

            if line.startswith("#"):
                if current:
                    trajectories.append(current)
                    current = []
            
            elif line.startswith(">0:"):
                coords = line[3:].split(";")
                for c in coords:
                    if not c:
                        continue
                    lon, lat = map(float, c.split(","))
                    current.append((lon, lat))

    if current:
        trajectories.append(current)

    return trajectories
        
def process_trajectories(input_file, output_file):
    trajectories = parse_input(input_file)

    traj_id = 0

    with open(output_file, "w") as out:
        for traj in trajectories:
            if traj_id < START_ID:
                continue
            if traj_id > END_ID:
                break
            
            if haversine(traj[0], traj[-1]) > 3000:
                continue
            print("Mapmatching trajectory:", traj_id)
            matched = route_osrm(traj)

            if not matched:
                continue

            # convert to output format
            parts = [f"{lon},{lat}" for lon, lat in matched]

            out.write(f"#{traj_id}\n")
            out.write(">0:" + ";".join(parts) + ";\n")

            traj_id += 1

process_trajectories(INPUT_FILE, OUTPUT_FILE)