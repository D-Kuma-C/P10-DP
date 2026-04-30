# t-drive eks:
# 1,2008-02-02 15:36:08,116.51172,39.92123
# 1,2008-02-02 15:46:08,116.51135,39.93883

# output eks:
# #1:
# >0:116.51172,39.92123;116.51135,39.93883;

import os
import datetime
import math



# Parameters
START_FILE_INDEX = 0
END_FILE_INDEX = 100

INCLUDE_TIME_IN_OUTPUT = False

# Minimun amount of points, max time and distance between points in trajectories
MIN_POINTS = 3
MAX_TIME = 15 * 60
MAX_DISTANCE = 0.05 # 5 kilometer
MIN_DISTANCE = 0.0001 # 10 m


MAX_SPEED = 40

START_DATE = datetime.datetime.strptime("2008-02-02", "%Y-%m-%d")
END_DATE = datetime.datetime.strptime("2008-02-09", "%Y-%m-%d")

MIN_LON, MAX_LON = 115.7, 117.4
MIN_LAT, MAX_LAT = 39.4, 41.6

    
# Output File 

time_tag = "_time" if INCLUDE_TIME_IN_OUTPUT else ""

output_name = (
    f"{time_tag}"
    f"_p-{MIN_POINTS}"
    f"_d-{MAX_DISTANCE}"
    f"_t-{int(MAX_TIME/60)}min"
    f"_files-{END_FILE_INDEX-START_FILE_INDEX}"
    f"_start-{START_DATE.strftime('%Y%m%d')}"
    f"_end-{END_DATE.strftime('%Y%m%d')}"
    f".dat"
)

input_folder = r"C:\p10-data\taxi_log_2008_by_id"
output_file = r"C:\Git\P10-DP\t-drive\tdrive_" + output_name



def load_files(start, end):
    files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]
    files.sort(key=lambda x: int(x.split(".")[0]))


    open(output_file, "w").close()

    traj_id = 0

    for index in range(start, end):
        print("Converting file number: ", index)
        if index < len(files):
            traj_id = load_data(files[index], traj_id)

    print(f"Output file: ", output_file)

def load_data(file, traj_id):

    file_path = os.path.join(input_folder, file)

    with open(file_path) as f:
        lines = f.readlines()

    if (len(lines) == 0):
        return traj_id

    trajectory = []
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
        
       # if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
        #    continue
        
        current_point = (lon, lat)

        if prev_point and is_noise(prev_point, current_point):
            continue
        
        if prev_point == current_point:
            continue

        
        if prev_timestamp and (timestamp - prev_timestamp).total_seconds() > MAX_TIME:
            if len(trajectory) >= MIN_POINTS:
                write_trajectory(trajectory, traj_id)
                traj_id += 1

            trajectory = []
            prev_point = None
            prev_timestamp = None
            continue


        
        if prev_point and prev_timestamp:
            if is_unrealistic_speed(prev_point, current_point, prev_timestamp, timestamp):
                continue
        
        if (INCLUDE_TIME_IN_OUTPUT):
            trajectory.append(f"{lon},{lat},{timestamp}")
        else:
            trajectory.append(f"{lon},{lat}")
            
        prev_point = current_point
        prev_timestamp = timestamp
    
    if len(trajectory) >= MIN_POINTS:
        write_trajectory(trajectory, traj_id)
        traj_id += 1

    return traj_id
        
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


def measure_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) > MAX_DISTANCE

def write_trajectory(trajectory, traj_id):
    trajectory_string = ";".join(trajectory) + ";"

    with open(output_file, "a") as f2:
        f2.write(f"#{traj_id}\n")
        f2.write(f">0:{trajectory_string}\n")


load_files(START_FILE_INDEX, END_FILE_INDEX)