import datetime
import math
import csv
import json
import os

START_USER_INDEX = 0
END_USER_INDEX = 10

START_DATE = datetime.datetime.strptime("2007-04-01", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2011-11-01", "%Y-%m-%d")

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

def write_trajectory(f, trajectory, traj_id):
    f.write(f"#{traj_id}\n")
    f.write(">0:" + ";".join(trajectory) + ";\n")

def is_meaningful_trip(trajectory):
    if not trajectory: return False
    start = trajectory[0].split(',')
    end = trajectory[-1].split(',')
    # Calculate distance between first and last point
    total_displacement = distance((float(start[0]), float(start[1])), 
                                  (float(end[0]), float(end[1])))
    return total_displacement > MIN_TRAJECTORY_DISTANCE

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

                trajectory = []
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

                    if (prev_time and (timestamp - prev_time).total_seconds() > MAX_TIME) or (prev_point and (distance(prev_point, current_point) > MAX_DISTANCE)):
                        if len(trajectory) >= MIN_POINTS:
                            if (is_meaningful_trip(trajectory)):
                                write_trajectory(out, trajectory, traj_id)
                                traj_id += 1
                        trajectory = []

                    if INCLUDE_TIME:
                        trajectory.append(f"{lon},{lat},{timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        trajectory.append(f"{lon},{lat}")

                    prev_point = current_point
                    prev_time = timestamp

                if len(trajectory) >= MIN_POINTS:
                    if (is_meaningful_trip(trajectory)):
                        write_trajectory(out, trajectory, traj_id)
                        traj_id += 1
                
    print("Finished converting, saved to:", OUTPUT_FILE)

load_data()
